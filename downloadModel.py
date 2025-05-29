#!/usr/bin/env python3
"""
Download model Q3 từ Hugging Face Hub
"""

import os
from huggingface_hub import hf_hub_download
from config import MODEL_REPO_ID, MODEL_FILENAME, MODEL_DIR, get_model_path

def download_model():
    """Download model Q3"""
    

    
    print(f"Repository: {MODEL_REPO_ID}")
    print(f"Filename: {MODEL_FILENAME}")
    print(f"Target path: {get_model_path()}")
    
    # Tạo thư mục models
    os.makedirs(MODEL_DIR, exist_ok=True)
    
    # Kiểm tra xem model đã tồn tại chưa, nếu rồi thì bypass
    if os.path.exists(get_model_path()):
        return get_model_path()
    
    try:
        print(f"\nDownloading {MODEL_FILENAME}...")
        
        # Download model
        model_path = hf_hub_download(
            repo_id=MODEL_REPO_ID,
            filename=MODEL_FILENAME,
            local_dir=MODEL_DIR,
            resume_download=True
        )
        
        print(f"\nDownloaded successfully!")
        print(f"Model path: {model_path}")
        
        return model_path
        
    except Exception as e:
        print(f"Error downloading model: {e}")
        return None

if __name__ == "__main__":
    model_path = download_model()
    
    if model_path:
        print("Run application with: python main.py")
    else:
        print("\nCannot download model. Please try again.")