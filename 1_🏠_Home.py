import streamlit as st
import config

st.set_page_config(
    page_title=config.APP_TITLE, page_icon=config.APP_ICON, layout="wide"
)

st.title(":blue[_AWS CLF_] Certificate Navigator 🧭")


st.header("📢 :blue[_Notice_]", divider="rainbow")
st.markdown(
    """
        - 자격증 합격을 위해서는 :orange[반복적으로 많은 문제를 풀어보는 것]이 필수입니다.
        - 하루에 성공을 하나씩 쌓는게 중요합니다. 실패는 중요하지 않아요.
        - :orange[로그인 후] 문제를 확인할 수 있습니다.
        """
)
st.header("🃏 :blue[_Flash Card_]", divider="rainbow")
st.markdown(
    """
    - :orange[영역별 개념]을 기억하기 위한 플래시 카드입니다.
    - 핵심 개념에 대해서 :orange[간단하게 설명]할 수 있게 되도록 활용해보세요.
    """
)

st.header("📝 :blue[_Homework_]", divider="rainbow")
st.markdown(
    """
    - :orange[영역별 문제]를 추출해서 퀴즈로 제시합니다.
    - 신중하게 풀기보다 :orange[빠르게 많은 문제를 풀어보면서 익숙해지는 것]이 더 좋습니다.
    """
)

st.header("⚙️:blue[_시스템 안내 사항_]", divider="rainbow")
st.markdown(
    """
    - :orange[문제를 찾지 못함] 유형의 오류시 새로고침 후 다시 문제 페이지에 접근해보세요.
    """
)

st.divider()

# 로그인 상태 확인
# if "user" not in st.session_state:
#     st.warning("퀴즈를 시작하려면 먼저 로그인해주세요.")
#     st.info("좌측 사이드바에서 '🔐 Login' 페이지로 이동하여 로그인하세요.")
# else:
#     user = st.session_state.get("user", {})
#     username = user.get("username", "알 수 없는 사용자")
#     st.header(
#         f"🏁 :blue[_{username}_]님, 환영합니다!",
#         divider="rainbow",
#     )

#     st.divider()

#     st.subheader(
#         f"현재 Challenge는 총 :blue[_{config.CHALLENGE_SIZE}개_]의 문제를 :blue[_연속_]으로 맞춰야 합니다."
#     )

# 디버깅용 (개발 중에만 사용, 배포 시 제거)
# if st.checkbox("Show session state (Debug)"):
#     st.write(st.session_state)
