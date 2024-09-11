import json

# JSON 파일 읽기
with open('../exam/1_CLF_AWS CAF_31.json', 'r', encoding='utf-8') as file:
    quizzes = json.load(file)

# idx 값을 정수형 리스트로 추출
idx_list = [int(quiz['idx']) for quiz in quizzes]

# idx 리스트 콘솔에 출력
print(len(idx_list))
print(idx_list)
