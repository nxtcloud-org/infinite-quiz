import streamlit as st
import sqlite3
import pandas as pd
import config
from datetime import datetime, timedelta


# 데이터베이스 연결 함수
def get_db_connection():
    conn = sqlite3.connect("db/db.sqlite")
    conn.row_factory = sqlite3.Row
    return conn


# 주제별 문제 풀이 현황을 가져오는 함수 (날짜 필터링 추가)
def get_problem_attempts(topic, start_date=None, end_date=None):
    conn = get_db_connection()
    query = """
    SELECT 
        qr.question_idx,
        u.id as user_id,
        u.name as user_name,
        COUNT(*) as attempt_count,
        SUM(CASE WHEN qr.correct = 1 THEN 1 ELSE 0 END) as correct_count,
        MIN(qr.created_at) as first_attempt,
        MAX(qr.created_at) as last_attempt
    FROM question_results qr
    JOIN users u ON qr.user_id = u.id
    WHERE qr.topic = ?
    """
    params = [topic]
    if start_date and end_date:
        query += " AND DATE(qr.created_at) BETWEEN ? AND ?"
        params.extend([start_date, end_date])
    query += " GROUP BY qr.question_idx, u.id, u.name ORDER BY qr.question_idx, attempt_count DESC"
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()

    df["first_attempt"] = pd.to_datetime(df["first_attempt"])
    df["last_attempt"] = pd.to_datetime(df["last_attempt"])

    return df


# 사용자별 시도 횟수를 3열로 표시하는 함수
def display_user_attempts(user_data):
    cols = st.columns(3)
    for idx, row in enumerate(user_data.iterrows()):
        _, row = row
        user_accuracy = (row["correct_count"] / row["attempt_count"]) * 100
        with cols[idx % 3]:
            st.metric(
                label=f"{row['user_name']} (ID: {row['user_id']})",
                value=f"시도: {row['attempt_count']}회",
                delta=f"정답률: {user_accuracy:.2f}%",
            )

    remaining_cols = 3 - (len(user_data) % 3)
    if remaining_cols < 3:
        for _ in range(remaining_cols):
            with cols[2 - remaining_cols]:
                st.write("")


# 사용자 목록을 가져오는 함수
def get_user_list(problem_attempts):
    user_list = problem_attempts[["user_id", "user_name"]].drop_duplicates()
    return user_list.sort_values("user_name")


# 모든 문제에 대해 특정 횟수 이상 시도한 사용자 목록을 가져오는 함수
def get_frequent_users(problem_attempts, min_attempts):
    user_problem_attempts = (
        problem_attempts.groupby(["user_id", "question_idx"])
        .agg({"user_name": "first", "attempt_count": "sum"})
        .reset_index()
    )

    all_problems = problem_attempts["question_idx"].unique()
    frequent_users = user_problem_attempts.groupby("user_id").filter(
        lambda x: all(x["attempt_count"] >= min_attempts)
        and len(x) == len(all_problems)
    )

    result = frequent_users.groupby("user_id").agg({"user_name": "first"}).reset_index()

    return result.sort_values("user_name")


@st.experimental_fragment
def date_filter_section():
    date_filter = st.radio("날짜 필터 옵션", ["전체 기간", "특정 날짜", "기간 지정"])

    if date_filter == "전체 기간":
        start_date, end_date = None, None
    elif date_filter == "특정 날짜":
        selected_date = st.date_input("날짜 선택", datetime.now().date())
        start_date = end_date = selected_date
    else:  # 기간 지정
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input(
                "시작 날짜", datetime.now().date() - timedelta(days=30)
            )
        with col2:
            end_date = st.date_input("종료 날짜", datetime.now().date())

    return start_date, end_date


@st.experimental_fragment
def display_problem_details(idx, problem_data):
    total_attempts = problem_data["attempt_count"].sum()
    total_correct = problem_data["correct_count"].sum()
    accuracy = (total_correct / total_attempts) * 100 if total_attempts > 0 else 0

    st.write(f"**문제 IDX {idx}**")
    col1, col2, col3 = st.columns(3)
    col1.metric("총 시도 횟수", total_attempts)
    col2.metric("총 정답 횟수", total_correct)
    col3.metric("정답률", f"{accuracy:.2f}%")

    user_data = problem_data.sort_values("attempt_count", ascending=False)
    display_user_attempts(user_data)


