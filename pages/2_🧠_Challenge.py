import streamlit as st
import random
import config
from utils.helpers import load_questions
import requests
import asyncio
import aiohttp
import json

# 버튼 키관리를 위한 현 페이지 정보
current_page = __file__.split("/")[-1].split(".")[0]  # 예: '2_🎯_Challenge'

# Lambda 함수 URL
CHALLENGE_LAMBDA_URL = config.CHALLENGE_LAMBDA_URL


async def invoke_lambda_async(session, operation, payload):
    async with session.post(
        CHALLENGE_LAMBDA_URL, json={"operation": operation, "payload": payload}
    ) as response:
        response_text = await response.text()
        print(f"Lambda response: {response_text}")  # 디버깅을 위한 로그 추가
        try:
            return await response.json()
        except json.JSONDecodeError:
            print(f"Failed to decode JSON. Raw response: {response_text}")
            return {"statusCode": response.status, "body": response_text}


def invoke_lambda(operation, payload):
    try:
        response = requests.post(
            CHALLENGE_LAMBDA_URL, json={"operation": operation, "payload": payload}
        )
        return response.json()
    except Exception as e:
        st.error(f"Error calling Lambda function: {str(e)}")
        return None


def initialize_session_state():
    if "questions" not in st.session_state:
        st.session_state["questions"] = load_questions(config.CHALLENGE_FILE)

    # 항상 새로운 문제 세트 생성
    st.session_state["challenge_questions"] = random.sample(
        st.session_state["questions"], config.CHALLENGE_SIZE
    )
    st.session_state["current_question"] = 0
    st.session_state["correct_answers"] = 0
    st.session_state["challenge_ended"] = False
    st.session_state["challenge_success"] = False
    st.session_state["user_answer"] = None
    st.session_state["show_result"] = False


def is_length_greater_than_two(lst):
    return len(lst) >= 2


def map_char_to_num(char):
    char_to_num = {"A": 0, "B": 1, "C": 2, "D": 3}
    return char_to_num.get(char, 4)  # 매핑에 없는 문자는 기본값 4를 반환


st.set_page_config(page_title="Challenge", page_icon="🎯", layout="wide")

# 로그인 상태 확인
if "user" not in st.session_state:
    st.warning("Challenge를 시작하려면 먼저 로그인해주세요.")
    st.info("좌측 사이드바에서 '🔐 Login' 페이지로 이동하여 로그인하세요.")
    st.stop()

user = st.session_state["user"]
user_id = user["user_id"]
username = user["username"]

# 'questions' 초기화
if "questions" not in st.session_state:
    st.session_state["questions"] = load_questions(config.CHALLENGE_FILE)

# Challenge 시작 또는 재시작 시 세션 상태 초기화
if "challenge_questions" not in st.session_state or st.session_state.get(
    "restart_challenge", False
):
    initialize_session_state()
    st.session_state["restart_challenge"] = False

st.title(":blue[_Challenge_] 🎯")
st.header(f"{username}님 :blue[화이팅!]", divider="rainbow")

# Challenge가 끝나지 않았고 아직 풀지 않은 문제가 있을 때만 질문을 표시
if (
    not st.session_state["challenge_ended"]
    and st.session_state["current_question"] < config.CHALLENGE_SIZE
):
    question = st.session_state["challenge_questions"][
        st.session_state["current_question"]
    ]

    # 질문 표시
    st.subheader(f"문제 {st.session_state['current_question'] + 1}")

    st.divider()
    question_idx = question["idx"]
    tab1, tab2 = st.tabs(["KOR", "ENG"])
    with tab1:
        st.write(f"문제 번호 : {question_idx}")
        st.write(question["question"]["kor"])
    with tab2:
        st.write(f"문제 번호 : {question_idx}")
        st.write(question["question"]["eng"])
    st.divider()

    is_multiple_answer = is_length_greater_than_two(question["answer"])

    options = list(question["choices"]["kor"].values())

    if is_multiple_answer:
        st.write(
            ":orange[복수 정답] 문제입니다. 해당하는 :orange[모든 답을 선택]하세요."
        )
        st.write("긴 문제는 선택지에 :orange[마우스를 올려두면] 보입니다.")
        user_answer = st.multiselect("답을 선택하세요:", options)
    else:
        user_answer = st.radio("답을 선택하세요:", options)

    on = st.toggle("영문 선택지 확인하기")

    if on:
        for i in question["choices"]["eng"]:
            st.write(f"{i} : {question['choices']['eng'][i]}")

    st.divider()

    # 다음 버튼
    if st.button("다음", type="primary"):
        st.session_state["user_answer"] = user_answer

        if is_multiple_answer:
            correct_options = [
                question["choices"]["kor"][ans] for ans in question["answer"]
            ]
            is_correct = set(user_answer) == set(correct_options)
        else:
            correct_option = question["choices"]["kor"][question["answer"][0]]
            is_correct = user_answer == correct_option

        if is_correct:
            st.session_state["correct_answers"] += 1
            st.session_state["current_question"] += 1

            # Lambda 함수 호출하여 사용자 데이터 업데이트
            invoke_lambda(
                "update_user_data",
                {
                    "user_id": user_id,
                    "is_correct": True,
                    "challenge_completed": st.session_state["current_question"]
                    == config.CHALLENGE_SIZE,
                },
            )

            if st.session_state["current_question"] == config.CHALLENGE_SIZE:
                st.session_state["challenge_ended"] = True
                st.session_state["challenge_success"] = True

                # Lambda 함수 호출하여 Challenge 결과 저장
                invoke_lambda(
                    "save_challenge_result",
                    {
                        "user_id": user_id,
                        "success": True,
                        "correct_answers": st.session_state["correct_answers"],
                        "challenge_size": config.CHALLENGE_SIZE,
                    },
                )
        else:
            st.session_state["challenge_ended"] = True
            st.session_state["challenge_success"] = False

            # Lambda 함수 호출하여 사용자 데이터 업데이트 및 Challenge 결과 저장
            invoke_lambda(
                "update_user_data",
                {"user_id": user_id, "is_correct": False, "challenge_completed": False},
            )
            invoke_lambda(
                "save_challenge_result",
                {
                    "user_id": user_id,
                    "success": False,
                    "correct_answers": st.session_state["correct_answers"],
                    "challenge_size": config.CHALLENGE_SIZE,
                },
            )

        st.rerun()

