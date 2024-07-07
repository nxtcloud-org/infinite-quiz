# topic_config.py

import config

TOPICS = {
    "s3_cloudfront": {
        "title": "S3 & CloudFront",
        "file": config.S3_CLOUDFRONT_HOMEWORK_FILE,
        "quiz_id": "S3_CF_HW",
    },
    "ai": {
        "title": "AI Services",
        "file": config.AI_HOMEWORK_FILE,
        "quiz_id": "AI_HW",
    },
    "iam": {
        "title": "Identity and Access Management",
        "file": config.IAM_HOMEWORK_FILE,
        "quiz_id": "IAM_HW",
    },
    "classic": {
        "title": "Classic Architecture",
        "file": config.CLASSIC_HOMEWORK_FILE,
        "quiz_id": "CLASSIC_HW",
    },
}


def load_topic_config(topic):
    return TOPICS.get(topic, TOPICS["s3_cloudfront"])
