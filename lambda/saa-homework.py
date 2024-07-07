import json
import boto3
from datetime import datetime
import os
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

dynamodb = boto3.resource("dynamodb")
HOME_WORK_RESULT_TABLE_NAME = os.environ.get("HOME_WORK_RESULT_TABLE_NAME")
home_work_table = dynamodb.Table(HOME_WORK_RESULT_TABLE_NAME)


def lambda_handler(event, context):
    json_body = json.loads(event["body"])
    logger.info(f"Received event: {json.dumps(json_body)}")

    operation = json_body["operation"]
    payload = json_body["payload"]
    if operation == "save_homework_result":
        return save_homework_result(payload)
    else:
        return {"statusCode": 400, "body": json.dumps("Unsupported operation")}


def save_homework_result(payload):
    user_id = payload["user_id"]
    user_name = payload["username"]
    quiz_idx = payload["quiz_idx"]
    date = payload["date"]
    is_correct = payload["is_correct"]
    quiz_topic = payload["quiz_topic"]

    date_quiz_idx = f"{date}#{quiz_idx}"

    try:
        response = home_work_table.update_item(
            Key={"user_id": user_id, "date_quiz_idx": date_quiz_idx},
            UpdateExpression="SET user_name = :user_name, "
            "quiz_topic = :quiz_topic, "
            "is_correct = :is_correct, "
            "quiz_idx = :quiz_idx",
            ExpressionAttributeValues={
                ":user_name": user_name,
                ":is_correct": is_correct,
                ":quiz_topic": quiz_topic,
                ":quiz_idx": quiz_idx,
            },
            ReturnValues="UPDATED_NEW",
        )
        logger.info(f"DynamoDB update response: {json.dumps(response)}")
        return {
            "statusCode": 200,
            "body": json.dumps("Homework result saved successfully"),
        }
    except Exception as e:
        logger.error(f"Error saving homework result: {str(e)}")
        return {
            "statusCode": 500,
            "body": json.dumps(f"Error saving homework result: {str(e)}"),
        }
