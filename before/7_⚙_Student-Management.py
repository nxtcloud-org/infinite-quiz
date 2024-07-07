import streamlit as st
import json
import os
import config  # config.py 파일에서 ADMIN_PASSWORD를 가져옵니다.

# 학생 데이터 파일 경로
STUDENT_DATA_PATH = "db/student.json"


# 학생 데이터 로드
def load_student_data():
    if os.path.exists(STUDENT_DATA_PATH):
        with open(STUDENT_DATA_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


# 학생 데이터 저장
def save_student_data(data):
    with open(STUDENT_DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# 비밀번호 확인 함수
def check_password():
    def password_entered():
        if st.session_state["password"] == config.ADMIN_PASSWORD:
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # 비밀번호 세션에서 삭제
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        st.text_input(
            "관리자 비밀번호를 입력하세요",
            type="password",
            on_change=password_entered,
            key="password",
        )
        return False
    elif not st.session_state["password_correct"]:
        st.text_input(
            "관리자 비밀번호를 입력하세요",
            type="password",
            on_change=password_entered,
            key="password",
        )
        st.error("비밀번호가 올바르지 않습니다.")
        return False
    else:
        return True


# 메인 함수
def main():
    st.title("학생 데이터 관리")

    if check_password():
        # 학생 데이터 로드
        student_data = load_student_data()

        # 사이드바에 기능 선택
        action = st.sidebar.selectbox("작업 선택", ["조회/수정", "생성", "삭제"])

        if action == "조회/수정":
            st.header("학생 정보 조회/수정")
            student_name = st.selectbox("학생 선택", list(student_data.keys()))

            if student_name:
                student = student_data[student_name]
                new_name = st.text_input("이름", student["name"])
                new_school = st.text_input("소속", student["school"])
                new_password = st.text_input(
                    "비밀번호", student["password"], type="password"
                )

                if st.button("정보 수정"):
                    student_data[student_name]["name"] = new_name
                    student_data[student_name]["school"] = new_school
                    student_data[student_name]["password"] = new_password
                    save_student_data(student_data)
                    st.success("학생 정보가 수정되었습니다.")

        elif action == "생성":
            st.header("새 학생 생성")
            new_name = st.text_input("이름")
            new_school = st.text_input("소속")
            new_password = st.text_input("비밀번호", type="password")

            if st.button("학생 생성"):
                if new_name and new_name not in student_data:
                    student_data[new_name] = {
                        "name": new_name,
                        "school": new_school,
                        "password": new_password,
                        "point": 0,
                        "success": 0,
                        "failure": 0,
                        "attempts": 0,
                        "wrong": 0,
                        "correct": 0,
                    }
                    save_student_data(student_data)
                    st.success(f"새 학생 '{new_name}'이(가) 생성되었습니다.")
                elif not new_name:
                    st.error("학생 이름을 입력해주세요.")
                else:
                    st.error("이미 존재하는 학생 이름입니다.")

        elif action == "삭제":
            st.header("학생 삭제")
            student_to_delete = st.selectbox(
                "삭제할 학생 선택", list(student_data.keys())
            )

            if st.button("학생 삭제"):
                if student_to_delete in student_data:
                    del student_data[student_to_delete]
                    save_student_data(student_data)
                    st.success(f"'{student_to_delete}' 학생이 삭제되었습니다.")
                else:
                    st.error("선택한 학생을 찾을 수 없습니다.")

        # 현재 학생 목록 표시
        st.header("현재 학생 목록")
        st.table(
            [
                {"이름": student["name"], "소속": student["school"]}
                for student in student_data.values()
            ]
        )

        if st.button("로그아웃"):
            st.session_state["password_correct"] = False
            st.experimental_rerun()


if __name__ == "__main__":
    main()
