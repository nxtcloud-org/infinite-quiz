import streamlit as st
import config
import json
from datetime import datetime
import pandas as pd

st.set_page_config(page_title="관리자 통계", page_icon="📊", layout="wide")


def check_password():
    """Returns `True` if the user had the correct password."""

    def password_entered():
        """Checks whether a password entered by the user is correct."""
        if st.session_state["password"] == config.ADMIN_PASSWORD:
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # don't store password
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        # First run, show input for password.
        st.text_input(
            "관리자 비밀번호를 입력하세요",
            type="password",
            on_change=password_entered,
            key="password",
        )
        return False
    elif not st.session_state["password_correct"]:
        # Password incorrect, show input + error.
        st.text_input(
            "관리자 비밀번호를 입력하세요",
            type="password",
            on_change=password_entered,
            key="password",
        )
        st.error("😕 비밀번호가 올바르지 않습니다.")
        return False
    else:
        # Password correct.
        return True


def load_users():
    with open(config.STUDENTS_FILE, "r") as f:
        return json.load(f)


def load_quiz_results():
    with open(config.RESULTS_FILE, "r") as f:
        return json.load(f)


def calculate_points(success, failure):
    return (success * config.CORRECT_ANSWER_POINTS) + (
        failure * config.INCORRECT_ANSWER_POINTS
    )


if check_password():
    st.title(":blue[_관리자 통계_] 📊")

    users = load_users()
    quiz_results = load_quiz_results()

    st.header("🔍 데이터 필터", divider="rainbow")

    col1, col2 = st.columns(2)
    with col1:
        # 날짜 선택
        dates = list(quiz_results.keys())
        dates.sort(reverse=True)
        selected_date = st.selectbox("📅 날짜 선택", ["전체"] + dates)

    with col2:
        # 학교 선택
        schools = list(set(user["school"] for user in users.values()))
        selected_school = st.selectbox("🏫 학교 선택", ["전체"] + schools)

    st.header("📊 통계 결과", divider="rainbow")

    # 데이터 필터링 및 표 생성
    if selected_date == "전체":
        # 전체 통계
        filtered_data = []
        for name, user_data in users.items():
            if selected_school == "전체" or user_data["school"] == selected_school:
                filtered_data.append(
                    {
                        "이름": name,
                        "학교": user_data["school"],
                        "총 시도 횟수": user_data["attempts"],
                        "성공 횟수": user_data["success"],
                        "실패 횟수": user_data["failure"],
                        "포인트": user_data["point"],
                    }
                )
    else:
        # 날짜별 통계
        filtered_data = []
        for name, result in quiz_results[selected_date].items():
            user = users.get(name)
            if user and (
                selected_school == "전체" or user["school"] == selected_school
            ):
                filtered_data.append(
                    {
                        "이름": name,
                        "학교": user["school"],
                        "시도 횟수": result["success"] + result["failure"],
                        "성공 횟수": result["success"],
                        "실패 횟수": result["failure"],
                    }
                )

    df = pd.DataFrame(filtered_data)

    if not df.empty:
        st.subheader(
            f"{'🗓 전체 기간' if selected_date == '전체' else f'📅 {selected_date}'} 통계"
        )
        st.dataframe(df)

        st.subheader("📈 요약 통계", divider="gray")
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("👥 총 참가자 수", len(df))
        col2.metric(
            "🔄 총 시도 횟수",
            df["총 시도 횟수" if selected_date == "전체" else "시도 횟수"].sum(),
        )
        col3.metric("✅ 총 성공 횟수", df["성공 횟수"].sum())
        # col4.metric("⭐ 평균 포인트", f"{df['포인트'].mean():.2f}")
        # 당일 점수만 찾아오는 로직이 안됨, 왜냐하면 계정 정보에 바로 점수를 올려놓기 때문, 퀴즈 풀때마다 성공 실패외에 맞춤 틀림 count를 잡아서 데일리로 저장되어야지 가능
    else:
        st.info("선택한 조건에 해당하는 데이터가 없습니다.")

    st.divider()

    if st.button("🚪 로그아웃"):
        st.session_state["password_correct"] = False
        st.experimental_rerun()
