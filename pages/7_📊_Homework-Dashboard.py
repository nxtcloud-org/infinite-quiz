import streamlit as st
import pandas as pd
from datetime import datetime
import config
import requests

# Lambda 함수 URL
HOMEWORK_CHECK_LAMBDA_URL = config.HOMEWORK_CHECK_LAMBDA_URL


def invoke_lambda(operation, payload):
    try:
        response = requests.post(
            HOMEWORK_CHECK_LAMBDA_URL, json={"operation": operation, "payload": payload}
        )
        return response.json()
    except Exception as e:
        st.error(f"Error calling Lambda function: {str(e)}")
        return None


def authenticate():
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False

    if not st.session_state.authenticated:
        password = st.text_input("관리자 비밀번호를 입력하세요", type="password")
        if st.button("인증"):
            if password == config.ADMIN_PASSWORD:
                st.session_state.authenticated = True
                st.success("인증되었습니다.")
                st.rerun()
            else:
                st.error("비밀번호가 올바르지 않습니다.")
    return st.session_state.authenticated


def main():
    st.title("숙제 확인")

    if not authenticate():
        return

    # 날짜 선택
    selected_date = st.date_input("날짜 선택", datetime.now())

    # 숙제 영역 선택
    quiz_topics = ["s3_cloudfront", "ai", "iam", "classic"]  # 예시 토픽들
    selected_topic = st.selectbox("숙제 영역 선택", quiz_topics)

    # 학생/문제 기준 선택
    view_basis = st.radio("보기 기준", ["학생", "문제"])

    if st.button("불러오기"):
        data = invoke_lambda(
            "get_homework_results",
            {
                "date": selected_date.strftime("%Y-%m-%d"),
                "quiz_topic": selected_topic,
                "view_basis": view_basis,
            },
        )

        if data:
            if view_basis == "학생":
                display_student_view(data, selected_topic)
            else:
                display_question_view(data)


def display_student_view(data, topic):
    st.subheader("학생별 결과")

    # 각 토픽별 총 문제 수 설정
    topic_question_counts = {"s3_cloudfront": 119, "ai": 9, "iam": 56, "classic": 219}

    total_questions = topic_question_counts.get(topic, 0)

    df = pd.DataFrame(data)

    if df.empty:
        st.warning("선택한 영역에 대한 데이터가 없습니다.")
        return

    # total_questions 값을 df의 길이만큼 확장
    df["total_questions"] = total_questions

    # 정답률 계산
    df["정답률"] = df["correct"] / df["total_questions"] * 100

    st.table(
        df[
            [
                "user_name",
                "correct",
                "incorrect",
                "correct_questions",
                "incorrect_questions",
                "정답률",
            ]
        ]
    )


def display_question_view(data):
    st.subheader("문제별 결과")

    df = pd.DataFrame(data)
    df["정답률"] = (
        df["correct_count"] / (df["correct_count"] + df["incorrect_count"]) * 100
    )

    st.table(
        df[
            [
                "quiz_idx",
                "correct_count",
                "incorrect_count",
                "correct_students",
                "incorrect_students",
                "정답률",
            ]
        ]
    )


if __name__ == "__main__":
    main()
