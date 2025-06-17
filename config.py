#!/usr/bin/env python3

import os

# =============================================================================
# CẤU HÌNH MODEL
# =============================================================================

# Model Q3
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
    "D": ["hướng dẫn", "guide", "manual", "tutorial"],
    "E": ["khác", "other", "miscellaneous", "miscellany"]
}

# =============================================================================
# CẤU HÌNH UI - Cơ bản
# =============================================================================

UI_TITLE = "Chat AI Tìm kiếm & Phân loại File"
UI_PORT = 7860 