import streamlit as st
import random
import config
import json
from datetime import datetime

st.set_page_config(page_title="퀴즈", page_icon="🧠", layout="wide")


# 사용자 데이터 로드 함수
def load_users():
    with open(config.STUDENTS_FILE, "r") as f:
        return json.load(f)


# 사용자 데이터 저장 함수
def save_users(users):
    with open(config.STUDENTS_FILE, "w") as f:
        json.dump(users, f)


def update_student_data(name, is_correct, quiz_completed=False):
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

        if quiz_completed:
            students[name]["success"] += 1
            students[name]["point"] += config.QUIZ_SUCCESS_BONUS
        elif st.session_state["quiz_ended"]:
            students[name]["failure"] += 1

        # attempts를 success와 failure의 합으로 업데이트
        students[name]["attempts"] = (
            students[name]["success"] + students[name]["failure"]
        )

    save_users(students)


def save_quiz_result(name, success):
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
            "success": 0,
            "failure": 0,
            "attempts": 0,
        }

    results[current_date][name]["correct"] += st.session_state["correct_answers"]
    results[current_date][name]["wrong"] += (
        config.QUIZ_SIZE - st.session_state["correct_answers"]
    )

    if success:
        results[current_date][name]["success"] += 1
    else:
        results[current_date][name]["failure"] += 1

    # attempts를 success와 failure의 합으로 업데이트
    results[current_date][name]["attempts"] = (
        results[current_date][name]["success"] + results[current_date][name]["failure"]
    )

    with open(config.RESULTS_FILE, "w") as f:
        json.dump(results, f)


# 세션 상태 초기화 함수
def initialize_session_state():
    st.session_state["quiz_questions"] = random.sample(
        st.session_state["questions"], config.QUIZ_SIZE
    )
    st.session_state["current_question"] = 0
    st.session_state["correct_answers"] = 0
    st.session_state["quiz_ended"] = False
    st.session_state["quiz_success"] = False
    st.session_state["user_answer"] = None
    st.session_state["show_result"] = False


# 로그인 상태 확인
if "user" not in st.session_state:
    st.warning("먼저 로그인해주세요.")
    st.info("좌측 사이드바에서 '🔐 Login' 페이지로 이동하여 로그인하세요.")
    st.stop()

# 퀴즈 시작 또는 재시작 시 세션 상태 초기화
if "quiz_questions" not in st.session_state or st.session_state.get(
    "restart_quiz", False
):
    initialize_session_state()
    st.session_state["restart_quiz"] = False

st.title(":blue[_Quiz_] 🎯")

name = st.session_state["user"]["name"]
st.header(f"{name}님 :blue[화이팅!]", divider="rainbow")

# 퀴즈가 끝나지 않았고 아직 풀지 않은 문제가 있을 때만 질문을 표시
if (
    not st.session_state["quiz_ended"]
    and st.session_state["current_question"] < config.QUIZ_SIZE
):
    question = st.session_state["quiz_questions"][st.session_state["current_question"]]

    # 질문 표시
    st.subheader(f"문제 {st.session_state['current_question'] + 1}")

    st.divider()
    st.write(question["question"])
    st.divider()

    options = list(question["options"].values())

    # 복수 정답 여부 확인
    is_multiple_answer = isinstance(question["answer"], list)

    if is_multiple_answer:
        st.write(
            ":orange[복수 정답] 문제입니다. 해당하는 :orange[모든 답을 선택]하세요."
        )
        st.write("긴 문제는 선택지에 :orange[마우스를 올려두면] 보입니다.")
        user_answer = st.multiselect("답을 선택하세요:", options)
    else:
        user_answer = st.radio("답을 선택하세요:", options)

    st.divider()
    # 다음 버튼
    if st.button("다음", type="primary"):
        st.session_state["user_answer"] = user_answer

        if is_multiple_answer:
            correct_options = [question["options"][ans] for ans in question["answer"]]
            is_correct = set(user_answer) == set(correct_options)
        else:
            correct_option = question["options"][question["answer"]]
            is_correct = user_answer == correct_option

        if is_correct:
            st.session_state["correct_answers"] += 1
            st.session_state["current_question"] += 1
            update_student_data(name, True)

            if st.session_state["current_question"] == config.QUIZ_SIZE:
                st.session_state["quiz_ended"] = True
                st.session_state["quiz_success"] = True
                update_student_data(name, True, quiz_completed=True)
                save_quiz_result(name, True)
        else:
            st.session_state["quiz_ended"] = True
            st.session_state["quiz_success"] = False
            update_student_data(name, False)
            save_quiz_result(name, False)

        st.experimental_rerun()

# 퀴즈가 끝났을 때 결과 표시
if st.session_state["quiz_ended"]:
    if st.session_state.get("quiz_success", False):
        st.success(f"축하합니다! {config.QUIZ_SIZE}문제를 모두 맞추셨습니다.")
        st.subheader(
            f"총 {config.QUIZ_SIZE}문제를 :green[_연속으로 모두_] 맞추셨습니다!!"
        )
        st.balloons()
    else:
        question = st.session_state["quiz_questions"][
            st.session_state["current_question"]
        ]
        if isinstance(question["answer"], list):
            correct_options = [question["options"][ans] for ans in question["answer"]]
            st.error(f"오답입니다. 정답은 {', '.join(correct_options)}입니다.")
        else:
            correct_option = question["options"][question["answer"]]
            st.error(f"오답입니다. 정답은 {correct_option}입니다.")
        st.warning(
            f"{config.QUIZ_SIZE}문제 중 {st.session_state['correct_answers']}문제를 맞추셨습니다."
        )
        st.info(
            "아쉽지만 다음에 다시 도전해보세요! 계속 노력하면 반드시 성공할 수 있습니다."
        )

    if st.button("퀴즈 다시 시작하기", type="primary"):
        st.session_state["restart_quiz"] = True
        st.experimental_rerun()

# 퀴즈 진행 상황 표시
st.sidebar.progress(st.session_state["current_question"] / config.QUIZ_SIZE)
st.sidebar.write(
    f"{st.session_state['current_question']} / {config.QUIZ_SIZE} 문제 완료"
)
