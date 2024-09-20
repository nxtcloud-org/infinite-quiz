import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import config
import altair as alt


# 데이터베이스 연결 함수
def get_db_connection():
    conn = sqlite3.connect("db/db.sqlite")
    conn.row_factory = sqlite3.Row
    return conn


# 날짜별 문제 풀이 현황을 가져오는 함수
def get_daily_stats(date, topic):
    conn = get_db_connection()
    query = """
    SELECT 
        u.id as user_id,
        u.name as user_name,
        u.school,
        u.team,
        COUNT(*) as total_attempts,
        SUM(CASE WHEN qr.correct = 1 THEN 1 ELSE 0 END) as correct_answers,
        SUM(CASE WHEN qr.correct = 0 THEN 1 ELSE 0 END) as incorrect_answers
    FROM question_results qr
    JOIN users u ON qr.user_id = u.id
    WHERE date(qr.created_at) = ?
    AND qr.topic = ?
    GROUP BY u.id, u.name, u.school, u.team
    """
    df = pd.read_sql_query(query, conn, params=(date, topic))
    conn.close()
    return df


# 주제별 문제 확인 현황을 가져오는 함수 (날짜 필터링 추가)
def get_topic_progress(topic, start_date=None, end_date=None):
    conn = get_db_connection()
    idx_list = ",".join(map(str, config.TOPICS[topic].get("idx_list", [])))
    query = f"""
    SELECT 
        u.id as user_id,
        u.name as user_name,
        u.school,
        u.team,
        COUNT(DISTINCT qr.question_idx) as checked_questions,
        SUM(CASE WHEN qr.correct = 1 THEN 1 ELSE 0 END) as correct_answers,
        COUNT(*) as total_attempts
    FROM question_results qr
    JOIN users u ON qr.user_id = u.id
    WHERE qr.question_idx IN ({idx_list})
    AND qr.topic = ?
    """
    params = [topic]
    if start_date and end_date:
        query += " AND date(qr.created_at) BETWEEN ? AND ?"
        params.extend([start_date, end_date])
    query += " GROUP BY u.id, u.name, u.school, u.team"
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    return df


# 시간대별 활동을 가져오는 함수 (사용자별)
def get_hourly_activity(date, topic):
    conn = get_db_connection()
    query = """
    SELECT 
        u.id as user_id,
        u.name as user_name,
        strftime('%H', qr.created_at) as hour,
        COUNT(*) as activity_count
    FROM question_results qr
    JOIN users u ON qr.user_id = u.id
    WHERE date(qr.created_at) = ?
    AND qr.topic = ?
    GROUP BY u.id, u.name, strftime('%H', qr.created_at)
    ORDER BY u.id, hour
    """
    df = pd.read_sql_query(query, conn, params=(date, topic))
    conn.close()
    return df


st.set_page_config(page_title="Homework Dashboard", page_icon="📊", layout="wide")

st.title("📊 Homework Dashboard")

# 주제 선택
topic_options = list(config.TOPICS.keys())
selected_topic = st.selectbox("주제 선택", topic_options)

# 날짜 선택 옵션
date_option = st.radio("날짜 선택 옵션", ["특정 날짜", "전체 기간"])

if date_option == "특정 날짜":
    selected_date = st.date_input("날짜 선택", datetime.now().date())
    start_date = end_date = selected_date
else:
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input(
            "시작 날짜", datetime.now().date() - timedelta(days=30)
        )
    with col2:
        end_date = st.date_input("종료 날짜", datetime.now().date())

# 일일 통계
if date_option == "특정 날짜":
    daily_stats = get_daily_stats(selected_date, selected_topic)
    st.subheader(f"{selected_date} {config.TOPICS[selected_topic]['title']} 일일 통계")
    if not daily_stats.empty:
        # 필터링 옵션
        col1, col2, col3 = st.columns(3)
        with col1:
            name_filter = st.text_input("이름으로 필터링")
        with col2:
            school_filter = st.selectbox(
                "학교로 필터링", ["All"] + list(daily_stats["school"].unique())
            )
        with col3:
            team_filter = st.selectbox(
                "팀으로 필터링", ["All"] + list(daily_stats["team"].unique())
            )

        # 필터 적용
        filtered_stats = daily_stats
        if name_filter:
            filtered_stats = filtered_stats[
                filtered_stats["user_name"].str.contains(name_filter, case=False)
            ]
        if school_filter != "All":
            filtered_stats = filtered_stats[filtered_stats["school"] == school_filter]
        if team_filter != "All":
            filtered_stats = filtered_stats[filtered_stats["team"] == team_filter]

        st.dataframe(filtered_stats)
    else:
        st.info("선택한 날짜와 주제에 대한 데이터가 없습니다.")

