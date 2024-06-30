import os
import json


# 각문제에 correct, incorrect 붙이기
def update_exam_files(folder_path):
    for file_name in os.listdir(folder_path):
        if file_name.endswith(".json"):
            file_path = os.path.join(folder_path, file_name)
            with open(file_path, "r", encoding="utf-8") as file:
                data = json.load(file)

            for item in data:
                item["correct"] = 0
                item["incorrect"] = 0

            with open(file_path, "w", encoding="utf-8") as file:
                json.dump(data, file, ensure_ascii=False, indent=4)
            print(f"Updated {file_name}")


# 폴더 경로를 지정하세요
folder_path = "exam"
update_exam_files(folder_path)
