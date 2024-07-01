import json


# 파일 읽기 함수
def read_json_file(file_path):
    with open(file_path, "r", encoding="utf-8") as file:
        return json.load(file)


# 파일 쓰기 함수
def write_json_file(file_path, data):
    with open(file_path, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=2, ensure_ascii=False)


# 문제 세트 변환 함수
def transform_choices(problem_set):
    for problem in problem_set:
        kor_choices = problem["choices"]["kor"]
        eng_choices = problem["choices"]["eng"]
        choice_keys = ["A", "B", "C", "D", "E", "F", "G", "H", "I", "J"]

        # 변환된 딕셔너리 생성
        transformed_kor = {
            choice_keys[i]: choice for i, choice in enumerate(kor_choices)
        }
        transformed_eng = {
            choice_keys[i]: choice for i, choice in enumerate(eng_choices)
        }

        # 기존 선택지 대체
        problem["choices"]["kor"] = transformed_kor
        problem["choices"]["eng"] = transformed_eng

    return problem_set


# 파일 경로
file_path = "test2.json"

# 파일 읽기
problem_set = read_json_file(file_path)

# 변환된 문제 세트
transformed_problem_set = transform_choices(problem_set)

# 변환된 데이터를 파일에 쓰기
write_json_file(file_path, transformed_problem_set)
