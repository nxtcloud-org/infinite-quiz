import os
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

# 앱 설정
APP_TITLE = "AWS SAA 자격증 제조기"
APP_ICON = "🏠"

# 퀴즈 설정
CHALLENGE_SIZE = 2  # 퀴즈 문제 수

# 파일 경로
CHALLENGE_FILE = "exam/homework4_Classic_219.json"
HOMEWORK_FILE = "exam/homework1_S3_CloudFront_119.json"
USERS_LAMBDA_URL = os.environ.get("USERS_LAMBDA_URL")
CHALLENGE_LAMBDA_URL = os.environ.get("CHALLENGE_LAMBDA_URL")

# 관리자 설정
ADMIN_PASSWORD = "4808"

# 포인트 설정
CORRECT_ANSWER_POINTS = 3  # 문제 정답 시 획득 포인트
WRONG_ANSWER_POINTS = 1
QUIZ_SUCCESS_BONUS = 30  # 성공(퀴즈 모두 정답) 시 추가 보너스 포인트

# 학교 목록
SCHOOLS = ["Nxtcloud", "school1", "school2", "school3", "school4", "ETC"]

TEAMS = ["Nxtcloud", "team1", "team2", "team3", "team4", "ETC"]
