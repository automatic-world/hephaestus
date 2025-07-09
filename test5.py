from typing import TypedDict
from langchain_openai.chat_models import ChatOpenAI
from langchain.schema import SystemMessage
from langchain_core.messages import BaseMessage
import json


class SystemInfo(TypedDict):
    description: str
    supported: bool


class ConceptRelation(TypedDict):
    _from: str
    _to: str
    relation_type: str
    relation_category: str
    justification: str


class ConceptDocument(TypedDict):
    concept: str
    description: str
    systems: dict[str, SystemInfo]
    relations: list[ConceptRelation]


def replace_args(_param: dict, content: str) -> str:
    try:
        for key, value in _param.items():
            content = content.replace(f"{{{key}}}", str(value))
        return content
    except Exception as e:
        print(e)
        return content


def get_prompt(_param: dict) -> list[SystemMessage]:
    prompt = """
당신은 두 시스템({source}와 {target})을 비교하여, 각 시스템의 개념과 기능을 구조적으로 분석하고 대응 관계를 추론하는 애플리케이션 전문가입니다.

다음 작업을 순서대로 수행하세요:

---

0. [역할 정의]
- Source는 비교의 기준이 되는 시스템이며, 여기서는 {source}입니다.
- Target은 비교 대상이며, 여기서는 {target}입니다.

---

1. Source({source})의 주요 개념 목록을 도출하세요.
2. Target({target})의 주요 개념 목록을 도출하세요.
3. 각 Source 개념에 대해 Target 개념과의 대응 관계를 추론하고 설명하세요.
   - 개념 간 단순 치환이 아니라, 구조, 목적, 표현 방식 등을 고려한 대응이어야 합니다.
4. JSON의 제일 상위 description 필드엔 각 개념의 포괄적(추상적) 정의를 작성하세요.
   - 두 시스템과 무관하게, 해당 개념 자체가 의미하는 바를 설명합니다.
5. 대응 유형을 다음 중 하나로 분류하세요:
   - "direct", "restructure", "expand", "reduce", "new_concept"
6. relation_category 는 다음 중 하나로 분류하세요
   - "mapping", "hierarchy", "composition", "domain"
7. concept 필드에는 슬래시(/)를 절대 포함하지 마세요.
---

8. 결과는 다음 JSON 형식으로 출력하세요:

[
  {
    "concept": "Query Language",
    "description": "그래프 또는 데이터베이스에 저장된 데이터를 검색, 수정, 삭제하는 명령어 또는 문법",
    "systems": {
      "Neo4j": {
        "concept": "Query Language",
        "description": "Cypher 언어를 사용하여 그래프 질의 수행",
        "supported": true
      },
      "ArangoDB": {
        "concept": "Query Language",
        "description": "AQL(ArangoDB Query Language)을 사용하여 데이터 쿼리 수행",
        "supported": true
      }
    },
    "relations": [
      {
        "_from": "Neo4j_Query-Language",
        "_to": "ArangoDB_Query-Language",
        "relation_type": "correspond_to",
        "relation_category": "mapping",
        "justification": "둘 다 데이터베이스 내 데이터를 질의하는 언어를 제공하며 이름과 문법이 다름"
      },
      {
        "_from": "Query Language",
        "_to": "Neo4j_Query-Language",
        "relation_type": "implements",
        "relation_category": "hierarchy",
        "justification": "Neo4j의 Query Language는 추상 개념으로, Cypher와 같은 구체적 구현"
      },
      {
        "_from": "Query Language",
        "_to": "ArangoDB_Query-Language",
        "relation_type": "implements",
        "relation_category": "hierarchy",
        "justification": "ArangoDB의 Query Language는 AQL로 구체화된 언어"
      }
    ]
  }
]
"""
    return [SystemMessage(content=replace_args(_param, prompt))]


