import os
from huggingface_hub import hf_hub_download

MODEL_DIR = "../models"  # Thư mục lưu mô hình
os.makedirs(MODEL_DIR, exist_ok=True)  # Tạo thư mục nếu chưa tồn tại

REPO_ID = "QuantFactory/Meta-Llama-3-8B-Instruct-GGUF"   # Đổi theo repo của bạn
# Tên tệp mô hình
FILENAME = "Meta-Llama-3-8B-Instruct.Q4_K_M.gguf"  # File model

# Tải mô hình
print("Đang tải mô hình...")
model_path = hf_hub_download(
    repo_id=REPO_ID,
    filename=FILENAME,
    local_dir=MODEL_DIR,
    local_dir_use_symlinks=False
)
print(f"Mô hình đã được tải về: {model_path}")