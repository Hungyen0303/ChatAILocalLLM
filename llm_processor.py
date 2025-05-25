import os
from llama_cpp import Llama

# Đường dẫn đến file mô hình
MODEL_PATH = "models/Meta-Llama-3-8B-Instruct.Q4_K_M.gguf"

# Kiểm tra file mô hình
if not os.path.exists(MODEL_PATH):
    raise FileNotFoundError(f"Model file not found at: {MODEL_PATH}")

# Khởi tạo mô hình
try:
    llm = Llama(
        model_path=MODEL_PATH,
        n_ctx=4096,
        n_threads=4,
        n_batch=512,
        use_mlock=True,
        verbose=False,
        chat_format="llama-3"
    )
    print("✅ Model loaded successfully!")
except Exception as e:
    print(f"❌ Error loading model: {e}")
    exit(1)

# Hàm query chính 
def process_prompt(prompt: str) -> str:
    """
    Xử lý câu hỏi với format chuẩn Llama-3-Instruct, trả về phản hồi bắt đầu bằng
    'Đang tìm kiếm trong thư mục…' nếu câu hỏi liên quan đến tìm kiếm file.
    """
    system_prompt = """
    Bạn là một trợ lý AI chạy offline, hỗ trợ tìm kiếm file trong thư mục. 
    Nếu câu hỏi liên quan đến tìm kiếm file, bắt đầu phản hồi bằng "Đang tìm kiếm trong thư mục…".
    Trả lời ngắn gọn, tự nhiên và phù hợp.
    """
    
    try:
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ]
        
        response = llm.create_chat_completion(
            messages=messages,
            max_tokens=256,
            temperature=0.7,
            top_p=0.9,
            stop=None,
            repeat_penalty=1.1
        )
        
        content = response["choices"][0]["message"]["content"].strip()
        
        if not content:
            return "Xin lỗi, tôi không thể tạo ra phản hồi phù hợp. Bạn có thể thử lại không?"
        
        return content
        
    except Exception as e:
        return f"Lỗi khi xử lý: {str(e)}"



# Hàm thay thế nếu chat completion không hoạt động , 
def process_prompt_alternative(prompt: str) -> str:
    """
    Phương pháp thay thế sử dụng raw prompt nếu chat completion không hoạt động.
    """
    formatted_prompt = f"""<|begin_of_text|><|start_header_id|>system<|end_header_id>

Bạn là một trợ lý AI chạy offline, hỗ trợ tìm kiếm file trong thư mục. 
Nếu câu hỏi liên quan đến tìm kiếm file, bắt đầu phản hồi bằng "Đang tìm kiếm trong thư mục…".
Trả lời ngắn gọn, tự nhiên và phù hợp.<|eot_id|><|start_header_id|>user<|end_header_id>

{prompt}<|eot_id|><|start_header_id|>assistant<|end_header_id>

"""
    try:
        output = llm(
            formatted_prompt,
            max_tokens=256,
            temperature=0.7,
            top_p=0.9,
            stop=["<|eot_id|>", "<|end_of_text|>"],
            echo=False,
            repeat_penalty=1.1
        )
        
        response = output["choices"][0]["text"].strip()
        
        if not response:
            return "Xin lỗi, tôi không thể tạo ra phản hồi phù hợp. Bạn có thể thử lại không?"
        
        return response
        
    except Exception as e:
        return f"Lỗi khi xử lý: {str(e)}"