def insert_collections(llm_concepts: list[ConceptDocument]):
    from arango import ArangoClient
    client = ArangoClient()
    db = client.db("_system", username="root", password="openSesame")

    collections = [('concepts', False), ('concept_relation', True)]
    for name, is_edge in collections:
        if not db.has_collection(name):
            db.create_collection(name, edge=is_edge)
            print(f"Created collection: {name}")

    concepts_col = db.collection('concepts')
    edges_col = db.collection('concept_relation')

    for item in llm_concepts:
        concept_key = item['concept'].lower().replace(" ", "-")
        if not concepts_col.has(concept_key):
            concepts_col.insert({
                "_key": concept_key,
                "concept": item["concept"],
                "description": item["description"]
            })


        for sys in item.get("systems", []):
            sys_info = item["systems"][sys]
            sys_concept = f'{sys}_{item["concept"]}'
            child_concept_key = f'{concept_key}__{sys_concept.lower().replace(" ", "-")}'
            if not concepts_col.has(child_concept_key):
                concepts_col.insert({
                    "_key": child_concept_key,
                    "concept": f'{sys} {item["concept"]}',
                    "description": sys_info["description"],
                    "supported": sys_info["supported"]
                })



        for rel in item.get("relations", []):
            _from_val: str = "concepts/" + (concept_key if concept_key == rel["_from"].lower().replace(" ", "-") else concept_key + '__' + rel["_from"].lower().replace(" ", "-"))
            edges_col.insert({
                "_from": _from_val,
                "_to": "concepts/" + concept_key + '__' + rel["_to"].lower().replace(" ", "-"),
                "relation_type": rel["relation_type"],
                "relation_category": rel["relation_category"],
                "justification": rel["justification"]
            })


def get_llm_response(_param: dict) -> list[ConceptDocument]:
    openai_api_key = ''
    chat = ChatOpenAI(model="gpt-4.1-nano", openai_api_key=openai_api_key)

    try:
        response: BaseMessage = chat.invoke(get_prompt(_param))
        print(f'res ::: {response.content}')
        return json.loads(response.content)
    except Exception as e:
        print(f"error ::: {e}")
        return []


