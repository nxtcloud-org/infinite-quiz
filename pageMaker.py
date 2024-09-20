import os
import re

# config.py에서 TOPICS 딕셔너리를 가져옵니다.
from config import TOPICS


def sanitize_filename(filename):
    """파일명에서 사용할 수 없는 문자를 제거하거나 대체합니다."""
    return re.sub(r'[\\/*?:"<>|]', "", filename)


def create_topic_files():
    start_index = 2  # 파일명 시작 번호를 2로 변경

    # 현재 스크립트 위치에 'pages' 폴더 경로 생성
    pages_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "pages")

    # 'pages' 폴더가 없으면 생성
    if not os.path.exists(pages_dir):
        os.makedirs(pages_dir)

    for key, value in TOPICS.items():
        if key == "cloudFundamentals" or start_index > 1:
            title = value["title"]
            filename = f"{start_index}_{sanitize_filename(title)}.py"
            filepath = os.path.join(pages_dir, filename)

            with open(filepath, "w", encoding="utf-8") as f:
                f.write(f"from q_page_format import render_question_page\n")
                f.write(f'CURRENT_TOPIC = "{key}"\n')
                f.write(f"render_question_page(CURRENT_TOPIC)\n")

            print(f"Created file: {filepath}")
            start_index += 1


if __name__ == "__main__":
    create_topic_files()