# Challenge가 끝났을 때 결과 표시
if st.session_state["challenge_ended"]:
    correct_questions = [
        str(q["idx"])
        for q in st.session_state["challenge_questions"][
            : st.session_state["correct_answers"]
        ]
    ]
    wrong_questions = [
        str(q["idx"])
        for q in st.session_state["challenge_questions"][
            st.session_state["correct_answers"] :
        ]
    ]

    # 비동기로 Lambda 함수 호출
    async def call_lambda():
        async with aiohttp.ClientSession() as session:
            result = await invoke_lambda_async(
                session,
                "save_challenge_result",
                {
                    "user_id": user_id,
                    "success": st.session_state["challenge_success"],
                    "correct_answers": st.session_state["correct_answers"],
                    "challenge_size": config.CHALLENGE_SIZE,
                    "correct_questions": correct_questions,
                    "wrong_questions": wrong_questions,
                },
            )
            print(f"Lambda result: {result}")  # 디버깅을 위한 로그 추가
            if isinstance(result, dict) and result.get("statusCode") != 200:
                print(
                    f"Error saving challenge result: {result.get('body', 'Unknown error')}"
                )
            elif not isinstance(result, dict):
                print(f"Unexpected result format: {result}")

    # 비동기 함수 실행
    asyncio.run(call_lambda())

    if st.session_state.get("challenge_success", False):
        st.success(f"축하합니다! {config.CHALLENGE_SIZE}문제를 모두 맞추셨습니다.")
        st.subheader(
            f"총 {config.CHALLENGE_SIZE}문제를 :green[_연속으로 모두_] 맞추셨습니다!!"
        )
        st.balloons()
    else:
        question = st.session_state["challenge_questions"][
            st.session_state["current_question"]
        ]

        correct_options = [
            question["choices"]["kor"][ans] for ans in question["answer"]
        ]
        st.error(f'당신의 오답 : {st.session_state["user_answer"]}')
        st.info(question["question"]["kor"])
        st.success(f'정답 : {", ".join(correct_options)}')
        st.warning(
            f"{config.CHALLENGE_SIZE}문제 중 {st.session_state['correct_answers']}문제를 맞추셨습니다."
        )
        st.info(
            "아쉽지만 다음에 다시 도전해보세요! 계속 노력하면 반드시 성공할 수 있습니다."
        )

    if st.button("Challenge 다시 시작하기", type="primary"):
        initialize_session_state()  # 새로운 문제 세트로 초기화
        st.rerun()

# Challenge 진행 상황 표시
st.sidebar.progress(st.session_state["current_question"] / config.CHALLENGE_SIZE)
st.sidebar.write(
    f"{st.session_state['current_question']} / {config.CHALLENGE_SIZE} 문제 완료"
)

# 사이드바에 사용자 정보 및 로그아웃 버튼 표시
if "user" in st.session_state:
    st.sidebar.success(f"{st.session_state['user']['username']}님 로그인됨")
    if st.sidebar.button("로그아웃", key=f"logout_button_{current_page}"):
        del st.session_state["user"]
        st.rerun()
else:
    st.sidebar.info("로그인이 필요합니다.")
