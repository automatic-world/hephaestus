from typing import TypedDict
from arango import ArangoClient
from langchain_core.messages import SystemMessage, BaseMessage
from langchain_openai import ChatOpenAI
import json


class FunctionInfo(TypedDict):
    original_id: str
    new_name: str
    function_info: str


class LLMResponse(TypedDict):
    data: list[FunctionInfo]
    continue_req_yn: str
    last_checked_id: str


def replace_args(_param: dict, content: str) -> str:

    try:
        for key, value in _param.items():
            key = ("{" + key + "}")
            content = content.replace(key, str(value))
        return content
    except Exception as e:
        print(e)
        return content


def list_to_tsv_str(_list: list) -> str:
    keys = [key for key in _list[0]]

    out: list[str] = ['\t'.join(keys)]
    for d in _list:
        row = [value if value is not None else '' for key, value in d.items()]
        out.append('\t'.join(row))
    return '\n'.join(out)


def get_json_str(_list: list) -> str:
    out: list[list[str]] = []
    for d in _list:
        row = [value if value is not None else '' for key, value in d.items()]
        out.append(row)
    return json.dumps(out, ensure_ascii=False)


def get_list_in_list(_list: list[dict]) -> list[list[str]]:

    out: list[list[str]] = []
    for d in _list:
        row = [value if value is not None else '' for key, value in d.items()]
        out.append(row)
    return out


def get_all_elements() -> list[dict]:
    # ArangoDB 연결 설정
    client = ArangoClient()
    db = client.db("_system", username="root", password="openSesame")

    aql_query = """
    LET excludedNodes = (
      FOR v IN 0..10 OUTBOUND "nodes/tests" edges
        RETURN v._id
    )
    FOR node IN nodes
      FILTER node._id NOT IN excludedNodes
      
      LET parentEdge = (
        FOR e IN edges
          FILTER e._to == node._id
          LIMIT 1
          RETURN e._from
      )
      
      LET fnInfo = (
        FILTER node.type == "function"
        LET doc = DOCUMENT("nodes", node._key)
        RETURN doc.reason_kor
      )
      
      RETURN {
        id: node._key,
        parent_id: LENGTH(parentEdge) > 0 ? parentEdge[0] : null,
        type: node.type,
        name: node.name,
        function_info: LENGTH(fnInfo) > 0 ? fnInfo[0] : null
      }
    """

    result: list[dict] = list(db.aql.execute(aql_query))
    _sort: list[str] = ["nodes/" + r["id"] for r in result]
    length = len(result)
    for i in range(length):
        pid: str = result[i]['parent_id']
        if pid is not None and pid != '':
            ori = result[i]
            _ori = _sort[i]
            del result[i]
            del _sort[i]
            t_idx: int = _sort.index(pid)
            result[t_idx + 1:t_idx + 1] = [ori]
            _sort[t_idx + 1:t_idx + 1] = [_ori]

    return result

def get_prompt(_param: dict) -> list[SystemMessage]:
    prompt = """
[context]
당신은 Python 라이브러리 전문가를 보조하는 유용한 AI Tool입니다. 아래의 사항을 준수하여 답변해주세요.


[objective]
아래의 사항을 준수하여 답변해주세요.
1. [검토 대상]에는 python 라이브러리 파일과 관련한 JSON_ARRAY 형태의 문자열을 받습니다.
2. 각 컬럼은 순서대로 id, parent_id, type, name, function_info 입니다.
3. function_info에는 해당 name이라는 이름의 function의 기능을 추상적으로 기술하고 있습니다.
4. 각 기능들을 [요청사항]에 맞게 다른 목적 혹은 다른 프로그램(으)로써 바꾸기 위해 한줄 한줄 각 기능들을 어떻게 바껴야 할지 생각하고, 적절하게 변경해주세요.
5. 만일 답변이 완전하게 되지 않아서 계속 출력할 필요가 있으면, 마지막으로 검토를 완료한 id는 last_checked_id에 넣고 continue_req_yn를 'Y'로 주세요.
6. 마지막 id까지 검토가 완료되었다면 continue_req_yn를 반드시 'N'으로 주세요.
7. 응답 형식은 [응답 형식]과 같은 JSON으로 주세요.

[요청사항]
{query}

[검토 대상]
{checking_target}


[audience]
python 전문 AI


[response]
{
    "data": [
        {"original_id": "langchain_neo4j_vectorstores_neo4j_vector_py_Neo4jVector", "new_name": "ArangoVector", "function_info": "~~~"},
        {"original_id": "langchain_neo4j_chains_graph_qa_cypher_utils_py", "new_name": "__from", "function_info": "~~~"},
        ...
    ],
    "continue_req_yn": "Y",
    "last_checked_id": "langchain_neo4j_vectorstores_neo4j_vector_py_add_embeddings"
}
"""

    context = SystemMessage(content=replace_args(_param=_param, content=prompt))
    return [context]


