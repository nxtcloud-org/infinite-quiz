import json
import boto3
from botocore.exceptions import ClientError
import uuid
import os
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# 환경 변수에서 테이블 이름을 가져옵니다. 이렇게 하면 향후 다른 테이블을 사용할 때 유연하게 대응할 수 있습니다.
TABLE_NAME = os.environ.get("USER_TABLE_NAME")

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(TABLE_NAME)


def lambda_handler(event, context):
    logger.info(f"Received event: {json.dumps(event)}")

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
        "update_user": update_user,
    }

    if operation in operations:
        try:
            result = operations[operation](payload)
            logger.info(f"Operation result: {json.dumps(result)}")
            return json.dumps(result)
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
                "success": 0,
                "failure": 0,
                "attempts": 0,
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
    password = payload["password"]

    try:
        response = table.query(
            IndexName="username-index",
            KeyConditionExpression="username = :username",
            ExpressionAttributeValues={":username": username},
        )

        if response["Items"]:
            user = response["Items"][0]
            if user["password"] == password:
                return {
                    "statusCode": 200,
                    "body": json.dumps({"user_id": user["user_id"]}),
                }
            else:
                return {"statusCode": 401, "body": json.dumps("Incorrect password")}
        else:
            return {"statusCode": 404, "body": json.dumps("User not found")}
    except ClientError as e:
        return {"statusCode": 500, "body": json.dumps("Error during login")}


def get_user(payload):
    user_id = payload["user_id"]

    try:
        response = table.get_item(Key={"user_id": user_id})
        if "Item" in response:
            user = response["Item"]
            del user["password"]  # 보안을 위해 비밀번호는 제외
            return {"statusCode": 200, "body": json.dumps(user)}
        else:
            return {"statusCode": 404, "body": json.dumps("User not found")}
    except ClientError as e:
        return {"statusCode": 500, "body": json.dumps("Error retrieving user")}


def update_user(payload):
    user_id = payload["user_id"]
    updates = payload["updates"]

    update_expression = "SET "
    expression_attribute_values = {}

    for key, value in updates.items():
        if key not in ["user_id", "username", "password"]:  # 이러한 필드는 변경 불가
            update_expression += f"{key} = :{key}, "
            expression_attribute_values[f":{key}"] = value

    update_expression = update_expression.rstrip(", ")

    try:
        response = table.update_item(
            Key={"user_id": user_id},
            UpdateExpression=update_expression,
            ExpressionAttributeValues=expression_attribute_values,
            ReturnValues="UPDATED_NEW",
        )
        return {"statusCode": 200, "body": json.dumps("User updated successfully")}
    except ClientError as e:
        return {"statusCode": 500, "body": json.dumps("Error updating user")}


# 추가: school이나 team으로 사용자 검색 함수
def search_users_by_school(school):
    try:
        response = table.query(
            IndexName="school-index",
            KeyConditionExpression="school = :school",
            ExpressionAttributeValues={":school": school},
        )
        return {"statusCode": 200, "body": json.dumps(response["Items"])}
    except ClientError as e:
        return {
            "statusCode": 500,
            "body": json.dumps("Error searching users by school"),
        }


def search_users_by_team(team):
    try:
        response = table.query(
            IndexName="team-index",
            KeyConditionExpression="team = :team",
            ExpressionAttributeValues={":team": team},
        )
        return {"statusCode": 200, "body": json.dumps(response["Items"])}
    except ClientError as e:
        return {"statusCode": 500, "body": json.dumps("Error searching users by team")}