# 주제별 진행 상황
topic_progress = get_topic_progress(selected_topic, start_date, end_date)
st.subheader(
    f"{config.TOPICS[selected_topic]['title']} 주제 진행 상황 ({start_date} ~ {end_date})"
)
if not topic_progress.empty:
    total_questions = len(config.TOPICS[selected_topic].get("idx_list", []))
    topic_progress["progress_percentage"] = (
        topic_progress["checked_questions"] / total_questions
    ) * 100
    topic_progress["accuracy_percentage"] = (
        topic_progress["correct_answers"] / topic_progress["total_attempts"]
    ) * 100

    # 소수점 두 자리까지 반올림
    topic_progress["progress_percentage"] = topic_progress["progress_percentage"].round(
        2
    )
    topic_progress["accuracy_percentage"] = topic_progress["accuracy_percentage"].round(
        2
    )

    # 표시할 열 선택
    display_columns = [
        "user_id",
        "user_name",
        "school",
        "team",
        "checked_questions",
        "progress_percentage",
        "accuracy_percentage",
    ]
    st.dataframe(topic_progress[display_columns])

    # 사용자 선택 옵션 추가
    st.subheader("개별 사용자 진행 상황")
    all_users = topic_progress["user_name"].tolist()
    selected_users = st.multiselect("표시할 사용자 선택", all_users, default=all_users)

    # 선택된 사용자만 필터링
    filtered_progress = topic_progress[topic_progress["user_name"].isin(selected_users)]

    # st.metric을 사용한 진행 상황 표시
    cols = st.columns(3)  # 3열 레이아웃 생성
    for idx, row in filtered_progress.iterrows():
        with cols[idx % 3]:  # 3열 순환
            st.metric(
                label=f"{row['user_name']} ({row['school']}, {row['team']})",
                value=f"{row['progress_percentage']}%",
                delta=f"정확도: {row['accuracy_percentage']}%",
            )

else:
    st.info(f"{config.TOPICS[selected_topic]['title']} 주제에 대한 데이터가 없습니다.")

# 시간대별 활동 (사용자별)
if date_option == "특정 날짜":
    hourly_activity = get_hourly_activity(selected_date, selected_topic)
    st.subheader(
        f"{selected_date} {config.TOPICS[selected_topic]['title']} 시간대별 활동 (사용자별)"
    )
    if not hourly_activity.empty:
        # 사용자 선택 옵션
        users = hourly_activity["user_name"].unique()
        selected_users = st.multiselect(
            "사용자 선택", users, default=users, key="hourly_users"
        )

        # 선택된 사용자의 데이터만 필터링
        filtered_activity = hourly_activity[
            hourly_activity["user_name"].isin(selected_users)
        ]

        # Altair를 사용한 인터랙티브 차트
        chart = (
            alt.Chart(filtered_activity)
            .mark_line(point=True)
            .encode(
                x="hour:O",
                y="activity_count:Q",
                color="user_name:N",
                tooltip=["user_name", "hour", "activity_count"],
            )
            .properties(width=600, height=400)
            .interactive()
        )

        st.altair_chart(chart, use_container_width=True)
    else:
        st.info("선택한 날짜와 주제에 대한 시간대별 활동 데이터가 없습니다.")

# 사이드바에 사용자 정보 및 로그아웃 버튼 표시 (옵션)
if "user" in st.session_state:
    st.sidebar.success(f"{st.session_state['user']['name']}님 로그인됨")
    if st.sidebar.button("로그아웃"):
        del st.session_state["user"]
        st.rerun()
else:
    st.sidebar.info("로그인이 필요합니다.")
