import streamlit as st
import json
from datetime import datetime, timedelta
import os
from collections import defaultdict
import config

st.set_page_config(page_title="숙제 검사", page_icon="📚", layout="wide")


# homework.json 파일 내용을 날짜별로 필터링하여 보여주는 함수
def display_filtered_homework():
    try:
        with open("db/homework.json", "r") as f:
            homework_json = json.load(f)

        # 날짜 목록 추출 (최신 날짜부터 정렬)
        dates = sorted(homework_json.keys(), reverse=True)

        # 날짜 선택기
        selected_date = st.selectbox("날짜 선택", dates)

        # 불러오기 버튼
        if st.button("homework.json 불러오기"):
            if selected_date in homework_json:
                st.subheader(f"{selected_date} 숙제 데이터")
                st.json(homework_json[selected_date])
            else:
                st.warning("선택한 날짜에 해당하는 데이터가 없습니다.")

    except FileNotFoundError:
        st.error("db/homework.json 파일을 찾을 수 없습니다.")
    except json.JSONDecodeError:
        st.error("db/homework.json 파일이 올바른 JSON 형식이 아닙니다.")


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


def load_homework_data():
    try:
        with open("db/homework.json", "r") as f:
            data = f.read()
            if not data:  # 파일이 비어있는 경우
                return {}
            return json.loads(data)
    except FileNotFoundError:
        return {}
    except json.JSONDecodeError:
        st.error(
            "homework.json 파일이 올바른 JSON 형식이 아닙니다. 파일을 확인해 주세요."
        )
        return {}


def get_date_range():
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=7)  # 최근 7일간의 데이터를 보여줍니다
    date_range = [
        end_date - timedelta(days=x) for x in range((end_date - start_date).days + 1)
    ]
    return date_range  # 최근 날짜부터 과거 순으로 정렬된 리스트를 반환합니다


def reorganize_data(homework_data, selected_date_str):
    student_data = defaultdict(
        lambda: {
            "total_attempts": 0,
            "total_correct": 0,
            "total_wrong": 0,
            "problems": {},
            "problem_count": 0,
        }
    )

    for q_idx, q_data in homework_data[selected_date_str].items():
        for student, stats in q_data["students"].items():
            student_data[student]["total_attempts"] += stats["attempts"]
            student_data[student]["total_correct"] += stats["correct"]
            student_data[student]["total_wrong"] += stats["wrong"]
            student_data[student]["problems"][q_idx] = stats
            student_data[student]["problem_count"] += 1

    return student_data


def display_student_stats(student, stats):
    with st.expander(f"학생: {student}"):
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("푼 문제 수", stats["problem_count"])
        col2.metric("총 시도 횟수", stats["total_attempts"])
        col3.metric("총 정답 횟수", stats["total_correct"])
        col4.metric("총 오답 횟수", stats["total_wrong"])

        st.subheader("문제별 통계")
        problem_data = []
        for q_idx, prob_stats in stats["problems"].items():
            problem_data.append(
                {
                    "문제 번호": q_idx,
                    "시도 횟수": prob_stats["attempts"],
                    "정답 횟수": prob_stats["correct"],
                    "오답 횟수": prob_stats["wrong"],
                }
            )
        st.table(problem_data)


def main():

    st.title("📚 숙제 검사 (학생별 통계)")

    if check_password():
        st.subheader("json 바로 확인용")

        # homework.json 파일 내용을 보여주는 expander 추가
        with st.expander("homework.json 파일 내용 보기 (날짜별 필터링)"):
            display_filtered_homework()

        #######

        # 인증 성공 후 데이터 표시
        homework_data = load_homework_data()

        if not homework_data:
            st.warning("숙제 데이터가 없거나 로드할 수 없습니다.")
            return

        # 날짜 선택 (최근 날짜부터 표시)
        date_range = get_date_range()
        selected_date = st.selectbox(
            "날짜 선택",
            date_range,
            format_func=lambda x: x.strftime("%Y-%m-%d"),
            index=0,  # 기본값을 가장 최근 날짜로 설정
        )
        selected_date_str = selected_date.strftime("%Y-%m-%d")

        if selected_date_str in homework_data:
            st.header(f"{selected_date_str} 숙제 현황")

            # 데이터 재구성
            student_data = reorganize_data(homework_data, selected_date_str)

            # 전체 통계
            total_students = len(student_data)
            total_problems = len(homework_data[selected_date_str])
            total_attempts = sum(
                stats["total_attempts"] for stats in student_data.values()
            )
            total_correct = sum(
                stats["total_correct"] for stats in student_data.values()
            )
            total_wrong = sum(stats["total_wrong"] for stats in student_data.values())

            st.subheader("전체 통계")
            col1, col2, col3, col4, col5 = st.columns(5)
            col1.metric("총 학생 수", total_students)
            col2.metric("총 문제 수", total_problems)
            col3.metric("총 시도 횟수", total_attempts)
            col4.metric("총 정답 횟수", total_correct)
            col5.metric("총 오답 횟수", total_wrong)

            # 학생별 통계
            st.subheader("학생별 통계")
            for student, stats in student_data.items():
                display_student_stats(student, stats)

        else:
            st.info(f"{selected_date_str}에 해당하는 숙제 데이터가 없습니다.")

        # 로그아웃 버튼
        if st.button("로그아웃"):
            st.session_state["password_correct"] = False
            st.rerun()


if __name__ == "__main__":
    main()