def get_llm_response(_param: dict) -> LLMResponse:
    openai_api_key = ''

    # LLM 설정
    chat = ChatOpenAI(model="gpt-4.1-nano", openai_api_key=openai_api_key)

    try:
        response: BaseMessage = chat.invoke(get_prompt(_param=_param))
        _res = json.loads(response.content)
        return LLMResponse(
            data=[FunctionInfo(**row) for row in _res.get("data")],
            continue_req_yn=_res.get("continue_req_yn"),
            last_checked_id=_res.get("last_checked_id")
        )
    except Exception as e:
        print(f"error ::: {e}")
        return LLMResponse(
            data=[],
            continue_req_yn='N',
            last_checked_id=''
        )


if __name__ == "__main__":
    originals = get_all_elements()
    el_list: list[list[str]] = get_list_in_list(_list=originals)
    output_last: list[FunctionInfo] = []
    sort: list[str] = [l[0] for l in el_list]

    continue_flag: str = 'Y'

    from_i: int = 0
    to_i: int = len(el_list)

    while continue_flag == 'Y':
        t_list: list[list[str]] = el_list[from_i:to_i]

        param: dict = {
            'query': 'arangodb에 맞는 프로그램으로 바꾸고 싶어요.',
            'checking_target': t_list
        }

        res: LLMResponse = get_llm_response(_param=param)
        data: list[FunctionInfo] = res.get("data")
        output_last = output_last + data
        if res.get("continue_req_yn") == 'Y':
            from_i = sort.index(res.get("last_checked_id"))
            to_i = len(el_list)
        else:
            continue_flag = res.get("continue_req_yn")

    print(output_last)


