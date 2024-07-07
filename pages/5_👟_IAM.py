import streamlit as st
import config
from topic_config import load_topic_config
from utils.helpers import load_homework_questions
import requests
from datetime import datetime

# 현재 홈워크 주제 설정
CURRENT_TOPIC = "iam"  # 이 부분은 각 파일마다 다르게 설정

# Lambda 함수 URL
HOMEWORK_LAMBDA_URL = config.HOMEWORK_LAMBDA_URL


def invoke_lambda(operation, payload):
    try:
        response = requests.post(
            HOMEWORK_LAMBDA_URL, json={"operation": operation, "payload": payload}
        )
        return response.json()
    except Exception as e:
        st.error(f"Error calling Lambda function: {str(e)}")
        return None


def initialize_session_state(questions, topic):
    if f"{topic}_current_question" not in st.session_state:
        st.session_state[f"{topic}_current_question"] = 0
    if f"{topic}_answers" not in st.session_state:
        st.session_state[f"{topic}_answers"] = {}
    if f"{topic}_total_questions" not in st.session_state:
        st.session_state[f"{topic}_total_questions"] = len(questions)
    if f"{topic}_user_answer" not in st.session_state:
        st.session_state[f"{topic}_user_answer"] = None
    if f"{topic}_show_result" not in st.session_state:
        st.session_state[f"{topic}_show_result"] = False


def is_multiple_answer(question):
    return len(question["answer"]) > 1


st.set_page_config(
    page_title=f"{CURRENT_TOPIC.upper()} Homework", page_icon="👟", layout="wide"
)

st.title(f"👟 {CURRENT_TOPIC.upper()} Homework")

# 사용자 인증 확인
if "user" not in st.session_state:
    st.warning("먼저 로그인해주세요.")
    st.info("좌측 사이드바에서 '🔐 Login' 페이지로 이동하여 로그인하세요.")
    st.stop()

user = st.session_state["user"]
user_id = user["user_id"]
username = user["username"]

# 현재 주제에 대한 설정 로드
topic_config = load_topic_config(CURRENT_TOPIC)
QUIZ_ID = topic_config["quiz_id"]

# 문제 로드 (세션에 없으면 새로 로드)
if f"{CURRENT_TOPIC}_questions" not in st.session_state:
    st.session_state[f"{CURRENT_TOPIC}_questions"] = load_homework_questions(
        topic_config["file"]
    )

questions = st.session_state[f"{CURRENT_TOPIC}_questions"]

# 세션 상태 초기화
initialize_session_state(questions, CURRENT_TOPIC)

st.header(f"{username}님의 {topic_config['title']} 숙제", divider="rainbow")

# 현재 문제 표시
current_q = st.session_state[f"{CURRENT_TOPIC}_current_question"]
question = questions[current_q]
quiz_idx = question["idx"]

st.subheader(
    f"문제 {current_q + 1} / {st.session_state[f'{CURRENT_TOPIC}_total_questions']}"
)

tab1, tab2 = st.tabs(["한국어", "English"])

with tab1:
    st.write(f"문제 idx : {quiz_idx}")
    st.write(question["question"]["kor"])

with tab2:
    st.write(f"문제 idx : {quiz_idx}")
    st.write(question["question"]["eng"])

options = list(question["choices"]["kor"].values())
if is_multiple_answer(question):
    st.write(":orange[복수 정답] 문제입니다. 해당하는 :orange[모든 답을 선택]하세요.")
    user_answer = st.multiselect(
        "답을 선택하세요:", options, key=f"{CURRENT_TOPIC}_q_{current_q}"
    )
else:
    user_answer = st.radio(
        "답을 선택하세요:", options, key=f"{CURRENT_TOPIC}_q_{current_q}"
    )

# 영어 선택지 확인 토글
show_english = st.toggle("영문 선택지 확인하기")
if show_english:
    st.write("영문 선택지:")
    for key, value in question["choices"]["eng"].items():
        st.write(f"{key}: {value}")

if st.button("제출", type="primary"):
    with st.spinner("결과 확인 중..."):
        st.session_state[f"{CURRENT_TOPIC}_user_answer"] = user_answer
        if is_multiple_answer(question):
            correct_options = [
                question["choices"]["kor"][ans] for ans in question["answer"]
            ]
            is_correct = set(user_answer) == set(correct_options)
        else:
            correct_option = question["choices"]["kor"][question["answer"][0]]
            is_correct = user_answer == correct_option

        st.session_state[f"{CURRENT_TOPIC}_answers"][current_q] = is_correct
        st.session_state[f"{CURRENT_TOPIC}_show_result"] = True

        # 결과 저장
        invoke_lambda(
            "save_homework_result",
            {
                "user_id": user_id,
                "username": username,
                "date": datetime.now().strftime("%Y-%m-%d"),
                "quiz_idx": str(question["idx"]),
                "is_correct": is_correct,
                "quiz_topic": "iam",
            },
        )

# 결과 표시
if st.session_state[f"{CURRENT_TOPIC}_show_result"]:
    if st.session_state[f"{CURRENT_TOPIC}_answers"][current_q]:
        st.success("정답입니다!")
    else:
        st.error("틀렸습니다.")
        if is_multiple_answer(question):
            st.error(
                f'당신의 오답: {", ".join(st.session_state[f"{CURRENT_TOPIC}_user_answer"])}'
            )
            st.success(
                f'정답: {", ".join([question["choices"]["kor"][ans] for ans in question["answer"]])}'
            )
        else:
            st.error(f"당신의 오답: {st.session_state[f'{CURRENT_TOPIC}_user_answer']}")
            st.success(f'정답: {question["choices"]["kor"][question["answer"][0]]}')

# 이전/다음 문제 버튼
col1, col2 = st.columns(2)
with col1:
    if st.button("이전 문제", disabled=(current_q == 0)):
        st.session_state[f"{CURRENT_TOPIC}_current_question"] = max(0, current_q - 1)
        st.session_state[f"{CURRENT_TOPIC}_show_result"] = False
        st.rerun()

with col2:
    if st.button(
        "다음 문제",
        disabled=(
            current_q == st.session_state[f"{CURRENT_TOPIC}_total_questions"] - 1
        ),
    ):
        st.session_state[f"{CURRENT_TOPIC}_current_question"] = min(
            st.session_state[f"{CURRENT_TOPIC}_total_questions"] - 1, current_q + 1
        )
        st.session_state[f"{CURRENT_TOPIC}_show_result"] = False
        st.rerun()

# 진행 상황 표시
st.sidebar.progress(
    (current_q + 1) / st.session_state[f"{CURRENT_TOPIC}_total_questions"]
)
st.sidebar.write(
    f"{current_q + 1} / {st.session_state[f'{CURRENT_TOPIC}_total_questions']} 문제"
)

# 초기화 버튼
if st.sidebar.button("다시 시작"):
    st.session_state[f"{CURRENT_TOPIC}_current_question"] = 0
    st.session_state[f"{CURRENT_TOPIC}_answers"] = {}
    st.session_state[f"{CURRENT_TOPIC}_show_result"] = False
    st.rerun()

# 사이드바에 사용자 정보 및 로그아웃 버튼 표시
if "user" in st.session_state:
    st.sidebar.success(f"{st.session_state['user']['username']}님 로그인됨")
    if st.sidebar.button("로그아웃", key=f"logout_button_{CURRENT_TOPIC}"):
        del st.session_state["user"]
        st.rerun()
else:
    st.sidebar.info("로그인이 필요합니다.")
