import json
from datetime import date


def load_questions(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_results(file_path):
    try:
        with open(file_path, "r") as f:
            content = f.read()
            if content:
                return json.loads(content)
            else:
                return {}
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def save_result(results, file_path, name, success):
    today = date.today().isoformat()

    if today not in results:
        results[today] = {}

    if name not in results[today]:
        results[today][name] = {"success": 0, "failure": 0}

    if success:
        results[today][name]["success"] += 1
    else:
        results[today][name]["failure"] += 1

    with open(file_path, "w") as f:
        json.dump(results, f)