"""
[{'original_id': 'langchain_neo4j_vectorstores_neo4j_vector_py_Neo4jVector', 'new_name': 'ArangoVector', 'function_info': 'ArangoVector 클래스를 도입하여 ArangoDB에 최적화된 벡터 저장 및 유사도 검색 기능을 제공하며, 기존 Neo4j 관련 함수들을 ArangoDB의 검색 인터페이스로 교체합니다.'}, {'original_id': 'langchain_neo4j_chains_graph_qa_cypher_utils_py', 'new_name': '__from', 'function_info': 'ArangoDB의 문서 및 그래프 구조에 맞게 바이너리 검색 또는 일치 검사를 수행하는 함수로 재구성하며, Cypher에 특화된 내용은 제거합니다.'}, {'original_id': 'langchain_neo4j_graphs_neo4j_graph_py_refresh_schema', 'new_name': 'refresh_schema', 'function_info': 'ArangoDB에서 컬렉션 및 그래프 스키마 정보를 새로고침하거나 업데이트하는 함수로 교체하며, ArangoDB의 스키마 추상화에 맞게 변경합니다.'}, {'original_id': 'langchain_neo4j_graphs_neo4j_graph_py_query', 'new_name': 'query', 'function_info': 'ArangoDB의 AQL 쿼리 실행 기능을 활용하여 데이터 조회를 수행하는 함수로 변경, Neo4j의 Cypher 대신 ArangoDB 쿼리 언어에 적합하게 수정합니다.'}, {'original_id': 'langchain_neo4j_graphs_neo4j_graph_py_get_structured_schema', 'new_name': 'get_structured_schema', 'function_info': 'ArangoDB에서 컬렉션과 그래프 구조를 구조화된 딕셔너리로 반환하는 함수로 변경하여, ArangoDB의 스키마 정보를 일관되게 제공하도록 구현합니다.'}, {'original_id': 'langchain_neo4j_graphs_neo4j_graph_py_get_schema', 'new_name': 'get_schema', 'function_info': 'ArangoDB에서 실행 중인 컬렉션 및 그래프의 간단한 스키마 요약 문자열을 반환하는 함수로 변환하며, ArangoDB 특성에 맞는 문자열 포맷으로 변경합니다.'}, {'original_id': 'langchain_neo4j_graphs_neo4j_graph_py_close', 'new_name': 'close', 'function_info': 'ArangoDB 드라이버와의 연결을 종료하는 함수로 변경하며, 연결 상태 체크 후 안전하게 종료하는 로직을 포함합니다.'}, {'original_id': 'langchain_neo4j_graphs_neo4j_graph_py_add_graph_documents', 'new_name': 'add_graph_documents', 'function_info': 'ArangoDB의 문서 컬렉션에 그래프 데이터(노드, 에지)를 적절한 방식으로 삽입하는 함수로 변경, ArangoDB의 문서 기반 저장 구조에 맞게 조정합니다.'}, {'original_id': 'langchain_neo4j_graphs_graph_store_py_refresh_schema', 'new_name': 'refresh_schema', 'function_info': 'ArangoDB의 스키마 정보를 새로고침하는 함수를 구현하며, 컬렉션 또는 그래프의 메타데이터를 최신 상태로 유지합니다.'}, {'original_id': 'langchain_neo4j_graphs_graph_store_py_query', 'new_name': 'query', 'function_info': 'ArangoDB의 AQL을 사용하여 쿼리 실행 및 결과 반환, Neo4j의 Cypher 대신 ArangoDB 쿼리 언어에 적합하도록 변경합니다.'}, {'original_id': 'langchain_neo4j_graphs_graph_store_py_get_structured_schema', 'new_name': 'get_structured_schema', 'function_info': 'ArangoDB에서 컬렉션, 그래프의 구조를 구조화된 딕셔너리로 반환하는 함수로 변경하며, 관련 데이터 구조에 맞게 수정합니다.'}, {'original_id': 'langchain_neo4j_graphs_graph_store_py_get_schema', 'new_name': 'get_schema', 'function_info': 'ArangoDB의 컬렉션 및 그래프의 간단한 텍스트 요약 스키마 정보를 반환하는 함수로 변경하여 사용합니다.'}, {'original_id': 'langchain_neo4j_chat_message_histories_neo4j_py_messages', 'new_name': 'messages', 'function_info': 'ArangoDB 기반의 채팅 메시지 저장 로직으로 대체하며, 메시지 저장, 조회, 삭제를 ArangoDB 문서 구조에 맞게 수행합니다.'}, {'original_id': 'langchain_neo4j_chat_message_histories_neo4j_py_clear', 'new_name': 'clear', 'function_info': 'ArangoDB에서 채팅 세션 및 메시지 삭제 기능으로 수정, 컬렉션 또는 그래프 내 문서를 삭제하는 방식으로 변경합니다.'}, {'original_id': 'langchain_neo4j_chat_message_histories_neo4j_py_add_message', 'new_name': 'add_message', 'function_info': 'ArangoDB 문서에 채팅 메시지를 저장하는 함수로 재작성하며, 메시지 내용, 역할, 세션 정보 등을 문서에 저장하는 형식으로 수정합니다.'}, {'original_id': 'langchain_neo4j_chat_message_histories_neo4j_py___init__', 'new_name': '__init__', 'function_info': 'ArangoDB 클라이언트 연결 초깃값과 세션셋업을 담당하는 생성자 함수로 변경하며, 연결 검증 및 기본 구성 로직을 포함합니다.'}, {'original_id': 'langchain_neo4j_chat_message_histories_neo4j_py___del__', 'new_name': '__del__', 'function_info': 'ArangoDB 드라이버 및 세션 종료를 담당하는 소멸자 함수로 변경합니다.'}, {'original_id': 'langchain_neo4j_chains_graph_qa___init___py', 'new_name': '__init__', 'function_info': 'ArangoDB 기반의 그래프 QA 체인 인스턴스 생성자 함수로 변경하며, 연결 설정, 매개변수 인증 및 검증 로직을 포함합니다.'}, {'original_id': 'langchain_neo4j_chains_graph_qa_cypher_utils_py', 'new_name': 'verify_schema', 'function_info': 'ArangoDB 스키마 또는 컬렉션이 예상한 구조와 일치하는지 검증하는 함수로 재구성하며, Cypher 검증 내용은 제거합니다.'}, {'original_id': 'langchain_neo4j_chains_graph_qa_cypher_utils_py_judge_direction', 'new_name': 'detect_relation_types', 'function_info': 'ArangoDB의 문서 또는 그래프 데이터 내 관계 유형을 분석하여 방향성을 판단하는 함수로 변경합니다.'}, {'original_id': 'langchain_neo4j_chains_graph_qa_cypher_utils_py_extract_paths', 'new_name': 'extract_paths', 'function_info': 'ArangoDB의 그래프 탐색 또는 경로 추출 로직에 적합하게 변경하고, Cypher 패턴 매칭 대신 ArangoDB 그래프 쿼리 방식으로 수정합니다.'}, {'original_id': 'langchain_neo4j_chains_graph_qa_cypher_utils_py_extract_node_variable', 'new_name': 'extract_node_variable', 'function_info': 'ArangoDB 그래프 또는 문서 내 노드 변수 추출 로직으로 재구성하며, 문자열 패턴 분석 대신 구조화된 형식을 활용할 수 있습니다.'}, {'original_id': 'langchain_neo4j_chains_graph_qa_cypher_utils_py_detect_labels', 'new_name': 'detect_labels', 'function_info': 'ArangoDB 문서 또는 그래프의 라벨(컬렉션 이름 또는 속성)을 분석하여 추출하는 함수로 변경합니다.'}, {'original_id': 'langchain_neo4j_chains_graph_qa_cypher_utils_py_correct_query', 'new_name': 'correct_query', 'function_info': 'ArangoDB 쿼리 최적화 또는 버그 수정을 위한 함수로 재구성하며, Cypher 쿼리 검증 대신 ArangoDB 쿼리 검증 로직으로 변경합니다.'}, {'original_id': 'langchain_neo4j_chains_graph_qa_cypher_utils_py_clean_node', 'new_name': 'clean_node', 'function_info': 'ArangoDB 내 노드 또는 문서 식별자 정제 함수로 변경하며, 문자열에서 불필요한 패턴 또는 문자를 제거하는 로직을 포함합니다.'}, {'original_id': 'langchain_neo4j_chains_graph_qa_cypher_utils_py___init__', 'new_name': '__init__', 'function_info': 'ArangoDB 스키마 또는 제약 조건 관련 초기화자로 변경하며, 객체 생성 시 스키마 검증 로직을 포함합니다.'}, {'original_id': 'langchain_neo4j_chains_graph_qa_cypher_utils_py___call__', 'new_name': '__call__', 'function_info': 'ArangoDB 쿼리 유효성 검증 또는 포맷팅 기능 수행, 그 수행 결과로 ArangoDB 쿼리 문자열 또는 검증된 쿼리 반환합니다.'}]
"""