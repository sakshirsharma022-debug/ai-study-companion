from dotenv import load_dotenv
import os
import requests
import json
from datetime import datetime

load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_API_URL = os.getenv("GROQ_API_URL")

quiz_active = False
quiz_questions = []
current_question_index = 0
score = 0

SYSTEM_PROMPT = """
You are a highly knowledgeable AI tutor. 
Answer every user question directly and clearly. 
Do not ask the user to respond first or repeat instructions. 
Provide examples if needed, but stay concise and educational.
"""

def generate_llm_response(user_msg):
    if not user_msg:
        return "Please type something"
    payload = {
        "model":"llama-3.1-8b-instant",
        "messages":[
            {"role":"system","content":SYSTEM_PROMPT},
            {"role":"user","content":user_msg}
        ],
        "temperature":0.3,
        "max_tokens":300
    }
    headers = {
        "Authorization":f"Bearer {GROQ_API_KEY}",
        "Content-Type":"application/json"
    }
    try:
        response = requests.post(GROQ_API_URL, json=payload, headers=headers)
        data = response.json()
        return data["choices"][0]["message"]["content"]
    except Exception as e:
        print("error details:", e)
        return "Error contacting AI engine."

HISTORY_FILE = "study_history.json"

def log_qa(user_question, ai_answer, quiz_attempted=False, score=None):
    entry = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "user_question": user_question,
        "ai_answer": ai_answer,
        "quiz_attempted": quiz_attempted,
        "quiz_score": score
    }
    try:
        with open(HISTORY_FILE, "r") as f:
            history = json.load(f)
    except FileNotFoundError:
        history = []
    history.append(entry)
    with open(HISTORY_FILE, "w") as f:
        json.dump(history, f, indent=4)

def get_quiz_questions(concept):
    quiz_prompt = f"""
    Create exactly 2 multiple choice questions (MCQ) from this topic:

    {concept}

    Format EXACTLY like this:

    Q1: <question>
    A) option
    B) option
    C) option
    D) option
    ANSWER: <letter>

    Q2: <question>
    A) option
    B) option
    C) option
    D) option
    ANSWER: <letter>
    """

    payload = {
        "model": "llama-3.1-8b-instant",
        "messages": [
            {"role": "system", "content": "Generate quizzes ONLY in the exact format."},
            {"role": "user", "content": quiz_prompt}
        ],
        "temperature": 0.3,
        "max_tokens": 250
    }

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    response = requests.post(GROQ_API_URL, json=payload, headers=headers)
    data = response.json()
    return data["choices"][0]["message"]["content"]


def parse_quiz(quiz_text):
    questions = []
    blocks = quiz_text.strip().split("\n\n")

    for block in blocks:
        lines = block.split("\n")
        question = lines[0]
        options = lines[1:5]
        answer = lines[5].split(":")[1].strip()

        questions.append({
            "question": question,
            "options": "\n".join(options),
            "answer": answer
        })

    return questions


def handle_quiz(user_msg):
    global quiz_active, quiz_questions, current_question_index, score

    if "quiz" in user_msg.lower() and not quiz_active:
        concept = "Explain " + user_msg
        quiz_raw = get_quiz_questions(concept)
        quiz_questions = parse_quiz(quiz_raw)
        quiz_active = True
        current_question_index = 0
        score = 0
        q = quiz_questions[0]
        return f"{q['question']}\n{q['options']}", None

    if quiz_active:
        user_ans = user_msg.strip().upper()
        correct_ans = quiz_questions[current_question_index]["answer"]
        response = ""
        if user_ans == correct_ans:
            score += 1
            response += "✅ Correct!!\n\n"
        else:
            response += f"❌ Wrong. Correct answer was {correct_ans}\n\n"

        current_question_index += 1

        if current_question_index >= len(quiz_questions):
            quiz_active = False
            final_score = score
            response += f"🎉 Quiz finished!! Your Score: {score}/{len(quiz_questions)}"
            score = 0
            return response, final_score

        q = quiz_questions[current_question_index]
        response += f"{q['question']}\n{q['options']}"
        return response, None

    return None, None
