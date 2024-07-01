import streamlit as st
from utils.helpers import load_questions, load_results
import config
import json

st.set_page_config(
    page_title=config.APP_TITLE, page_icon=config.APP_ICON, layout="wide"
)


def update_user_data_structure():
    with open(config.STUDENTS_FILE, "r") as f:
        students = json.load(f)

    updated = False
    for name, data in students.items():
        if "wrong" not in data:
            data["wrong"] = 0
            updated = True
        if "correct" not in data:
            data["correct"] = data.get("success", 0) * config.QUIZ_SIZE
            updated = True
        data["attempts"] = data.get("success", 0) + data.get("failure", 0)
        updated = True

    if updated:
        with open(config.STUDENTS_FILE, "w") as f:
            json.dump(students, f)


def update_quiz_results_structure():
    try:
        with open(config.RESULTS_FILE, "r") as f:
            results = json.load(f)
    except FileNotFoundError:
        return

    updated = False
    for date, date_data in results.items():
        for name, user_data in date_data.items():
            if "success" not in user_data:
                user_data["success"] = 0
                updated = True
            if "failure" not in user_data:
                user_data["failure"] = 0
                updated = True
            if "correct" not in user_data:
                user_data["correct"] = user_data["success"] * config.QUIZ_SIZE
                updated = True
            if "wrong" not in user_data:
                user_data["wrong"] = user_data["failure"] * config.QUIZ_SIZE
                updated = True
            user_data["attempts"] = user_data["success"] + user_data["failure"]
            updated = True

    if updated:
        with open(config.RESULTS_FILE, "w") as f:
            json.dump(results, f)


# 앱 시작 시 데이터 구조 업데이트
update_user_data_structure()
update_quiz_results_structure()

if "questions" not in st.session_state:
    st.session_state["questions"] = load_questions(config.QUESTIONS_FILE)

if "results" not in st.session_state:
    st.session_state["results"] = load_results(config.RESULTS_FILE)

st.title(":blue[_AWS SAA_] 제조기 :sunglasses:")

col1, col2 = st.columns(2)

with col1:
    st.header("📢 :blue[_Notice_]", divider="rainbow")
    st.markdown(
        """
        - :orange[매일 수행]해야하는 과제입니다.
        - 자격증 합격을 위해서는 :orange[반복적으로 많은 문제를 풀어보는 것]이 필수입니다.
        - 총 50문제에서 랜덤으로 문제를 추출해서 퀴즈로 제시합니다.
        - :orange[로그인 후 퀴즈 탭으로 이동해서 퀴즈를 진행]합니다.
        - 문제는 :orange[연속으로 모두 맞춰야 성공]입니다.
        - :orange[실패 시 다시 퀴즈를 시작]합니다.
        - 관리자는 여러분이 몇 번의 시도 중 몇 번의 실패와 성공을 했는지 확인합니다.
        - :orange[하루에 반드시 1회 이상의 성공]을 기록해야합니다.
        """
    )

with col2:
    st.header("👀 :blue[_관리자 확인_] 예시", divider="rainbow")
    st.image(
        "example.png",
        caption="하루에 성공을 하나씩 쌓는게 중요합니다. 실패는 중요하지 않아요",
    )

st.divider()

# 로그인 상태 확인
if "user" not in st.session_state:
    st.warning("퀴즈를 시작하려면 먼저 로그인해주세요.")
    st.info("좌측 사이드바에서 '🔐 Login' 페이지로 이동하여 로그인하세요.")
else:
    st.header(
        f"🏁 :blue[_{st.session_state['user']['name']}_]님, 환영합니다!",
        divider="rainbow",
    )

    st.divider()

    st.subheader(
        f"이 퀴즈는 총 :blue[_{config.QUIZ_SIZE}개_]의 문제를 :blue[_연속_]으로 맞춰야 합니다."
    )