@st.experimental_fragment
def display_frequent_users(problem_attempts, min_attempts):
    frequent_users = get_frequent_users(problem_attempts, min_attempts)

    if not frequent_users.empty:
        st.write(f"모든 문제를 각각 {min_attempts}회 이상 시도한 사용자 목록:")
        cols = st.columns(3)
        for idx, (_, user) in enumerate(frequent_users.iterrows()):
            with cols[idx % 3]:
                st.write(f"{user['user_name']} (ID: {user['user_id']})")
    else:
        st.write(f"모든 문제를 각각 {min_attempts}회 이상 시도한 사용자가 없습니다.")


st.set_page_config(
    page_title="Comprehensive Problem Dashboard", page_icon="📊", layout="wide"
)

st.title("📊 Comprehensive Problem Dashboard")

# 주제 선택
topic_options = list(config.TOPICS.keys())
selected_topic = st.selectbox("주제 선택", topic_options)

if selected_topic:
    # 날짜 필터링 옵션
    st.subheader("날짜 필터링", divider="rainbow")
    start_date, end_date = date_filter_section()

    problem_attempts = get_problem_attempts(selected_topic, start_date, end_date)

    st.subheader(
        f"{config.TOPICS[selected_topic]['title']} 문제별 풀이 현황", divider="rainbow"
    )

    if not problem_attempts.empty:
        # 날짜 범위 표시
        if start_date and end_date:
            st.write(f"데이터 기간: {start_date} ~ {end_date}")
        else:
            first_attempt = problem_attempts["first_attempt"].min()
            last_attempt = problem_attempts["last_attempt"].max()
            st.write(
                f"데이터 기간: 전체 (첫 시도: {first_attempt.strftime('%Y-%m-%d')}, 마지막 시도: {last_attempt.strftime('%Y-%m-%d')})"
            )

        # 문제 idx 선택 (전체 옵션 추가)
        question_idx_list = ["전체"] + sorted(
            problem_attempts["question_idx"].unique().tolist()
        )
        selected_idx = st.selectbox("문제 IDX 선택", question_idx_list)

        if selected_idx == "전체":
            st.divider()
            st.subheader("전체 문제 요약", divider="rainbow")

            # 전체 문제에 대한 요약 정보
            total_attempts = problem_attempts["attempt_count"].sum()
            total_correct = problem_attempts["correct_count"].sum()
            accuracy = (
                (total_correct / total_attempts) * 100 if total_attempts > 0 else 0
            )
            unique_problems = problem_attempts["question_idx"].nunique()
            unique_users = problem_attempts["user_id"].nunique()

            col1, col2, col3, col4, col5 = st.columns(5)
            col1.metric("총 문제 수", unique_problems)
            col2.metric("총 사용자 수", unique_users)
            col3.metric("총 시도 횟수", total_attempts)
            col4.metric("총 정답 횟수", total_correct)
            col5.metric("전체 정답률", f"{accuracy:.2f}%")

            # 사용자 명단 표시
            st.divider()
            st.subheader("참여 사용자 명단", divider="rainbow")
            user_list = get_user_list(problem_attempts)

            cols = st.columns(3)
            for idx, (_, user) in enumerate(user_list.iterrows()):
                with cols[idx % 3]:
                    st.write(f"{user['user_name']} (ID: {user['user_id']})")

            # 모든 문제에 대해 특정 횟수 이상 시도한 사용자 명단
            st.divider()
            st.subheader("모든 문제를 자주 시도한 사용자 명단", divider="rainbow")
            min_attempts = st.number_input(
                "각 문제당 최소 시도 횟수", min_value=1, value=3, step=1
            )
            display_frequent_users(problem_attempts, min_attempts)

            # 문제별 요약 및 사용자별 상세 정보
            st.divider()
            st.subheader("문제별 상세 정보", divider="rainbow")
            for idx in sorted(problem_attempts["question_idx"].unique()):
                problem_data = problem_attempts[problem_attempts["question_idx"] == idx]
                display_problem_details(idx, problem_data)
                st.write("---")

        else:
            # 선택된 문제의 데이터 필터링
            filtered_data = problem_attempts[
                problem_attempts["question_idx"] == selected_idx
            ]
            display_problem_details(selected_idx, filtered_data)

            # 전체 데이터 표시
            st.subheader("상세 데이터")
            st.dataframe(filtered_data)

    else:
        st.info(
            f"{config.TOPICS[selected_topic]['title']} 주제에 대한 선택한 기간의 풀이 데이터가 없습니다."
        )

# 사이드바에 사용자 정보 및 로그아웃 버튼 표시 (옵션)
if "user" in st.session_state:
    st.sidebar.success(f"{st.session_state['user']['name']}님 로그인됨")
    if st.sidebar.button("로그아웃"):
        del st.session_state["user"]
        st.rerun()
else:
    st.sidebar.info("로그인이 필요합니다.")
