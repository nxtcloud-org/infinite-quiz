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
    is_correct = payload["is_correct"]
    quiz_completed = payload.get("quiz_completed", False)

    try:
        response = users_table.get_item(Key={"user_id": user_id})
        user = response["Item"]

        update_expression = "SET "
        expression_attribute_values = {}

        if is_correct:
            update_expression += "correct = correct + :inc, "
            expression_attribute_values[":inc"] = 1
            update_expression += "point = point + :correct_points, "
            expression_attribute_values[":correct_points"] = 3  # CORRECT_ANSWER_POINTS
        else:
            update_expression += "wrong = wrong + :inc, "
            expression_attribute_values[":inc"] = 1
            update_expression += "point = point + :wrong_points, "
            expression_attribute_values[":wrong_points"] = 1  # WRONG_ANSWER_POINTS

        if quiz_completed:
            update_expression += "success = success + :inc, "
            expression_attribute_values[":inc"] = 1
            update_expression += "point = point + :bonus_points, "
            expression_attribute_values[":bonus_points"] = 30  # QUIZ_SUCCESS_BONUS
        else:
            update_expression += "failure = failure + :inc, "
            expression_attribute_values[":inc"] = 1

        update_expression += "attempts = attempts + :inc"
        expression_attribute_values[":inc"] = 1

        users_table.update_item(
            Key={"user_id": user_id},
            UpdateExpression=update_expression,
            ExpressionAttributeValues=expression_attribute_values,
        )

        return {"statusCode": 200, "body": json.dumps("User data updated successfully")}
    except ClientError as e:
        return {
            "statusCode": 500,
            "body": json.dumps(f"Error updating user data: {str(e)}"),
        }


def save_challenge_result(payload):
    user_id = payload["user_id"]
    success = payload["success"]
    correct_answers = payload["correct_answers"]
    challenge_size = payload["challenge_size"]
    wrong_answers = challenge_size - correct_answers
    correct_questions = payload.get("correct_questions", [])
    wrong_questions = payload.get("wrong_questions", [])

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
                "date": current_date,
                "attempts": 0,
                "successes": 0,
                "total_correct": 0,
                "total_wrong": 0,
                "correct_questions": {},
                "wrong_questions": {},
            },
        )

        # 데이터 업데이트
        item["attempts"] += 1
        item["successes"] += 1 if success else 0
        item["total_correct"] += correct_answers
        item["total_wrong"] += wrong_answers

        # 맞춘 문제와 틀린 문제 업데이트
        for q_idx in correct_questions:
            item["correct_questions"][q_idx] = (
                item["correct_questions"].get(q_idx, 0) + 1
            )
        for q_idx in wrong_questions:
            item["wrong_questions"][q_idx] = item["wrong_questions"].get(q_idx, 0) + 1

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
