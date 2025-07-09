from langchain_openai.chat_models import ChatOpenAI
from langchain.schema import SystemMessage, HumanMessage
from langchain_core.messages import BaseMessage
from arango import ArangoClient
import json

# 환경 변수 로드 (OPENAI_API_KEY)
openai_api_key = ''

# ArangoDB 연결 설정
client = ArangoClient()
db = client.db("_system", username="root", password="openSesame")
nodes_collection = db.collection("nodes")
edges_collection = db.collection("edges")

# LLM 설정
chat = ChatOpenAI(model="gpt-4.1-nano", openai_api_key=openai_api_key)

system_prompt = SystemMessage(
    content=(
        "You are an helpful AI assistance.\n"
        "You have python codes.\n"
        "Arguments as various types of arguments as str, and content as str.\n"
        "You have to summarize how it works, you have to answer as JSON string\n"
        '{"reason" : "it is about..."}'
    )
)

# Step 1: 차수 높은 노드 목록 불러오기
aql_query = """
LET outDegrees = (
  FOR e IN edges
    COLLECT vertex = e._from WITH COUNT INTO degree
    RETURN { vertex, degree }
)

LET inDegrees = (
  FOR e IN edges
    COLLECT vertex = e._to WITH COUNT INTO degree
    RETURN { vertex, degree }
)

LET merged = (
  FOR o IN outDegrees
    LET i = FIRST(FOR x IN inDegrees FILTER x.vertex == o.vertex RETURN x)
    RETURN {
      vertex: o.vertex,
      degree: o.degree + (i != null ? i.degree : 0)
    }
)

FOR doc IN merged
  SORT doc.degree DESC
  RETURN doc.vertex
"""

node_keys = [doc for doc in db.aql.execute(aql_query)]
print(f'node_keys ::: {node_keys}')

# Step 2~4: 각 노드에 대해 defined_in edge를 검사하고 LLM으로 reason 생성
for node_key in node_keys:
    node_id = node_key.split("/")[-1]
    node = nodes_collection.get(node_id)
    if not node:
        continue

    edge_query = """
    FOR e IN nodes
        FILTER e._key == @node_key AND HAS(e, "source")
        RETURN e
    """
    edge_results = list(db.aql.execute(edge_query, bind_vars={"node_key": node_id}))

    print(f'edge_results ::: {edge_results}')
    for edge in edge_results:
        source_code = edge.get("source", "")
        if not source_code:
            continue

        user_prompt = HumanMessage(content=source_code)
        try:
            response: BaseMessage = chat.invoke([system_prompt, user_prompt])
            result_json = json.loads(response.content)
            if "reason" in result_json:
                node["reason"] = result_json["reason"]
                print(f'reason ::: {result_json["reason"]}')
                nodes_collection.update(node)
        except Exception as e:
            print(f"Error processing node {node_key}: {e}")

print("Processing complete.")