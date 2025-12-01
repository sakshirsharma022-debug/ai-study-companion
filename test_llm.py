from modules.llm_engine import generate_llm_response, log_qa, handle_quiz, quiz_active

print("Test your AI chatbot. Type 'exit' to quit.")

while True:
    msg = input("you: ").strip()
    if msg.lower() == "exit":
        break

    quiz_reply, quiz_score = handle_quiz(msg)

    if quiz_reply:  # either a quiz answer or starting a quiz
        print("AI:", quiz_reply)
        log_qa(msg, quiz_reply, quiz_attempted=(quiz_score is not None), score=quiz_score)
        continue  # skip normal AI response

    reply = generate_llm_response(msg)
    print("AI:", reply)
    log_qa(msg, reply)
