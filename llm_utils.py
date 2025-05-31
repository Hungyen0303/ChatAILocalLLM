from llm_processor import llm, logger

def ask_llm_yesno(file_content: str, topic: str) -> bool:
    prompt = (
        f"Nội dung file:\n{file_content}\n\n"
        f"Câu hỏi: File này có liên quan đến chủ đề '{topic}' không? "
        f"Trả lời duy nhất bằng 'Có' hoặc 'Không'."
    )
    try:
        response = llm.create_chat_completion(
            messages=[
                {"role": "system", "content": "Bạn là AI phân loại file."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=5,
            temperature=0.1,
            stop=["\n"]
        )
        answer = response["choices"][0]["message"]["content"].strip().lower()
        return answer.startswith("có")
    except Exception as e:
        logger.error(f"Lỗi LLM khi phân loại file: {e}")
        return False 