if __name__ == "__main__":
    _param = {
        "source": "Neo4j",
        "target": "ArangoDB"
    }

    # concepts_data = get_llm_response(_param)
    concepts_data = [
        {
            "concept": "Graph Model",
            "description": "데이터와 그들 간의 관계를 그래프 구조로 표현하는 데이터 모델",
            "systems": {
                "Neo4j": {
                    "concept": "Graph Model",
                    "description": "노드와 관계로 구성된 그래프 구조를 통해 데이터를 표현",
                    "supported": True
                },
                "ArangoDB": {
                    "concept": "Graph Model",
                    "description": "노드와 엣지로 구성된 그래프 형태의 데이터를 저장하고 처리하는 데이터 모델",
                    "supported": True
                }
            },
            "relations": [
                {
                    "_from": "Neo4j_Graph-Model",
                    "_to": "ArangoDB_Graph-Model",
                    "relation_type": "correspond_to",
                    "relation_category": "mapping",
                    "justification": "두 시스템 모두 노드와 관계를 핵심으로 하는 그래프 구조를 지원함"
                },
                {
                    "_from": "Graph Model",
                    "_to": "Neo4j_Graph-Model",
                    "relation_type": "implements",
                    "relation_category": "hierarchy",
                    "justification": "Neo4j의 그래프 모델은 추상 개념으로, 노드-관계 구조를 구체적으로 구현"
                },
                {
                    "_from": "Graph Model",
                    "_to": "ArangoDB_Graph-Model",
                    "relation_type": "implements",
                    "relation_category": "hierarchy",
                    "justification": "ArangoDB의 그래프 모델 역시 노드와 엣지로 그래프 데이터를 표현하는 구체적 모델"
                }
            ]
        },
        {
            "concept": "Node",
            "description": "그래프 구조에서 개별 데이터 항목 또는 객체를 나타내는 단위",
            "systems": {
                "Neo4j": {
                    "concept": "Node",
                    "description": "그래프의 정점으로서 엔티티 또는 객체를 표현",
                    "supported": True
                },
                "ArangoDB": {
                    "concept": "Node",
                    "description": "그래프에서의 데이터 포인트 또는 엔티티를 나타내는 개체",
                    "supported": True
                }
            },
            "relations": [
                {
                    "_from": "Neo4j_Node",
                    "_to": "ArangoDB_Node",
                    "relation_type": "correspond_to",
                    "relation_category": "mapping",
                    "justification": "두 시스템 모두 그래프 내 개별 객체를 나타내는 개념을 제공함"
                },
                {
                    "_from": "Node",
                    "_to": "Neo4j_Node",
                    "relation_type": "implements",
                    "relation_category": "hierarchy",
                    "justification": "Neo4j의 Node는 추상 개념으로, 구체적 노드 구현"
                },
                {
                    "_from": "Node",
                    "_to": "ArangoDB_Node",
                    "relation_type": "implements",
                    "relation_category": "hierarchy",
                    "justification": "ArangoDB의 Node 역시 그래프의 개별 데이터 엔티티를 나타내는 구체적 개념"
                }
            ]
        },
        {
            "concept": "Relationship",
            "description": "그래프 내에서 노드 간의 연결 또는 관계를 나타내는 구조",
            "systems": {
                "Neo4j": {
                    "concept": "Relationship",
                    "description": "노드 간 연결을 나타내는 엣지 또는 관계",
                    "supported": True
                },
                "ArangoDB": {
                    "concept": "Edge",
                    "description": "그래프 내 두 노드를 연결하는 구조, 관계를 표현하는 요소",
                    "supported": True
                }
            },
            "relations": [
                {
                    "_from": "Neo4j_Relationship",
                    "_to": "ArangoDB_Edge",
                    "relation_type": "correspond_to",
                    "relation_category": "mapping",
                    "justification": "Neo4j의 Relationship와 ArangoDB의 Edge는 그래프 내 연결 구조를 나타내는 개념으로 대응됨"
                },
                {
                    "_from": "Relationship",
                    "_to": "Neo4j_Relationship",
                    "relation_type": "implements",
                    "relation_category": "hierarchy",
                    "justification": "Neo4j의 Relationship은 추상 개념으로, 구체적 엣지 구현"
                },
                {
                    "_from": "Relationship",
                    "_to": "ArangoDB_Edge",
                    "relation_type": "implements",
                    "relation_category": "hierarchy",
                    "justification": "ArangoDB의 Edge 역시 노드 간 연결을 나타내는 구체적 구조"
                }
            ]
        },
        {
            "concept": "Property",
            "description": "노드 또는 관계에 부가하는 속성 또는 설명 정보",
            "systems": {
                "Neo4j": {
                    "concept": "Property",
                    "description": "노드 또는 관계에 저장된 키-값 쌍 형태의 속성",
                    "supported": True
                },
                "ArangoDB": {
                    "concept": "Attribute",
                    "description": "문서 또는 그래프 요소에 속하는 속성 또는 필드",
                    "supported": True
                }
            },
            "relations": [
                {
                    "_from": "Neo4j_Property",
                    "_to": "ArangoDB_Attribute",
                    "relation_type": "correspond_to",
                    "relation_category": "mapping",
                    "justification": "노드나 관계에 부가하는 속성으로서, ArangoDB의 Attribute와 대응됨"
                },
                {
                    "_from": "Property",
                    "_to": "Neo4j_Property",
                    "relation_type": "implements",
                    "relation_category": "hierarchy",
                    "justification": "Neo4j의 Property는 추상적 속성 개념으로 구체적 속성 구현"
                },
                {
                    "_from": "Property",
                    "_to": "ArangoDB_Attribute",
                    "relation_type": "implements",
                    "relation_category": "hierarchy",
                    "justification": "ArangoDB의 Attribute 역시 문서 또는 그래프 요소에 부가하는 속성"
                }
            ]
        },
        {
            "concept": "Query Language",
            "description": "데이터베이스에 저장된 데이터를 검색, 수정, 삭제하는 명령어 또는 문법",
            "systems": {
                "Neo4j": {
                    "concept": "Query Language",
                    "description": "Cypher 언어를 사용하여 그래프 질의 수행",
                    "supported": True
                },
                "ArangoDB": {
                    "concept": "Query Language",
                    "description": "AQL(ArangoDB Query Language)을 사용하여 데이터 쿼리 수행",
                    "supported": True
                }
            },
            "relations": [
                {
                    "_from": "Neo4j_Query-Language",
                    "_to": "ArangoDB_Query-Language",
                    "relation_type": "correspond_to",
                    "relation_category": "mapping",
                    "justification": "둘 다 데이터베이스 내 데이터를 질의하는 언어를 제공하며 이름과 문법이 다름"
                },
                {
                    "_from": "Query Language",
                    "_to": "Neo4j_Query-Language",
                    "relation_type": "implements",
                    "relation_category": "hierarchy",
                    "justification": "Neo4j의 Query Language는 추상 개념으로, Cypher와 같은 구체적 구현"
                },
                {
                    "_from": "Query Language",
                    "_to": "ArangoDB_Query-Language",
                    "relation_type": "implements",
                    "relation_category": "hierarchy",
                    "justification": "ArangoDB의 Query Language는 AQL로 구체화된 언어"
                }
            ]
        }
    ]

    if not concepts_data:
        print("❌ LLM 응답이 비어 있습니다. 작업을 중단합니다.")
        exit(1)

    insert_collections(llm_concepts=concepts_data)
    print("✅ ArangoDB에 개념 비교 결과 저장이 완료되었습니다.")