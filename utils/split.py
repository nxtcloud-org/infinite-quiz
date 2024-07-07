# 20개씩 객체 쪼개서 저장하는 코드
import json
import math


def split_json_file(input_file, objects_per_file):
    # 입력 파일 읽기
    with open(input_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    # 전체 파일 수 계산
    total_files = math.ceil(len(data) / objects_per_file)

    # 데이터를 지정된 개수만큼 나누어 새 파일로 저장
    for i in range(total_files):
        start = i * objects_per_file
        end = start + objects_per_file
        chunk = data[start:end]

        output_file = f"homework{i+1}.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(chunk, f, ensure_ascii=False, indent=2)

        print(f"Created {output_file} with {len(chunk)} objects")


# 스크립트 실행
input_file = "homework.json"
objects_per_file = 30

split_json_file(input_file, objects_per_file)
