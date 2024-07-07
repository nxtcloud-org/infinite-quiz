import streamlit as st
import json
import config
import requests

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
    login_name = st.text_input("이름")
    login_password = st.text_input(
        "비밀번호 (4자리 숫자)", type="password", max_chars=4
    )

    if st.button("로그인"):
        response = invoke_lambda(
            "login", {"username": login_name, "password": login_password}
        )
        if response["statusCode"] == 200:
            user_data = json.loads(response["body"])
            user_details = invoke_lambda("get_user", {"user_id": user_data["user_id"]})
            if user_details["statusCode"] == 200:
                st.session_state["user"] = json.loads(user_details["body"])
                st.success(f"{login_name}님, 환영합니다!")
                st.info("좌측 사이드바에서 '퀴즈' 페이지로 이동하여 퀴즈를 시작하세요.")
            else:
                st.error("사용자 정보를 가져오는데 실패했습니다.")
        else:
            st.error("이름 또는 비밀번호가 올바르지 않습니다.")

with tab2:
    st.header("회원가입")

    # 결과 메시지를 표시할 빈 요소 생성
    result_placeholder = st.empty()

    # 폼 생성
    with st.form("register_form"):
        new_name = st.text_input("이름 (회원가입)")
        new_school = st.selectbox("학교 또는 소속", config.SCHOOLS)
        new_team = st.selectbox("팀", config.TEAMS)
        new_password = st.text_input(
            "비밀번호 (4자리 숫자)", type="password", max_chars=4
        )

        # 폼 제출 버튼
        submit_button = st.form_submit_button("회원가입")

    if submit_button:
        if new_name and new_school and new_password:
            if len(new_password) == 4 and new_password.isdigit():
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
                        result_placeholder.error(f"{message}")
                    elif statuscode == 200:
                        result_placeholder.success(
                            f"회원가입이 완료되었습니다. 로그인탭에서 로그인해주세요."
                        )
                        # 폼 초기화
                        st.experimental_rerun()
                    else:
                        result_placeholder.error(
                            f"회원가입 실패. 관리자에게 문의해주세요."
                        )
                except Exception as e:
                    result_placeholder.error(
                        f"회원가입 중 오류가 발생했습니다: {str(e)}"
                    )
            else:
                result_placeholder.error("비밀번호는 4자리 숫자여야 합니다.")
        else:
            result_placeholder.error("이름, 소속, 비밀번호는 필수 입력 항목입니다.")

if "user" in st.session_state:
    st.sidebar.success(f"{st.session_state['user']['username']}님 로그인됨")
    if st.sidebar.button("로그아웃"):
        del st.session_state["user"]
        st.rerun()

# 사용자 정보 업데이트 (옵션)
if "user" in st.session_state:
    st.header("사용자 정보 업데이트")
    update_school = st.text_input(
        "소속 업데이트", value=st.session_state["user"].get("school", "")
    )
    update_team = st.text_input(
        "팀 업데이트", value=st.session_state["user"].get("team", "")
    )

    if st.button("정보 업데이트"):
        response = invoke_lambda(
            "update_user",
            {
                "user_id": st.session_state["user"]["user_id"],
                "updates": {"school": update_school, "team": update_team},
            },
        )
        if response["statusCode"] == 200:
            st.success("사용자 정보가 업데이트되었습니다.")
            # 세션의 사용자 정보도 업데이트
            st.session_state["user"]["school"] = update_school
            st.session_state["user"]["team"] = update_team
        else:
            st.error("사용자 정보 업데이트에 실패했습니다.")
