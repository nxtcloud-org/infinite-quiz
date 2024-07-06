import os
import json


def read_json_file(file_path):
    with open(file_path, "r", encoding="utf-8") as file:
        return json.load(file)


def write_json_file(file_path, data):
    with open(file_path, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=2, ensure_ascii=False)


def add_fields(data):
    for item in data:
        if "correct" not in item:
            item["correct"] = 0
        if "incorrect" not in item:
            item["incorrect"] = 0
        if "correct_students" not in item:
            item["correct_students"] = []
    return data


def transform_choices(data):
    choice_keys = ["A", "B", "C", "D", "E", "F", "G", "H", "I", "J"]
    for problem in data:
        for lang in ["kor", "eng"]:
            choices = problem["choices"][lang]
            if not isinstance(choices, dict):
                transformed_choices = {
                    choice_keys[i]: choice for i, choice in enumerate(choices)
                }
                problem["choices"][lang] = transformed_choices
    return data


def process_file(file_path, add_new_fields=True, transform=True):
    data = read_json_file(file_path)
    if add_new_fields:
        data = add_fields(data)
    if transform:
        data = transform_choices(data)
    write_json_file(file_path, data)
    print(f"Updated {file_path}")


def process_folder(folder_path, add_new_fields=True, transform=True):
    for file_name in os.listdir(folder_path):
        if file_name.endswith(".json"):
            file_path = os.path.join(folder_path, file_name)
            process_file(file_path, add_new_fields, transform)


def main():
    print("JSON 파일 처리 프로그램")
    print("1. 단일 파일 처리")
    print("2. 폴더 내 모든 JSON 파일 처리")
    choice = input("선택하세요 (1 또는 2): ")

    add_new_fields = (
        input(
            "새 필드(correct, incorrect, correct_students)를 추가하시겠습니까? (y/n): "
        ).lower()
        == "y"
    )
    transform = input("선택지 형식을 변환하시겠습니까? (y/n): ").lower() == "y"

    if choice == "1":
        file_path = input("처리할 JSON 파일의 경로를 입력하세요: ")
        process_file(file_path, add_new_fields, transform)
    elif choice == "2":
        folder_path = input("처리할 폴더의 경로를 입력하세요: ")
        process_folder(folder_path, add_new_fields, transform)
    else:
        print("잘못된 선택입니다.")


if __name__ == "__main__":
    main()
