import json
import os


# 주어진 경로의 모든 JSON 파일을 처리하여 파일명과 idx 값을 추출하는 함수
def extract_idx_from_files(directory_path):
    result = {}

    # 디렉토리 내 모든 파일을 반복
    for filename in os.listdir(directory_path):
        if filename.endswith(".json"):  # JSON 파일만 처리
            file_path = os.path.join(directory_path, filename)
            with open(file_path, "r", encoding="utf-8") as file:
                try:
                    quizzes = json.load(file)
                    # 각 파일의 idx 값을 리스트로 추출
                    idx_list = [int(quiz["idx"]) for quiz in quizzes]
                    # 파일명 (확장자 제외) 을 키로, idx 리스트를 값으로 저장
                    result[filename] = idx_list
                except json.JSONDecodeError:
                    print(f"Error decoding JSON in file: {filename}")
                except KeyError:
                    print(f"Key 'idx' not found in file: {filename}")

    return result


# 결과를 idx_list.json 파일에 저장하는 함수
def save_idx_list_to_file(data, output_file):
    with open(output_file, "w", encoding="utf-8") as output:
        json.dump(data, output, ensure_ascii=False, indent=4)


# 실행
if __name__ == "__main__":
    directory_path = input("Enter the directory path: ")  # 사용자로부터 경로 입력
    idx_data = extract_idx_from_files(directory_path)

    # 결과를 idx_list.json에 저장
    save_idx_list_to_file(idx_data, "idx_list.json")

    print(f"Extracted idx list has been saved to 'idx_list.json'.")
