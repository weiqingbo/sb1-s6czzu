import shutil
import requests
import json
import fitz
import re
import os
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def clear_directory(directory):
    for filename in os.listdir(directory):
        file_path = os.path.join(directory, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            print(f'Failed to delete {file_path}. Reason: {e}')

def get_access_token():
    url = "https://aip.baidubce.com/oauth/2.0/token?grant_type=client_credentials&client_id=s4ZmMkYlKsS1u9hh95kk8Crm&client_secret=ykp9MrTbh4XTfhgBAK15Zh3jG8w7IvN6"
    payload = json.dumps("")
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }

    response = requests.request("POST", url, headers=headers, data=payload)
    return response.json().get("access_token")

def call_ernie_bot(question):
    url = "https://aip.baidubce.com/rpc/2.0/ai_custom/v1/wenxinworkshop/chat/completions_pro?access_token=" + get_access_token()

    payload = json.dumps({
        "messages": [
            {
                "role": "user",
                "content": f"{question}"
            }
        ]
    })
    headers = {
        'Content-Type': 'application/json'
    }

    response = requests.request("POST", url, headers=headers, data=payload)
    return response.json()

def read_pdf(file_path):
    try:
        doc = fitz.open(file_path)
        text = ""
        for page in doc:
            text += page.get_text()
        print(text)
        return text
    except Exception as e:
        print(f"Error reading PDF file: {e}")
        return ""

def extract_sections(text):
    sections = ["自我介绍", "工作经历", "项目经历", "专业技能"]
    content = {section: "" for section in sections}

    pattern = r"(自我介绍|工作经历|项目经历|专业技能)"
    matches = re.finditer(pattern, text)

    section_positions = [(match.start(), match.group()) for match in matches]

    for i, (start, section) in enumerate(section_positions):
        end = section_positions[i + 1][0] if i + 1 < len(section_positions) else len(text)
        content[section] = text[start + len(section):end].strip()

    return content

@app.route('/api/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'status': 'failed', 'message': 'No file part in the request'})

    file = request.files['file']
    if file.filename == '':
        return jsonify({'status': 'failed', 'message': 'No selected file'})

    try:
        clear_directory(UPLOAD_FOLDER)
        file_path = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(file_path)

        resume_text = read_pdf(file_path)
        content = extract_sections(resume_text)
        print(content)

        question_prompt = f"我有一份简历，简历的内容都放在了一个json数据里面，请你根据我的简历内容，生成10个对应要面试的简历问题。这是简历内容:{content}，注意：直接给出10个对应要面试的简历问题就行，不要给我回答无关的字符，例如：*、+等等。"
        question_response = call_ernie_bot(question_prompt)
        questions = question_response.get("result", "未能生成自我介绍")

        # question_prompt_test = f"我有一份简历，简历的内容都放在了一个json数据里面，请你根据我的简历内容，生成10个对应要面试的简历问题。这是简历内容:{content}，注意：直接给出10个对应要面试的简历问题就行，不要给我回答无关的字符，例如：*、+等等。"
        # question_response_test = call_ernie_bot(question_prompt_test)
        # questions_test = question_response_test.get("result", "未能生成自我介绍")
        # print(questions_test)

        print("ques")
        print(questions)
        questions = questions.split('\n')
        print("question")
        print(questions)

        global filtered_questions
        filtered_questions = [line for line in questions if re.match(r"^\d+\.", line)]
        global user_answers
        user_answers = []

        return jsonify({'status': 'success'})
    except Exception as e:
        print(f"Error during file upload: {e}")
        return jsonify({'status': 'failed', 'message': str(e)})

@app.route('/api/interview', methods=['GET', 'POST'])
def interview():
    if request.method == 'GET':
        question_index = int(request.args.get('index', 0))
        if question_index < len(filtered_questions):
            return jsonify({'question': filtered_questions[question_index]})
        else:
            return jsonify({'question': None})

    elif request.method == 'POST':
        answer = request.json.get('answer')
        user_answers.append(answer)

        if len(user_answers) == len(filtered_questions):
            questions_answers = []
            for i in range(len(user_answers)):
                questions_answers.append(filtered_questions[i])
                questions_answers.append(user_answers[i])

            print(questions_answers)
            evaluate_prompt = f"你现在是一个简历评分员，总分值为0 - 10分，问题是面试官问的，答案是面试者答的，你要根据问题以及面试者对每个问题的回答情况进行总体评分，评分要严格！随便回答的不能给分！要贴近问题的答案才能给分！以及针对回答的问题提出建议。每个面试问题及面试者答案为：{questions_answers}"
            evaluate_response = call_ernie_bot(evaluate_prompt)
            evaluate = evaluate_response.get("result", "未能生成自我介绍")
            evaluate = evaluate.replace("**", "")
            print(evaluate)
            return jsonify({'status': 'success', 'evaluation': evaluate})

        return jsonify({'status': 'success'})

if __name__ == '__main__':
    app.run(debug=True)
