import streamlit as st
import json
import os
import config


def load_users():
    if os.path.exists(config.STUDENTS_FILE):
        with open(config.STUDENTS_FILE, "r") as f:
            return json.load(f)
    return {}


def save_users(users):
    with open(config.STUDENTS_FILE, "w") as f:
        json.dump(users, f)


st.set_page_config(page_title="로그인/회원가입", page_icon="🔐", layout="wide")

st.title("🔐 로그인 / 회원가입")

users = load_users()

tab1, tab2 = st.tabs(["로그인", "회원가입"])

with tab1:
    st.header("로그인")
    login_name = st.text_input("이름")
    login_password = st.text_input(
        "비밀번호 (4자리 숫자)", type="password", max_chars=4
    )

    if st.button("로그인"):
        if login_name in users and users[login_name]["password"] == login_password:
            st.session_state["user"] = users[login_name]
            st.success(f"{login_name}님, 환영합니다!")
            st.info("좌측 사이드바에서 '퀴즈' 페이지로 이동하여 퀴즈를 시작하세요.")
        else:
            st.error("이름 또는 비밀번호가 올바르지 않습니다.")

with tab2:
    st.header("회원가입")
    new_name = st.text_input("이름 (회원가입)")
    new_school = st.selectbox("학교", config.SCHOOLS)
    new_password = st.text_input(
        "비밀번호 (4자리 숫자)", type="password", max_chars=4, key="new_password"
    )

    if st.button("회원가입"):
        if new_name and new_school and new_password:
            if len(new_password) == 4 and new_password.isdigit():
                if new_name not in users:
                    users[new_name] = {
                        "name": new_name,
                        "school": new_school,
                        "password": new_password,
                        "point": 0,
                        "success": 0,
                        "failure": 0,
                        "attempts": 0,
                    }
                    save_users(users)
                    st.success("회원가입이 완료되었습니다. 이제 로그인할 수 있습니다.")
                else:
                    st.error("이미 존재하는 이름입니다.")
            else:
                st.error("비밀번호는 4자리 숫자여야 합니다.")
        else:
            st.error("모든 필드를 입력해주세요.")

if "user" in st.session_state:
    st.sidebar.success(f"{st.session_state['user']['name']}님 로그인됨")
    if st.sidebar.button("로그아웃"):
        del st.session_state["user"]
        st.experimental_rerun()
