#!/usr/bin/env python3
"""
Cấu hình đơn giản cho Chat AI Local LLM
"""

import os

# =============================================================================
# CẤU HÌNH MODEL - Quan trọng nhất
# =============================================================================

# Model Q3 để tối ưu tốc độ
MODEL_REPO_ID = "QuantFactory/Meta-Llama-3-8B-Instruct-GGUF"
MODEL_FILENAME = "Meta-Llama-3-8B-Instruct.Q3_K_M.gguf"
MODEL_DIR = "../models"

def get_model_path():
    """Lấy đường dẫn model"""
    return os.path.join(MODEL_DIR, MODEL_FILENAME)

# =============================================================================
# CẤU HÌNH FILESYSTEM - Cần thiết cho MCP
# =============================================================================

SUPPORTED_EXTENSIONS = ['.pdf', '.docx', '.doc', '.pptx', '.ppt', '.txt']
CONTENT_PREVIEW_LIMIT = 1000

# Từ khóa phân loại
CATEGORY_KEYWORDS = {
    "A": ["kế hoạch", "plan", "chiến lược", "strategy"],
    "B": ["marketing", "quảng cáo", "bán hàng", "sales"], 
    "C": ["báo cáo", "report", "thống kê", "statistics"],
    "D": ["hướng dẫn", "guide", "manual", "tutorial"]
}

# =============================================================================
# CẤU HÌNH UI - Cơ bản
# =============================================================================

UI_TITLE = "Chat AI Tìm kiếm & Phân loại File"
UI_PORT = 7860 