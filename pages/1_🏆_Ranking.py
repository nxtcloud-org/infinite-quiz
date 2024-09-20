import streamlit as st
import sqlite3
import pandas as pd


# 데이터베이스 연결 함수
def get_db_connection():
    conn = sqlite3.connect("db/db.sqlite")
    conn.row_factory = sqlite3.Row
    return conn


# 전체 랭킹 데이터를 가져오는 함수
def get_overall_ranking():
    conn = get_db_connection()
    query = """
    SELECT id, name, school, team, points, correct, incorrect
    FROM users
    ORDER BY points DESC
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    df["rank"] = df["points"].rank(method="min", ascending=False)
    return df


# 소속별 랭킹 데이터를 가져오는 함수
def get_school_ranking():
    conn = get_db_connection()
    query = """
    SELECT school, SUM(points) as total_points, COUNT(*) as member_count
    FROM users
    GROUP BY school
    ORDER BY total_points DESC
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    df["rank"] = df["total_points"].rank(method="min", ascending=False)
    return df


# 팀별 랭킹 데이터를 가져오는 함수
def get_team_ranking():
    conn = get_db_connection()
    query = """
    SELECT team, SUM(points) as total_points, COUNT(*) as member_count
    FROM users
    GROUP BY team
    ORDER BY total_points DESC
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    df["average_points"] = df["total_points"] / df["member_count"]
    df["rank"] = df["total_points"].rank(method="min", ascending=False)
    df["average_rank"] = df["average_points"].rank(method="min", ascending=False)
    return df


st.set_page_config(page_title="User Ranking", page_icon="🏆", layout="wide")

st.title("🏆 User Ranking")

# 랭킹 타입 선택
ranking_type = st.radio("랭킹 유형", ["전체 랭킹", "소속별 랭킹", "팀별 랭킹"])

if ranking_type == "전체 랭킹":
    ranking_data = get_overall_ranking()
    st.subheader("전체 사용자 랭킹")

    # Top 3 표시
    st.subheader("🥇 Top 3 🥈 🥉")
    top_3 = ranking_data.head(3)
    columns = st.columns(3)

    for i in range(min(3, len(top_3))):
        with columns[i]:
            if i < len(top_3):
                user = top_3.iloc[i]
                total_attempts = user["correct"] + user["incorrect"]
                accuracy = (
                    (user["correct"] / total_attempts * 100)
                    if total_attempts > 0
                    else 0
                )
                st.metric(
                    label=f"{i+1}등: {user['name']}",
                    value=f"{user['points']}점",
                    delta=f"정답률: {accuracy:.2f}%",
                )
            else:
                st.metric(label=f"{i+1}등", value="데이터 없음")

    # 필터링 옵션
    col1, col2 = st.columns(2)
    with col1:
        school_filter = st.selectbox(
            "소속 필터", ["전체"] + list(ranking_data["school"].unique())
        )
    with col2:
        team_filter = st.selectbox(
            "팀 필터", ["전체"] + list(ranking_data["team"].unique())
        )

    # 필터 적용
    if school_filter != "전체":
        ranking_data = ranking_data[ranking_data["school"] == school_filter]
    if team_filter != "전체":
        ranking_data = ranking_data[ranking_data["team"] == team_filter]

    # 랭킹 표시
    st.dataframe(
        ranking_data[
            ["rank", "name", "school", "team", "points", "correct", "incorrect"]
        ]
    )

elif ranking_type == "소속별 랭킹":
    school_ranking = get_school_ranking()
    st.subheader("소속별 랭킹")

    # Top 3 소속 표시
    st.subheader("🥇 Top 3 Groups 🥈 🥉")
    top_3_schools = school_ranking.head(3)
    columns = st.columns(3)

    for i in range(min(3, len(top_3_schools))):
        with columns[i]:
            if i < len(top_3_schools):
                school = top_3_schools.iloc[i]
                st.metric(
                    label=f"{i+1}등: {school['school']}",
                    value=f"{school['total_points']}점",
                    delta=f"구성원: {school['member_count']}명",
                )
            else:
                st.metric(label=f"{i+1}등", value="데이터 없음")

    # 소속별 랭킹 표시
    st.dataframe(school_ranking)

else:  # 팀별 랭킹
    team_ranking = get_team_ranking()
    st.subheader("팀별 랭킹")

    # 랭킹 기준 선택
    ranking_criterion = st.radio("랭킹 기준", ["총점", "평균 점수"])

    if ranking_criterion == "총점":
        team_ranking = team_ranking.sort_values("total_points", ascending=False)
        rank_column = "rank"
        value_column = "total_points"
    else:
        team_ranking = team_ranking.sort_values("average_points", ascending=False)
        rank_column = "average_rank"
        value_column = "average_points"

    # Top 3 팀 표시
    st.subheader("🥇 Top 3 Teams 🥈 🥉")
    top_3_teams = team_ranking.head(3)
    columns = st.columns(3)

    for i in range(min(3, len(top_3_teams))):
        with columns[i]:
            if i < len(top_3_teams):
                team = top_3_teams.iloc[i]
                st.metric(
                    label=f"{i+1}등: {team['team']}",
                    value=f"{team[value_column]:.2f}점",
                    delta=f"구성원: {team['member_count']}명",
                )
            else:
                st.metric(label=f"{i+1}등", value="데이터 없음")

    # 팀별 랭킹 표시
    st.dataframe(
        team_ranking[
            [rank_column, "team", "total_points", "average_points", "member_count"]
        ]
    )


# 사이드바에 사용자 정보 및 로그아웃 버튼 표시 (옵션)
if "user" in st.session_state:
    st.sidebar.success(f"{st.session_state['user']['name']}님 로그인됨")
    if st.sidebar.button("로그아웃"):
        del st.session_state["user"]
        st.rerun()
else:
    st.sidebar.info("로그인이 필요합니다.")
