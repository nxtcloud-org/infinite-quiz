import json
import boto3
import os
from botocore.exceptions import ClientError
from datetime import datetime

USERS_TABLE_NAME = os.environ.get("USERS_TABLE_NAME")
CHALLENGE_RESULT_TABLE_NAME = os.environ.get("CHALLENGE_RESULT_TABLE_NAME")

dynamodb = boto3.resource("dynamodb")
users_table = dynamodb.Table(USERS_TABLE_NAME)
challenge_results_table = dynamodb.Table(CHALLENGE_RESULT_TABLE_NAME)


def lambda_handler(event, context):
    json_body = json.loads(event["body"])
    operation = json_body["operation"]
    payload = json_body["payload"]

    operations = {
        "update_user_data": update_user_data,
        "save_challenge_result": save_challenge_result,
    }

    if operation in operations:
        return operations[operation](payload)
    else:
        return {"statusCode": 400, "body": json.dumps("Unsupported operation")}


def update_user_data(payload):
    user_id = payload["user_id"]
    quiz_idx = str(payload["quiz_idx"])  # 문자열로 변환
    is_correct = payload["is_correct"]
    challenge_completed = payload.get("challenge_completed", False)
    print("퀴즈 성공이야?")
    print(challenge_completed)

    try:
        update_expression = "SET "
        expression_attribute_values = {":zero": 0, ":inc": 1}
        expression_attribute_names = {"#qidx": quiz_idx}

        point_increase = 0

        if is_correct:
            print("문제 맞춘 경우")
            update_expression += (
                "correct_idx.#qidx = if_not_exists(correct_idx.#qidx, :zero) + :inc, "
            )
            point_increase += 3  # CORRECT_ANSWER_POINTS
        else:
            print("문제 틀린 경우")
            update_expression += (
                "challenge_failure = if_not_exists(challenge_failure, :zero) + :inc, "
                "challenge_attempts = if_not_exists(challenge_attempts, :zero) + :inc, "
                "incorrect_idx.#qidx = if_not_exists(incorrect_idx.#qidx, :zero) + :inc, "
            )
            point_increase += 1  # WRONG_ANSWER_POINTS

        if challenge_completed:
            update_expression += (
                "challenge_attempts = if_not_exists(challenge_attempts, :zero) + :inc, "
                "challenge_success = if_not_exists(challenge_success, :zero) + :inc, "
            )
            point_increase += 100  # QUIZ_SUCCESS_BONUS

        # point 업데이트를 마지막에 한 번만 수행
        update_expression += "point = if_not_exists(point, :zero) + :point_increase, "
        expression_attribute_values[":point_increase"] = point_increase

        # 마지막 쉼표 제거
        update_expression = update_expression.rstrip(", ")

        print("Update Expression:", update_expression)
        print("Expression Attribute Values:", expression_attribute_values)
        print("Expression Attribute Names:", expression_attribute_names)

        result = users_table.update_item(
            Key={"user_id": user_id},
            UpdateExpression=update_expression,
            ExpressionAttributeValues=expression_attribute_values,
            ExpressionAttributeNames=expression_attribute_names,
            ReturnValues="UPDATED_NEW",
        )

        print("Update Result:", result)

        return {"statusCode": 200, "body": json.dumps("User data updated successfully")}
    except ClientError as e:
        print("DynamoDB ClientError:", e.response["Error"]["Message"])
        return {
            "statusCode": 500,
            "body": json.dumps(f"Error updating user data: {str(e)}"),
        }
    except Exception as e:
        print("Unexpected error:", str(e))
        return {
            "statusCode": 500,
            "body": json.dumps(f"Unexpected error: {str(e)}"),
        }


def save_challenge_result(payload):
    user_id = payload["user_id"]
    user_name = payload["user_name"]
    success = payload["success"]
    correct_count = payload["correct_count"]
    incorrect_count = payload["incorrect_count"]

    current_date = datetime.now().strftime("%Y-%m-%d")

    try:
        # 기존 항목 가져오기 (없으면 새로 생성)
        response = challenge_results_table.get_item(
            Key={"user_id": user_id, "date": current_date}
        )
        item = response.get(
            "Item",
            {
                "user_id": user_id,
                "user_name": user_name,
                "date": current_date,
                "attempts": 0,
                "successes": 0,
                "total_correct": 0,
                "total_wrong": 0,
            },
        )

        # 데이터 업데이트
        item["attempts"] += 1
        item["successes"] += 1 if success else 0
        item["total_correct"] += correct_count
        item["total_wrong"] += incorrect_count

        # 업데이트된 항목 저장
        challenge_results_table.put_item(Item=item)

        return {
            "statusCode": 200,
            "body": json.dumps("Challenge result saved successfully"),
        }
    except Exception as e:
        print(f"Error saving challenge result: {str(e)}")  # 로그 추가
        return {
            "statusCode": 500,
            "body": json.dumps(f"Error saving challenge result: {str(e)}"),
        }
