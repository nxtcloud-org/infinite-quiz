import json
import boto3
from botocore.exceptions import ClientError
import uuid
import os
import logging
from decimal import Decimal

# 로깅 설정
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# 기존 핸들러를 교체
for handler in logger.handlers:
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))


# 사용자 정의 JSON 인코더
class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super(DecimalEncoder, self).default(obj)


# 환경 변수에서 테이블 이름을 가져옵니다.
TABLE_NAME = os.environ.get("USER_TABLE_NAME")

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(TABLE_NAME)


def lambda_handler(event, context):
    logger.info(f"Received event: {json.dumps(event, ensure_ascii=False)}")

    # Lambda URL을 통해 전달된 이벤트에서 body 추출
    if "body" in event:
        try:
            body = json.loads(event["body"])
        except json.JSONDecodeError:
            logger.error("Failed to parse event body as JSON")
            return {
                "statusCode": 400,
                "body": json.dumps("Invalid JSON in request body"),
            }
    else:
        body = event

    # operation과 payload 추출
    operation = body.get("operation")
    payload = body.get("payload", {})

    if not operation:
        logger.error("No operation specified in the event")
        return {"statusCode": 400, "body": json.dumps("No operation specified")}

    operations = {
        "register": register_user,
        "login": login_user,
        "get_user": get_user,
    }

    if operation in operations:
        try:
            result = operations[operation](payload)
            logger.info(
                f"Operation result: {json.dumps(result, ensure_ascii=False, cls=DecimalEncoder)}"
            )
            return json.dumps(result, cls=DecimalEncoder)
        except Exception as e:
            logger.error(f"Error in operation {operation}: {str(e)}")
            return {
                "statusCode": 500,
                "body": json.dumps(f"Error in operation {operation}: {str(e)}"),
            }
    else:
        logger.warning(f"Unsupported operation: {operation}")
        return {"statusCode": 400, "body": json.dumps("Unsupported operation")}


def register_user(payload):
    username = payload["username"]
    password = payload["password"]
    school = payload["school"]
    team = payload.get("team", "")

    # Check if user with same username, school and team exists
    response = table.query(
        IndexName="username-school-team-index",
        KeyConditionExpression="username = :username AND school = :school",
        FilterExpression="team = :team",
        ExpressionAttributeValues={
            ":username": username,
            ":school": school,
            ":team": team,
        },
    )

    if response["Items"]:
        return {
            "statusCode": 400,
            "body": json.dumps({"message": "이미 등록된 사용자입니다."}),
        }

    user_id = str(uuid.uuid4())

    try:
        table.put_item(
            Item={
                "user_id": user_id,
                "username": username,
                "password": password,
                "school": school,
                "team": team,
                "point": 0,
                "challenge_success": 0,
                "challenge_failure": 0,
                "challenge_attempts": 0,
                "correct_idx": {},
                "incorrect_idx": {},
            }
        )
        return {
            "statusCode": 200,
            "body": json.dumps(
                {"message": "회원가입이 완료되었습니다.", "user_id": user_id}
            ),
        }
    except ClientError as e:
        return {
            "statusCode": 500,
            "body": json.dumps({"message": "회원가입 중 오류가 발생했습니다."}),
        }


def login_user(payload):
    username = payload["username"]
    school = payload["school"]
    team = payload["team"]
    password = payload["password"]

    try:
        # 첫 번째 쿼리: 사용자 존재 여부 확인
        response = table.query(
            IndexName="username-school-team-index",
            KeyConditionExpression="username = :username AND school = :school",
            FilterExpression="team = :team",
            ExpressionAttributeValues={
                ":username": username,
                ":school": school,
                ":team": team,
            },
        )

        if response["Items"]:
            user_id = response["Items"][0]["user_id"]

            # 두 번째 쿼리: 사용자의 전체 정보 가져오기
            user_response = table.get_item(Key={"user_id": user_id})

            if "Item" in user_response:
                user = user_response["Item"]
                if str(user["password"]) == str(password):  # 문자열로 변환하여 비교
                    # 비밀번호 확인 후 제거
                    del user["password"]
                    # 문제 정보는 생략
                    del user["correct_idx"]
                    del user["incorrect_idx"]
                    return {
                        "statusCode": 200,
                        "body": json.dumps(user, cls=DecimalEncoder),
                    }
                else:
                    return {
                        "statusCode": 401,
                        "body": json.dumps(
                            {"message": "비밀번호가 올바르지 않습니다."}
                        ),
                    }
            else:
                return {
                    "statusCode": 404,
                    "body": json.dumps({"message": "사용자 정보를 찾을 수 없습니다."}),
                }
        else:
            return {
                "statusCode": 404,
                "body": json.dumps({"message": "사용자를 찾을 수 없습니다."}),
            }
    except ClientError as e:
        logger.error(f"Error during login: {str(e)}")
        return {
            "statusCode": 500,
            "body": json.dumps({"message": "로그인 중 오류가 발생했습니다."}),
        }


def get_user(payload):
    user_id = payload["user_id"]

    try:
        response = table.get_item(Key={"user_id": user_id})
        if "Item" in response:
            user = response["Item"]
            del user["password"]  # 보안을 위해 비밀번호는 제외
            # 문제 정보는 생략
            del user["correct_idx"]
            del user["incorrect_idx"]
            return {"statusCode": 200, "body": json.dumps(user)}
        else:
            return {"statusCode": 404, "body": json.dumps("User not found")}
    except ClientError as e:
        return {"statusCode": 500, "body": json.dumps("Error retrieving user")}
