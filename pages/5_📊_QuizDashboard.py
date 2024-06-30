import streamlit as st
import json
import pandas as pd
import os

# JSON 파일 로드
file_path = os.path.join("exam", "exam1-50.json")
with open(file_path, "r", encoding="utf-8") as file:
    quiz_data = json.load(file)

# 데이터 분석
quiz_stats = []
for quiz in quiz_data:
    quiz_id = quiz["id"]
    correct_count = quiz["correct"]
    incorrect_count = quiz["incorrect"]
    quiz_stats.append(
        {"id": quiz_id, "correct": correct_count, "incorrect": incorrect_count}
    )

df = pd.DataFrame(quiz_stats)

# 최다 정답, 최소 정답, 최다 오답, 최소 오답 문제 찾기
max_correct = df.loc[df["correct"].idxmax()]
min_correct = df.loc[df["correct"].idxmin()]
max_incorrect = df.loc[df["incorrect"].idxmax()]
min_incorrect = df.loc[df["incorrect"].idxmin()]

# Streamlit 앱
st.title("문제 분석")

# 메트릭 표시
col1, col2 = st.columns(2)
with col1:
    st.metric(
        "최다 정답 문제", f"ID: {max_correct['id']}", f"{max_correct['correct']}개"
    )
    st.metric(
        "최소 정답 문제", f"ID: {min_correct['id']}", f"{min_correct['correct']}개"
    )
with col2:
    st.metric(
        "최다 오답 문제",
        f"ID: {max_incorrect['id']}",
        f"{max_incorrect['incorrect']}개",
    )
    st.metric(
        "최소 오답 문제",
        f"ID: {min_incorrect['id']}",
        f"{min_incorrect['incorrect']}개",
    )

# 전체 퀴즈 통계 표시
st.subheader("전체 퀴즈 통계")
st.dataframe(df.set_index("id"))
