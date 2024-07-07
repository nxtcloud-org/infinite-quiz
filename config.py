import os
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

# 앱 설정
APP_TITLE = "AWS SAA 자격증 제조기"
APP_ICON = "🏠"

# 퀴즈 설정
CHALLENGE_SIZE = 2  # 퀴즈 문제 수

# 문제 파일 경로
CHALLENGE_FILE = "exam/homework1_S3_CloudFront_119.json"
S3_CLOUDFRONT_HOMEWORK_FILE = "exam/homework1_S3_CloudFront_119.json"
AI_HOMEWORK_FILE = "exam/homework2_AI_9.json"
IAM_HOMEWORK_FILE = "exam/homework3_IAM_56.json"
CLASSIC_HOMEWORK_FILE = "exam/homework4_Classic_219.json"

# 람다
USERS_LAMBDA_URL = os.environ.get("USERS_LAMBDA_URL")
CHALLENGE_LAMBDA_URL = os.environ.get("CHALLENGE_LAMBDA_URL")
HOMEWORK_LAMBDA_URL = os.environ.get("HOMEWORK_LAMBDA_URL")
HOMEWORK_CHECK_LAMBDA_URL = os.environ.get("HOMEWORK_CHECK_LAMBDA_URL")

# 관리자 설정
ADMIN_PASSWORD = "4808"

# 학교 목록
SCHOOLS = [
    "Nxtcloud",
    "우송대",
    "호남대",
    "GIST",
    "숙명여대",
    "연세대",
    "인하대",
    "ETC",
]

TEAMS = [
    "Nxtcloud",
    "진성님의지갑털이범들",
    "소고기-먹자",
    "강민",
    "여름학기",
    "Nxtcloud 인턴",
    "ETC",
]
