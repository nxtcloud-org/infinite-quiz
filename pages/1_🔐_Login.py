import streamlit as st
import json
import config
import requests

# 버튼 키관리를 위한 현 페이지 정보
current_page = __file__.split("/")[-1].split(".")[0]  # 예: '1_🔐_Login'

# Lambda 함수 URL을 환경 변수로 관리
USERS_LAMBDA_URL = config.USERS_LAMBDA_URL


def invoke_lambda(operation, payload):
    request_data = {"operation": operation, "payload": payload}
    try:
        response = requests.post(USERS_LAMBDA_URL, json=request_data)
        return response.json()
    except:
        return {
            "statusCode": 500,
            "body": json.dumps({"message": "Error calling Lambda"}),
        }


st.set_page_config(page_title="로그인/회원가입", page_icon="🔐", layout="wide")

st.title("🔐 로그인 / 회원가입")

tab1, tab2 = st.tabs(["로그인", "회원가입"])

with tab1:
    st.header("로그인")

    with st.form(key="login_form"):
        login_name = st.text_input("이름")
        login_school = st.selectbox(
            "학교 또는 소속",
            config.SCHOOLS,
            index=None,
            placeholder="학교 또는 소속을 선택해주세요.",
        )
        login_team = st.selectbox(
            "팀",
            config.TEAMS,
            index=None,
            placeholder="팀을 선택해주세요.",
        )
        login_password = st.text_input(
            "비밀번호 (4자리 숫자)", type="password", max_chars=4
        )
        login_button = st.form_submit_button("로그인", type="primary")
    if login_button:
        if login_name and login_school and login_team and login_password:
            if len(login_password) == 4 and login_password.isdigit():
                with st.spinner("로그인 중..."):
                    try:
                        response = invoke_lambda(
                            "login",
                            {
                                "username": login_name,
                                "school": login_school,
                                "team": login_team,
                                "password": login_password,
                            },
                        )
                        if response["statusCode"] == 200:
                            user_data = json.loads(response["body"])
                            st.session_state["user"] = user_data
                            st.success(f"{login_name}님, 환영합니다!")
                            st.info(
                                "좌측 사이드바 'Home' 페이지에서 안내사항을 확인할 수 있습니다."
                            )
                            st.info(
                                "좌측 사이드바의 여러 페이지에서 공부를 시작하세요!"
                            )
                        elif response["statusCode"] == 401:
                            st.error("로그인 정보가 올바르지 않습니다.")
                        else:
                            st.error(
                                "로그인 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요."
                            )
                    except Exception as e:
                        st.error(f"로그인 중 오류가 발생했습니다: {str(e)}")
            else:
                st.error("비밀번호는 4자리 숫자여야 합니다.")
        else:
            st.error("모든 필드를 입력해주세요.")

# 사이드바에 사용자 정보 및 로그아웃 버튼 표시
if "user" in st.session_state:
    st.sidebar.success(f"{st.session_state['user']['username']}님 로그인됨")
    if st.sidebar.button("로그아웃", key=f"logout_button_{current_page}"):
        del st.session_state["user"]
        st.rerun()
else:
    st.sidebar.info("로그인이 필요합니다.")


with tab2:
    st.header("회원가입")

    with st.form(key="register_form", clear_on_submit=True):
        new_name = st.text_input("이름 (회원가입)")
        new_school = st.selectbox(
            "학교 또는 소속",
            config.SCHOOLS,
            index=None,
            placeholder="학교 또는 소속을 선택해주세요. 선택지에 없는 항목은 관리자에게 문의해주세요.",
        )
        new_team = st.selectbox(
            "팀",
            config.TEAMS,
            index=None,
            placeholder="학교 또는 소속을 선택해주세요. 선택지에 없는 항목은 관리자에게 문의해주세요.",
        )
        new_password = st.text_input(
            "비밀번호 (4자리 숫자)", type="password", max_chars=4
        )

        submit_button = st.form_submit_button("회원가입", type="primary")

    if submit_button:
        if new_name and new_school and new_password:
            if len(new_password) == 4 and new_password.isdigit():
                with st.spinner("회원가입 처리 중..."):
                    try:
                        response = invoke_lambda(
                            "register",
                            {
                                "username": new_name,
                                "password": new_password,
                                "school": new_school,
                                "team": new_team,
                            },
                        )
                        statuscode = response["statusCode"]
                        json_body = json.loads(response["body"])
                        message = json_body["message"]
                        if statuscode == 400:
                            st.error(f"{message}")
                        elif statuscode == 200:
                            st.success(f"{message} 로그인탭에서 로그인해주세요.")
                        else:
                            st.error(f"회원가입 실패. 관리자에게 문의해주세요.")
                    except Exception as e:
                        st.error(f"회원가입 중 오류가 발생했습니다: {str(e)}")
            else:
                st.error("비밀번호는 4자리 숫자여야 합니다.")
        else:
            st.error("이름, 소속, 비밀번호는 필수 입력 항목입니다.")
