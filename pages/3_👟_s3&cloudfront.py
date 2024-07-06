import streamlit as st
import config
import json
import os
from datetime import datetime
from utils.helpers import load_homework_questions

st.set_page_config(page_title="Homework", page_icon="📚", layout="wide")

QUIZ_ID = "s3&cloudfront"  # 이 퀴즈의 고유 ID


def load_users():
    with open(config.STUDENTS_FILE, "r") as f:
        return json.load(f)


def save_users(users):
    with open(config.STUDENTS_FILE, "w") as f:
        json.dump(users, f)


def load_questions():
    questions = load_homework_questions(config.HOMEWORK_FILE)
    return questions


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


def update_homework_data(name, question):
    today = datetime.now().strftime("%Y-%m-%d")

    # Ensure the db directory exists
    os.makedirs("db", exist_ok=True)

    # Try to load existing data, or create a new dictionary if the file doesn't exist or is empty
    try:
        with open("db/homework.json", "r") as f:
            content = f.read()
            homework_data = json.loads(content) if content else {}
    except (FileNotFoundError, json.JSONDecodeError):
        homework_data = {}

    if today not in homework_data:
        homework_data[today] = {}

    question_idx = str(question["idx"])
    is_correct = st.session_state.get(f"correct_{question_idx}", False)

    if question_idx not in homework_data[today]:
        homework_data[today][question_idx] = {
            "total_attempts": 0,
            "total_correct": 0,
            "total_wrong": 0,
            "correct_students": [],
            "students": {},
        }

    homework_data[today][question_idx]["total_attempts"] += 1
    if is_correct:
        homework_data[today][question_idx]["total_correct"] += 1
        if name not in homework_data[today][question_idx]["correct_students"]:
            homework_data[today][question_idx]["correct_students"].append(name)
    else:
        homework_data[today][question_idx]["total_wrong"] += 1

    if name not in homework_data[today][question_idx]["students"]:
        homework_data[today][question_idx]["students"][name] = {
            "attempts": 0,
            "correct": 0,
            "wrong": 0,
        }

    homework_data[today][question_idx]["students"][name]["attempts"] += 1
    if is_correct:
        homework_data[today][question_idx]["students"][name]["correct"] += 1
    else:
        homework_data[today][question_idx]["students"][name]["wrong"] += 1

    # Write the updated data back to the file
    with open("db/homework.json", "w") as f:
        json.dump(homework_data, f)


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

    results[current_date][name]["correct"] += st.session_state.get(
        f"{QUIZ_ID}_correct_answers", 0
    )
    results[current_date][name]["wrong"] += st.session_state.get(
        f"{QUIZ_ID}_wrong_answers", 0
    )
    results[current_date][name]["attempts"] += 1

    with open(config.RESULTS_FILE, "w") as f:
        json.dump(results, f)


def is_length_greater_than_two(lst):
    return len(lst) >= 2


def initialize_session_state(questions):
    if f"{QUIZ_ID}_initialized" not in st.session_state:
        st.session_state[f"{QUIZ_ID}_current_question"] = 0
        st.session_state[f"{QUIZ_ID}_correct_answers"] = 0
        st.session_state[f"{QUIZ_ID}_wrong_answers"] = 0
        st.session_state[f"{QUIZ_ID}_total_questions"] = len(questions)
        st.session_state[f"{QUIZ_ID}_initialized"] = True


# 메인 코드
st.title("📚 :blue[_Homework_]")

# 로그인 상태 확인
if "user" not in st.session_state:
    st.warning("먼저 로그인해주세요.")
    st.info("좌측 사이드바에서 '🔐 Login' 페이지로 이동하여 로그인하세요.")
    st.stop()

name = st.session_state["user"]["name"]
st.header(f"{name}님 :blue[화이팅!]", divider="rainbow")

# 매번 새로운 문제 로드
questions = load_questions()

# 세션 상태 초기화
initialize_session_state(questions)

current_q = st.session_state[f"{QUIZ_ID}_current_question"]
question = questions[current_q]

# 현재 문제 번호 계산 (1부터 시작)
current_question_number = current_q + 1

st.subheader(
    f"문제 {current_question_number} / {st.session_state[f'{QUIZ_ID}_total_questions']}"
)

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
    user_answer = st.multiselect(
        "답을 선택하세요:", options, key=f"answer_{QUIZ_ID}_{current_q}"
    )
else:
    user_answer = st.radio(
        "답을 선택하세요:", options, key=f"answer_{QUIZ_ID}_{current_q}"
    )

on = st.toggle("영문 선택지 확인하기")

if on:
    for i in question["choices"]["eng"]:
        st.write(f"{i} : {question['choices']['eng'][i]}")

st.divider()

# 정답 옵션 미리 정의
correct_options = [question["choices"]["kor"][ans] for ans in question["answer"]]
correct_option = question["choices"]["kor"][question["answer"][0]]


# 답변 제출 버튼
if st.button("답변 제출", type="primary"):
    if is_multiple_answer:
        is_correct = set(user_answer) == set(correct_options)
    else:
        is_correct = user_answer == correct_option

    st.session_state[f"correct_{question['idx']}"] = is_correct

    if is_correct:
        st.success("정답입니다!")
        st.session_state[f"{QUIZ_ID}_correct_answers"] += 1
        update_student_data(name, True)
    else:
        st.error("틀렸습니다.")
        st.session_state[f"{QUIZ_ID}_wrong_answers"] += 1
        update_student_data(name, False)

    # 숙제 데이터 업데이트
    try:
        update_homework_data(name, question)
    except Exception as e:
        st.error(f"숙제 데이터 업데이트 중 오류가 발생했습니다: {str(e)}")

    # 정답 표시
    if is_multiple_answer:
        st.info(f"정답: {', '.join(correct_options)}")
    else:
        st.info(f"정답: {correct_option}")


# 이전 문제 버튼
col1, col2 = st.columns(2)
with col1:
    if st.button("이전 문제", disabled=(current_q == 0)):
        st.session_state[f"{QUIZ_ID}_current_question"] = max(0, current_q - 1)
        st.rerun()

# 다음 문제 버튼
with col2:
    if st.button(
        "다음 문제",
        disabled=(current_q == st.session_state[f"{QUIZ_ID}_total_questions"] - 1),
    ):
        st.session_state[f"{QUIZ_ID}_current_question"] = min(
            st.session_state[f"{QUIZ_ID}_total_questions"] - 1, current_q + 1
        )
        st.rerun()

# 퀴즈 종료 버튼
if st.button("퀴즈 종료", type="primary"):
    save_quiz_result(name)
    st.success(
        f"퀴즈가 종료되었습니다. 총 {st.session_state[f'{QUIZ_ID}_total_questions']}문제 중 {st.session_state[f'{QUIZ_ID}_correct_answers']}문제를 맞추셨습니다."
    )
    st.balloons()
    if st.button("퀴즈 다시 시작"):
        initialize_session_state(questions)
        st.rerun()

# 퀴즈 진행 상황 표시
st.sidebar.progress(current_q / st.session_state[f"{QUIZ_ID}_total_questions"])
st.sidebar.write(
    f"{current_q + 1} / {st.session_state[f'{QUIZ_ID}_total_questions']} 문제"
)
