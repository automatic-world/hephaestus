from typing import TypedDict
from arango import ArangoClient
from langchain_core.messages import SystemMessage, BaseMessage
from langchain_openai import ChatOpenAI
import json

class FunctionConceptEdge(TypedDict):
    node_id: str
    concept_id: str
    relation_type: str
    relation_category: str
    justification: str

def replace_args(_param: dict, content: str) -> str:
    try:
        for key, value in _param.items():
            key = ("{" + key + "}")
            content = content.replace(key, str(value))
        return content
    except Exception as e:
        print(e)
        return content

def get_all_functions() -> list[dict]:
    client = ArangoClient()
    db = client.db("_system", username="root", password="openSesame")
    return list(db.aql.execute("""
    FOR node IN nodes
      FILTER node.type IN ["function", "class"]
      RETURN {
        node_id: CONCAT("nodes/", node._key),
        node_name: node.name,
        node_docstring: node.docstring,
        node_reason: node.reason,
        node_defined_in: node.defined_in
      }
    """))

def get_all_concepts() -> list[dict]:
    client = ArangoClient()
    db = client.db("_system", username="root", password="openSesame")
    return list(db.aql.execute("""
    FOR concept IN concepts
      RETURN {
        concept_id: CONCAT("concepts/", concept._key),
        concept_concept: concept.concept,
        concept_description: concept.description
      }
    """))

def get_prompt(param: dict) -> SystemMessage:
    prompt = """
[Observation]
- 함수:
    - id: {node_id}
    - name: {node_name}
    - docstring: {node_docstring}
    - reason: {node_reason}
    - defined_in: {node_defined_in}
- 개념:
    - id: {concept_id}
    - concept: {concept_concept}
    - description: {concept_description}

[Task]
아래 relation_type 중에서 이 함수와 개념의 관계를 하나 골라주세요:
[implements, exemplifies, uses, is_part_of, related_to]
엄격하게 판단하여 함수와 개념이 상호 연관이 없는 경우 is_mutually_related를 false로 하고, reason은 null로 한 후 추론을 절대 하지 마세요.
그리고 relation_category("function_to_concept")와 관계의 근거(justification)를 1-2문장으로 기술해서 다음 JSON 형식으로 반환하세요.
주어진 개념 외의 개념이 해당 함수에 포함되어 있다면, additional_information에 자세히 기술하세요.

JSON 예시:
{
"is_mutually_related": true,
"reason": {
  "node_id": "{node_id}",
  "concept_id": "{concept_id}",
  "relation_type": "implements",
  "relation_category": "function_to_concept",
  "justification": "...",
  "additional_information": "..."
}
}
"""

    prompt = """
[Observation]
- 함수:
    - id: {node_id}
    - name: {node_name}
    - docstring: {node_docstring}
    - reason: {node_reason}
    - defined_in: {node_defined_in}
- 개념:
{concepts_str}

[Task]
아래 relation_type 중에서 이 함수와 개념의 관계를 하나 골라주세요:
[implements, exemplifies, uses, is_part_of, related_to]
엄격하게 판단하여 함수와 개념이 상호 연관이 없는 경우 is_mutually_related를 false로 하고, reason은 null로 한 후 추론을 절대 하지 마세요.
그리고 relation_category("function_to_concept")와 관계의 근거(justification)를 1-2문장으로 기술해서 제시된 개념의 수만큼 JSON ARRAY 형식으로 반환하세요.
주어진 개념 외의 개념이 해당 함수에 포함되어 있다면, additional_information에 자세히 기술하세요.

응답 예시:
{"is_mutually_related": true, "reason": {"node_id": "nodes/~", "concept_id": "concepts/~", "relation_type": "implements", "relation_category": "function_to_concept", "justification": "...", "additional_information": "..."}}
{"is_mutually_related": false, "reason": null}
"""

    prompt = replace_args(_param=param, content=prompt)
    return SystemMessage(content=prompt)

def get_llm_response(param: dict, api_key: str) -> FunctionConceptEdge | None:
    chat = ChatOpenAI(model="gpt-4.1-nano", openai_api_key=api_key)
    try:
        msg = get_prompt(param=param)
        response: BaseMessage = chat.invoke([msg])
        return json.loads(response.content)
    except Exception as e:
        print(f"error ::: {e}")
        return None

if __name__ == "__main__":
    api_key = ''
    all_nodes = get_all_functions()
    all_concepts = get_all_concepts()

    # for idx, con in enumerate(all_concepts):
    #     param = all_nodes[28] | con
    #     s_message = get_prompt(param=param)#
    #     print(f'{idx}-----\n{s_message.content}\n-----')

    param = all_nodes[40] | {'concepts_str': json.dumps(all_concepts, ensure_ascii=False)}
    s_message = get_prompt(param=param)
    print(f'-----\n{s_message.content}\n-----')
    # edge = get_llm_response(param=param, api_key=api_key)
    # print(edge)

    # 예시: 모든 함수 ↔ 모든 개념 쌍에 대해 LLM 추론 (실제론 적절한 candidate만 추려서 수행)
    # result_edges: list[FunctionConceptEdge] = []
    # for node in all_nodes:
    #     for concept in all_concepts:
    #         edge = get_llm_edge(node, concept, api_key)
    #         if edge:
    #             result_edges.append(edge)
    #             print(edge)
    # print(f"총 추론된 function↔concept 관계 수: {len(result_edges)}")
