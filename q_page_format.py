import streamlit as st
import sqlite3
from utils.helpers import load_homework_questions
from datetime import datetime
import config


def get_db_connection():
    conn = sqlite3.connect("db/db.sqlite")
    conn.row_factory = sqlite3.Row
    return conn


def save_question_result(user_id, quiz_idx, is_correct, quiz_topic):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
        INSERT INTO question_results (user_id, question_idx, topic, correct, created_at)
        VALUES (?, ?, ?, ?, ?)
        """,
            (user_id, quiz_idx, quiz_topic, is_correct, datetime.now()),
        )

        points_to_add = 3 if is_correct else 1
        cursor.execute(
            """
        UPDATE users
        SET points = points + ?,
            correct = correct + ?,
            incorrect = incorrect + ?
        WHERE id = ?
        """,
            (points_to_add, 1 if is_correct else 0, 0 if is_correct else 1, user_id),
        )

        conn.commit()
    except sqlite3.Error as e:
        st.error(f"데이터베이스 오류: {e}")
    finally:
        conn.close()


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


@st.experimental_fragment
def display_question(question, current_q, topic):
    st.subheader(
        f"문제 {current_q + 1} / {st.session_state[f'{topic}_total_questions']}"
    )

    tab1, tab2 = st.tabs(["한국어", "English"])

    with tab1:
        st.write(f"문제 idx : {question['idx']}")
        st.write(question["question"]["kor"])

    with tab2:
        st.write(f"문제 idx : {question['idx']}")
        st.write(question["question"]["eng"])

    options = list(question["choices"]["kor"].values())
    if is_multiple_answer(question):
        st.write(
            ":orange[복수 정답] 문제입니다. 해당하는 :orange[모든 답을 선택]하세요."
        )
        user_answer = st.multiselect(
            "답을 선택하세요:", options, key=f"{topic}_q_{current_q}"
        )
    else:
        user_answer = st.radio(
            "답을 선택하세요:", options, key=f"{topic}_q_{current_q}"
        )

    show_english = st.toggle("영문 선택지 확인하기")
    if show_english:
        st.write("영문 선택지:")
        for key, value in question["choices"]["eng"].items():
            st.write(f"{key}: {value}")

    return user_answer


@st.experimental_fragment
def display_result(question, user_answer, is_correct):
    if is_correct:
        st.success("정답입니다!")
    else:
        st.error("틀렸습니다.")
        if is_multiple_answer(question):
            st.error(f'당신의 오답: {", ".join(user_answer)}')
            st.success(
                f'정답: {", ".join([question["choices"]["kor"][ans] for ans in question["answer"]])}'
            )
        else:
            st.error(f"당신의 오답: {user_answer}")
            st.success(f'정답: {question["choices"]["kor"][question["answer"][0]]}')


def display_progress(current_q, total_questions):
    progress = (current_q + 1) / total_questions
    question_count = f"{current_q + 1} / {total_questions} 문제"
    return progress, question_count


def render_question_page(topic):
    st.set_page_config(
        page_title=f"{topic.upper()} Homework", page_icon="👟", layout="wide"
    )

    st.title(f"👟 {topic.upper()} Homework")

    if "user" not in st.session_state:
        st.warning("먼저 로그인해주세요.")
        st.info("좌측 사이드바에서 '🔐 Login' 페이지로 이동하여 로그인하세요.")
        st.stop()

    user = st.session_state["user"]
    user_id = user["id"]
    username = user["name"]

    topic_config = config.TOPICS[topic]

    if f"{topic}_questions" not in st.session_state:
        st.session_state[f"{topic}_questions"] = load_homework_questions(
            topic_config["file"]
        )

    questions = st.session_state[f"{topic}_questions"]

    initialize_session_state(questions, topic)

    st.header(f"{username}님의 {topic_config['title']} 숙제", divider="rainbow")

    current_q = st.session_state[f"{topic}_current_question"]
    question = questions[current_q]
    quiz_idx = question["idx"]

    user_answer = display_question(question, current_q, topic)

    if st.button("제출", type="primary"):
        with st.spinner("결과 확인 중..."):
            st.session_state[f"{topic}_user_answer"] = user_answer
            if is_multiple_answer(question):
                correct_options = [
                    question["choices"]["kor"][ans] for ans in question["answer"]
                ]
                is_correct = set(user_answer) == set(correct_options)
            else:
                correct_option = question["choices"]["kor"][question["answer"][0]]
                is_correct = user_answer == correct_option

            st.session_state[f"{topic}_answers"][current_q] = is_correct
            st.session_state[f"{topic}_show_result"] = True

            save_question_result(user_id, quiz_idx, is_correct, topic)

    if st.session_state[f"{topic}_show_result"]:
        display_result(
            question, user_answer, st.session_state[f"{topic}_answers"][current_q]
        )

    col1, col2 = st.columns(2)
    with col1:
        if st.button("이전 문제", disabled=(current_q == 0)):
            st.session_state[f"{topic}_current_question"] = max(0, current_q - 1)
            st.session_state[f"{topic}_show_result"] = False
            st.rerun()

    with col2:
        if st.button(
            "다음 문제",
            disabled=(current_q == st.session_state[f"{topic}_total_questions"] - 1),
        ):
            st.session_state[f"{topic}_current_question"] = min(
                st.session_state[f"{topic}_total_questions"] - 1, current_q + 1
            )
            st.session_state[f"{topic}_show_result"] = False
            st.rerun()

    progress, question_count = display_progress(
        current_q, st.session_state[f"{topic}_total_questions"]
    )
    with st.sidebar:
        st.progress(progress)
        st.write(question_count)

    if st.sidebar.button("다시 시작"):
        st.session_state[f"{topic}_current_question"] = 0
        st.session_state[f"{topic}_answers"] = {}
        st.session_state[f"{topic}_show_result"] = False
        st.rerun()

    if "user" in st.session_state:
        st.sidebar.success(f"{st.session_state['user']['name']}님 로그인됨")
        if st.sidebar.button("로그아웃", key=f"logout_button_{topic}"):
            del st.session_state["user"]
            st.rerun()
    else:
        st.sidebar.info("로그인이 필요합니다.")
