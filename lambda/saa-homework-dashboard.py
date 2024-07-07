import json
import boto3
from boto3.dynamodb.conditions import Key, Attr
import os
from decimal import Decimal


class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super(DecimalEncoder, self).default(obj)


dynamodb = boto3.resource("dynamodb")
homework_table = dynamodb.Table(os.environ["HOMEWORK_RESULT_TABLE"])
users_table = dynamodb.Table(os.environ["USERS_TABLE"])


def lambda_handler(event, context):
    json_body = json.loads(event["body"])
    operation = json_body["operation"]
    payload = json_body["payload"]

    if operation == "get_homework_results":
        return get_homework_results(payload)
    else:
        return {"statusCode": 400, "body": json.dumps("Unsupported operation")}


def get_homework_results(payload):
    date = payload["date"]
    quiz_topic = payload["quiz_topic"]
    view_basis = payload["view_basis"]

    if view_basis == "학생":
        return get_student_view(date, quiz_topic)
    else:
        return get_question_view(date, quiz_topic)


def get_student_view(date, quiz_topic):
    response = homework_table.scan(
        FilterExpression=Attr("date_quiz_idx").begins_with(date)
        & Attr("quiz_topic").eq(quiz_topic)
    )

    results = {}
    for item in response["Items"]:
        user_id = item["user_id"]
        if user_id not in results:
            results[user_id] = {
                "user_name": item["user_name"],
                "correct": 0,
                "incorrect": 0,
                "correct_questions": [],
                "incorrect_questions": [],
            }

        if item["is_correct"]:
            results[user_id]["correct"] += 1
            results[user_id]["correct_questions"].append(item["quiz_idx"])
        else:
            results[user_id]["incorrect"] += 1
            results[user_id]["incorrect_questions"].append(item["quiz_idx"])

    return {
        "statusCode": 200,
        "body": json.dumps(list(results.values()), cls=DecimalEncoder),
    }


def get_question_view(date, quiz_topic):
    response = homework_table.scan(
        FilterExpression=Attr("date_quiz_idx").begins_with(date)
        & Attr("quiz_topic").eq(quiz_topic)
    )

    results = {}
    for item in response["Items"]:
        quiz_idx = item["quiz_idx"]
        if quiz_idx not in results:
            results[quiz_idx] = {
                "quiz_idx": quiz_idx,
                "correct_count": 0,
                "incorrect_count": 0,
                "correct_students": [],
                "incorrect_students": [],
            }

        if item["is_correct"]:
            results[quiz_idx]["correct_count"] += 1
            results[quiz_idx]["correct_students"].append(item["user_name"])
        else:
            results[quiz_idx]["incorrect_count"] += 1
            results[quiz_idx]["incorrect_students"].append(item["user_name"])

    return {
        "statusCode": 200,
        "body": json.dumps(list(results.values()), cls=DecimalEncoder),
    }
