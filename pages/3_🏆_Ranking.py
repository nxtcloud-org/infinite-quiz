import streamlit as st
import json
from datetime import datetime
import pandas as pd
import config

st.set_page_config(page_title="랭킹", page_icon="🏆", layout="wide")


def load_data():
    with open(config.RESULTS_FILE, "r") as f:
        quiz_results = json.load(f)
    with open(config.STUDENTS_FILE, "r") as f:
        students = json.load(f)
    return quiz_results, students


def calculate_today_stats(results, date):
    total_attempts = 0
    participants = set()
    top_success = {"name": "", "count": 0}

    for name, data in results[date].items():
        attempts = data["success"] + data["failure"]
        total_attempts += attempts
        if attempts > 0:
            participants.add(name)
        if data["success"] > top_success["count"] and data["success"] >= 2:
            top_success = {"name": name, "count": data["success"]}

    return total_attempts, len(participants), top_success


def calculate_today_points(success, failure):
    return (success * config.CORRECT_ANSWER_POINTS) + (
        failure * config.WRONG_ANSWER_POINTS
    )


st.title("🏆 랭킹 게시판")

quiz_results, students = load_data()

# 가장 최근 날짜 찾기
latest_date = max(quiz_results.keys())

# 오늘의 기록 계산
total_attempts, total_participants, top_success = calculate_today_stats(
    quiz_results, latest_date
)

# 오늘의 기록 표시
st.header(f"📅 {latest_date} 기록", divider="rainbow")

col1, col2, col3 = st.columns(3)
col1.metric("오늘의 총 시도 횟수", total_attempts)
col2.metric("오늘의 참가 학생 수", total_participants)
if top_success["name"]:
    col3.metric(
        "오늘의 최다 성공자", f"{top_success['name']} ({top_success['count']}회)"
    )
else:
    col3.metric("오늘의 최다 성공자", "아직 없음")

# TOP 10 표시
st.header("🔝 전체 TOP 10", divider="rainbow")

user_list = [
    {
        "이름": data["name"],
        "소속": data["school"],
        "총 시도 횟수": data["attempts"],
        "포인트": data["point"],
    }
    for name, data in students.items()
]

df = pd.DataFrame(user_list)
if not df.empty:
    df_sorted = df.sort_values("포인트", ascending=False).head(10)
    st.table(df_sorted)
else:
    st.info("등록된 학생이 아직 없습니다.")

# 오늘의 TOP 10 표시
st.header(f"🔝 {latest_date} TOP 10", divider="rainbow")

today_user_list = [
    {
        "이름": name,
        "소속": students[name]["school"],
        "오늘의 시도 횟수": data["success"] + data["failure"],
        "오늘의 포인트": calculate_today_points(data["success"], data["failure"]),
    }
    for name, data in quiz_results[latest_date].items()
]

today_df = pd.DataFrame(today_user_list)
if not today_df.empty:
    today_df_sorted = today_df.sort_values("오늘의 포인트", ascending=False).head(10)
    st.table(today_df_sorted)
else:
    st.info("오늘 참가한 학생이 아직 없습니다.")
