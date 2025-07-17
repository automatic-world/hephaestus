
import json

def lambda_handler(event, context):
    """
    AWS Lambda 기본 핸들러 함수

    Parameters:
    - event: 호출 시 전달되는 이벤트 정보 (dict)
    - context: 실행 환경에 대한 메타 정보 (object)

    Returns:
    - dict: API Gateway용 JSON 응답 구조
    """
    print("Received event:", json.dumps(event))

    # 예시: GET 요청의 쿼리 파라미터 처리
    name = event.get("queryStringParameters", {}).get("name", "World")

    response = {
        "statusCode": 200,
        "headers": {
            "Content-Type": "application/json"
        },
        "body": json.dumps({
            "message": f"Hello, {name}!"
        })
    }

    return response