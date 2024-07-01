import streamlit as st
import config
import json
from datetime import datetime
from utils.helpers import load_questions

st.set_page_config(page_title="연습 퀴즈", page_icon="📚", layout="wide")


# 사용자 데이터 로드 함수
def load_users():
    with open(config.STUDENTS_FILE, "r") as f:
        return json.load(f)


# 사용자 데이터 저장 함수
def save_users(users):
    with open(config.STUDENTS_FILE, "w") as f:
        json.dump(users, f)


def update_student_data(name, is_correct):
    students = load_users()

    if name in students:
        if "wrong" not in students[name]:
            students[name]["wrong"] = 0
        if "correct" not in students[name]:
            students[name]["correct"] = 0

        if is_correct:
            students[name]["correct"] += 1
            students[name]["point"] += config.CORRECT_ANSWER_POINTS
        else:
            students[name]["wrong"] += 1
            students[name]["point"] += config.WRONG_ANSWER_POINTS

    save_users(students)


def save_quiz_result(name):
    current_date = datetime.now().strftime("%Y-%m-%d")

    try:
        with open(config.RESULTS_FILE, "r") as f:
            results = json.load(f)
    except FileNotFoundError:
        results = {}

    if current_date not in results:
        results[current_date] = {}

    if name not in results[current_date]:
        results[current_date][name] = {
            "correct": 0,
            "wrong": 0,
            "attempts": 0,
        }

    results[current_date][name]["correct"] += st.session_state["correct_answers"]
    results[current_date][name]["wrong"] += st.session_state["wrong_answers"]
    results[current_date][name]["attempts"] += 1

    with open(config.RESULTS_FILE, "w") as f:
        json.dump(results, f)


# 세션 상태 초기화 함수
def initialize_session_state():
    if "questions" not in st.session_state:
        st.session_state["questions"] = load_questions(config.QUESTIONS_FILE)

    if "current_question" not in st.session_state:
        st.session_state["current_question"] = 0

    if "correct_answers" not in st.session_state:
        st.session_state["correct_answers"] = 0

    if "wrong_answers" not in st.session_state:
        st.session_state["wrong_answers"] = 0

    if "answered" not in st.session_state:
        st.session_state["answered"] = [False] * len(st.session_state["questions"])

    if "user_answers" not in st.session_state:
        st.session_state["user_answers"] = [None] * len(st.session_state["questions"])


def is_length_greater_than_two(lst):
    return len(lst) >= 2


# 로그인 상태 확인
if "user" not in st.session_state:
    st.warning("먼저 로그인해주세요.")
    st.info("좌측 사이드바에서 '🔐 Login' 페이지로 이동하여 로그인하세요.")
    st.stop()

# 세션 상태 초기화
initialize_session_state()

st.title("📚 :blue[_연습 퀴즈_]")

name = st.session_state["user"]["name"]
st.header(f"{name}님 :blue[화이팅!]", divider="rainbow")

# 현재 문제 표시
current_q = st.session_state["current_question"]
question = st.session_state["questions"][current_q]

st.subheader(f"문제 {current_q + 1} / {len(st.session_state['questions'])}")

st.divider()
tab1, tab2 = st.tabs(["KOR", "ENG"])
with tab1:
    st.write(question["question"]["kor"])
with tab2:
    st.write(question["question"]["eng"])
st.divider()

is_multiple_answer = is_length_greater_than_two(question["answer"])

options = list(question["choices"]["kor"].values())

if is_multiple_answer:
    st.write(":orange[복수 정답] 문제입니다. 해당하는 :orange[모든 답을 선택]하세요.")
    st.write("긴 문제는 선택지에 :orange[마우스를 올려두면] 보입니다.")
    user_answer = st.multiselect("답을 선택하세요:", options, key=f"answer_{current_q}")
else:
    user_answer = st.radio("답을 선택하세요:", options, key=f"answer_{current_q}")

on = st.toggle("영문 선택지 확인하기")

if on:
    for i in question["choices"]["eng"]:
        st.write(f"{i} : {question['choices']['eng'][i]}")

st.divider()

# 답변 제출 버튼
if st.button("답변 제출", type="primary"):
    st.session_state["user_answers"][current_q] = user_answer

    if is_multiple_answer:
        correct_options = [
            question["choices"]["kor"][ans] for ans in question["answer"]
        ]
        is_correct = set(user_answer) == set(correct_options)
    else:
        correct_option = question["choices"]["kor"][question["answer"][0]]
        is_correct = user_answer == correct_option

    if is_correct:
        st.success("정답입니다!")
        st.session_state["correct_answers"] += 1
        update_student_data(name, True)
    else:
        st.error("틀렸습니다.")
        st.session_state["wrong_answers"] += 1
        update_student_data(name, False)

    st.session_state["answered"][current_q] = True

    # 정답 표시
    if is_multiple_answer:
        st.info(f"정답: {', '.join(correct_options)}")
    else:
        st.info(f"정답: {correct_option}")

# 이전 문제 버튼
col1, col2 = st.columns(2)
with col1:
    if st.button("이전 문제", disabled=(current_q == 0)):
        st.session_state["current_question"] = max(0, current_q - 1)
        st.rerun()

# 다음 문제 버튼
with col2:
    if st.button(
        "다음 문제", disabled=(current_q == len(st.session_state["questions"]) - 1)
    ):
        st.session_state["current_question"] = min(
            len(st.session_state["questions"]) - 1, current_q + 1
        )
        st.rerun()

# 퀴즈 종료 버튼
if st.button("퀴즈 종료", type="primary"):
    save_quiz_result(name)
    st.success(
        f"퀴즈가 종료되었습니다. 총 {len(st.session_state['questions'])}문제 중 {st.session_state['correct_answers']}문제를 맞추셨습니다."
    )
    st.balloons()
    if st.button("퀴즈 다시 시작"):
        initialize_session_state()
        st.rerun()

# 퀴즈 진행 상황 표시
st.sidebar.progress(
    st.session_state["current_question"] / len(st.session_state["questions"])
)
st.sidebar.write(
    f"{st.session_state['current_question'] + 1} / {len(st.session_state['questions'])} 문제"
)
st.sidebar.write(f"맞은 문제: {st.session_state['correct_answers']}")
st.sidebar.write(f"틀린 문제: {st.session_state['wrong_answers']}")
