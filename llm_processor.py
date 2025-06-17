import json
import os
import re
from llama_cpp import Llama
import logging

# Import cấu hình đơn giản
from config import MODEL_DIR, MODEL_FILENAME, get_model_path

# Import MCP filesystem client
try:
    from mcp_client import process_filesystem_query, initialize_filesystem
    MCP_AVAILABLE = True
    logging.info("MCP Filesystem client loaded")
except ImportError as e:
    logging.warning(f"MCP Filesystem not available: {e}")
    MCP_AVAILABLE = False

logger = logging.getLogger(__name__)

# Đường dẫn model từ config
MODEL_PATH = get_model_path()

# Kiểm tra file mô hình
if not os.path.exists(MODEL_PATH):
    raise FileNotFoundError(f"Model file not found at: {MODEL_PATH}")

# Khởi tạo mô hình
try:
    llm = Llama(
        model_path=MODEL_PATH,
        n_ctx=2048,
        n_threads=8,
        n_batch=128,
        use_mlock=True,
        verbose=False,
        chat_format="llama-3"
    )
    logger.info(f"Model loaded: {MODEL_FILENAME}")
except Exception as e:
    logger.error(f"Error loading model: {e}")
    raise

# Khởi tạo MCP Filesystem
if MCP_AVAILABLE:
    try:
        initialize_filesystem()
        logger.info("MCP Filesystem initialized")
    except Exception as e:
        logger.warning(f"MCP Filesystem initialization failed: {e}")
        MCP_AVAILABLE = False


#===================== detect_intent =====================

def detect_intent(prompt: str) -> tuple:
    """Detect intent"""
    
     # Sử dụng intents để xác định intent bằng LLM
    # Các intent có thể có
    intents_text = """
    - "search": Tìm kiếm file dựa trên nội dung hoặc tên
    - "classify": Phân loại file theo nhóm
    - "classify_by_topic": Phân loại file theo 1 chủ đề
    - "scan": Quét thư mục và liệt kê file.
    - "export": Xuất metadata file
    - "general": Chức năng khác không liên quan đến các chức năng trên
    """

    # tạo fragement prompt để xác định intent bằng LLM
    fragment_prompt = f"""
    [INST]
    Dưới đây là bảng các chức năng được hỗ trợ:
    {intents_text}

    Yêu cầu của người dùng: "{prompt}"

    Hãy xác định câu trên thuộc chức năng nào.
    Chỉ trả về duy nhất một trong các từ khóa sau: search, classify, classify_by_topic, scan, export, other.

    Intent:
    [/INST]
    """

    # tìm intent từ fragment prompt
    intent = llm.create_chat_completion(
        messages=[{"role": "user", "content": fragment_prompt}],
        temperature=0.1,
        max_tokens=30,
        stop=["\n"],
    )

    # trả về intent
    intent = intent["choices"][0]["text"].strip()
    logger.info(f"Intent detected: {intent}")
    return intent, prompt

def clean_extracted_query(query: str) -> str:
    """Clean extracted search query"""
    if not query:
        return ""
    
    # Remove trailing words that are not part of search terms
    cleanup_suffixes = ['trong', 'ở', 'tại', 'không', 'nào', 'gì', 'đâu']
    words = query.split()
    
    # Remove suffix words
    while words and words[-1].lower() in cleanup_suffixes:
        words.pop()
    
    # Remove prefix words if they exist
    cleanup_prefixes = ['file', 'tài', 'liệu']
    while words and words[0].lower() in cleanup_prefixes:
        words.pop(0)
    
    result = ' '.join(words).strip()
    
    # Validate result has meaningful content
    if len(result) > 1 and any(c.isalnum() for c in result):
        return result
    
    return query.strip()  # Return original if cleaning failed

#===================== process_prompt =====================

def process_prompt(prompt: str) -> str:

    """Main prompt processing - preserve original context"""
    
    # Detect intent
    intent, original_prompt = detect_intent(prompt)
    
    # Process with MCP if available and not general chat
    if MCP_AVAILABLE and intent != 'general':
        try:
            # Call appropriate MCP function
            if intent == 'search':
                keyword = search_handler(original_prompt)
                mcp_result = process_filesystem_query(keyword, "search")
                logger.info(f"Search '{keyword}' returned: {mcp_result[:200]}...")
            elif intent == 'scan':
                #######activate this when upgrate to external path implementation
                # directory = scan_handler(original_prompt)
                directory = ""
                mcp_result = process_filesystem_query(directory, "scan")
                logger.info(f"Scan returned: {mcp_result[:200]}...")
            elif intent == 'classify':
                targets = classify_handler(original_prompt)
                mcp_files = process_filesystem_query("", "scan_all")
                mcp_result = generate_classify_result(mcp_files,targets)
                logger.info(f"Classify returned: {mcp_result[:200]}...")
            elif intent == 'export':
                mcp_result = process_filesystem_query("", "export")
                logger.info(f"Export returned: {mcp_result[:200]}...")
            elif intent == 'classify_by_topic':
                topic = classify_by_topic_handler(original_prompt)
                mcp_result = process_filesystem_query(topic, "classify_by_topic")
                logger.info(f"Classify by topic '{topic}' returned: {mcp_result[:200]}...")
            else:
                return generate_simple_response(original_prompt)
            
            # Format result using patterns (no LLM) - pass original prompt
            formatted_result = format_mcp_result(mcp_result, intent, original_prompt)
            logger.info(f"Formatted result: {formatted_result[:100]}...")
            return formatted_result
                
        except Exception as e:
            logger.error(f"MCP error: {e}")
            # Handle error with patterns (no LLM) - preserve context
            return handle_error_with_pattern(str(e), intent, original_prompt)
    else:    
        # Only use LLM for general chat - use original prompt
        return generate_simple_response(original_prompt)
   

def generate_simple_response(prompt: str) -> str:
    """Generate simple LLM response - only for general chat"""
    try:
        response = llm.create_chat_completion(
            messages=[
                {"role": "system", "content": "Bạn là trợ lý AI. Phản hồi tin nhắn của user."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=300,
            temperature=0.7,
            stop=["\n\n"]
        )
        
        content = response["choices"][0]["message"]["content"].strip()
        return content if content else "Xin lỗi, tôi không hiểu."
        
    except Exception as e:
        logger.error(f"LLM error: {e}")
        return f"Lỗi LLM: {str(e)}"

def handle_error_with_pattern(error: str, intent: str, original_prompt: str = '') -> str:
    """Handle errors using patterns - preserve context"""
    
    error_patterns = {
        'file not found': 'Không tìm thấy file hoặc thư mục',
        'permission denied': 'Không có quyền truy cập file',
        'connection': 'Lỗi kết nối MCP',
        'timeout': 'Hết thời gian chờ',
        'invalid': 'Dữ liệu không hợp lệ'
    }
    
    error_lower = error.lower()
    for pattern, vietnamese_msg in error_patterns.items():
        if pattern in error_lower:
            if intent == 'search':
                return f"Lỗi tìm kiếm: {vietnamese_msg}"
            elif intent == 'scan':
                return f"Lỗi quét thư mục: {vietnamese_msg}"
            elif intent == 'classify':
                return f"Lỗi phân loại: {vietnamese_msg}"
            elif intent == 'export':
                return f"Lỗi xuất file: {vietnamese_msg}"
    
    return f"Lỗi hệ thống: {error}"

 

# ===================== format_mcp_result =====================

def format_mcp_result(result: str, intent: str, query: str = '', original_prompt: str = '') -> str:
    """Format MCP result using patterns - improved detection"""
    
    if intent == 'search':
        if 'Không tìm thấy' in result or 'No files found' in result or not result.strip():
            return f"Không tìm thấy file nào với từ khóa '{query}'"
        
        # Clean and process the result for better presentation
        cleaned_result = clean_search_result(result, query)
        
        # Count files from cleaned result to ensure consistency
        file_count = count_files_in_text(cleaned_result)
        
        if file_count == 0:
            return f"Không có kết quả tìm kiếm cho '{query}'\n\nDữ liệu trả về:\n{result}"
        elif file_count == 1:
            return f"Tìm thấy 1 file với từ khóa '{query}':\n\n{cleaned_result}"
        else:
            return f"Tìm thấy {file_count} file với từ khóa '{query}':\n\n{cleaned_result}"
    
    elif intent == 'scan':
        # Check for successful scan - look for actual data instead of "success" word
        has_data = any(indicator in result for indicator in [
            'Nhóm', 'file', 'Filename:', 'Categories', '•', '-', 'đã được', 'Total'
        ])
        
        if has_data and len(result.strip()) > 10:
            # Count files by multiple methods
            file_count = 0
            
            # Method 1: Count by patterns
            file_patterns = [r'Filename:', r'• Nhóm.*?(\d+)\s+file', r'(\d+)\s+file']
            for pattern in file_patterns:
                matches = re.findall(pattern, result)
                if matches:
                    if pattern == r'Filename:':
                        file_count = len(matches)
                    else:
                        # Sum up numbers found
                        file_count = sum(int(match) if isinstance(match, str) and match.isdigit() 
                                       else int(match[0]) if isinstance(match, tuple) and match[0].isdigit() 
                                       else 0 for match in matches)
                    break
            
            return f"Quét thư mục hoàn thành\nTổng số file: {file_count}\n\n{result}"
        else:
            return f"Lỗi quét thư mục: {result}"
    
    elif intent == 'classify':
        # Check for classification data
        has_classification = any(indicator in result for indicator in [
            'Nhóm', 'Categories', 'phân loại', 'file', '•'
        ])
        
        if has_classification:
            return f"Phân loại file thành công:\n\n{result}"
        else:
            return f"Lỗi phân loại: {result}"
    
    elif intent == 'export':
        # Check if export was successful and has detailed data
        has_export_data = any(indicator in result for indicator in [
            'Filename:', 'File:', 'size:', 'bytes', 'Nhóm', 'metadata', '•', '-'
        ])
        
        if has_export_data and len(result.strip()) > 50:
            # Format detailed metadata export
            formatted_export = format_export_metadata(result)
            return f"Xuất metadata thành công\n\n{formatted_export}"
        elif 'success' in result.lower() or 'exported' in result.lower() or 'xuất' in result.lower():
            return f"Xuất metadata thành công\nDữ liệu đã sẵn sàng\n\n{result}"
        else:
            return f"Lỗi xuất metadata: {result}"
    
    return result

def count_files_in_text(text: str) -> int:
    """Count unique files in text - consistent with cleaning logic"""
    
    lines = text.strip().split('\n')
    unique_files = set()
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # Look for file entries (lines starting with • or -)
        if line.startswith('•') or line.startswith('-'):
            # Extract filename for counting
            filename_match = re.search(r'([^/\\]+\.(txt|pdf|docx|pptx|doc|ppt|xlsx|csv))', line, re.IGNORECASE)
            if filename_match:
                filename = filename_match.group(1).strip()
                unique_files.add(filename)
        # Also check lines that contain file extensions but don't start with • or -
        elif any(ext in line.lower() for ext in ['.txt', '.pdf', '.docx', '.pptx', '.doc', '.ppt', '.xlsx', '.csv']):
            filename_match = re.search(r'([^/\\]+\.(txt|pdf|docx|pptx|doc|ppt|xlsx|csv))', line, re.IGNORECASE)
            if filename_match:
                filename = filename_match.group(1).strip()
                unique_files.add(filename)
    
    return len(unique_files)

def clean_search_result(result: str, query: str) -> str:
    """Clean and improve search result presentation"""
    
    # Remove redundant title if exists
    lines = result.strip().split('\n')
    cleaned_lines = []
    
    seen_files = set()
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # Skip redundant title lines that contain the query and end with ':'
        if ("Tìm thấy" in line and query in line and line.endswith(':')) or \
           ("file có" in line and query in line and line.endswith(':')):
            continue
            
        # Skip lines that just repeat the search
        if line == f"Tìm thấy file có '{query}':":
            continue
        
        # Handle file entries (lines starting with • or -)
        if line.startswith('•') or line.startswith('-'):
            # Extract filename for duplicate detection
            filename_match = re.search(r'([^/\\]+\.(txt|pdf|docx|pptx|doc|ppt|xlsx|csv))', line, re.IGNORECASE)
            if filename_match:
                filename = filename_match.group(1).strip()
                if filename in seen_files:
                    continue  # Skip duplicate
                seen_files.add(filename)
        
        # Handle other lines that might contain file info
        elif any(ext in line.lower() for ext in ['.txt', '.pdf', '.docx', '.pptx', '.doc', '.ppt', '.xlsx', '.csv']):
            filename_match = re.search(r'([^/\\]+\.(txt|pdf|docx|pptx|doc|ppt|xlsx|csv))', line, re.IGNORECASE)
            if filename_match:
                filename = filename_match.group(1).strip()
                if filename in seen_files:
                    continue  # Skip duplicate
                seen_files.add(filename)
        
        cleaned_lines.append(line)
    
    return '\n'.join(cleaned_lines)

# =============================================================

#===================== LLM_Handler ============================
# handler tương ứng với intent, xử lý user_prompt tạo ra targets
# Target là mục tiêu mà MCP cần tìm kiếm, xử lý, phân loại, export 
# Target là từ khóa cần tìm kiếm trong tên file, content của file(search)
# Target là danh mục nhóm cần phân loại. (classify)
# Target là địa chỉ thư mục cần quét. Để trống nếu không có (scan)
# Target là file cần xuất metadata. (export)
# Target là từ khóa cần phân loại theo 1 chủ đề. (classify_by_topic)


def search_handler(prompt: str) -> str:
    """Search handler"""

    fragment_prompt = f"""
    [INST]
    Từ yêu cầu sau đây, hãy trích xuất **chính xác 1 từ khóa duy nhất** cần tìm kiếm trong file.

    Chỉ trả về duy nhất từ khóa đó (không cần JSON, không giải thích).

    Yêu cầu người dùng:
    "{prompt}"
    [/INST]
    """

    response = llm.create_chat_completion(
        messages=[{"role": "user", "content": fragment_prompt}],
        temperature=0.2,
        max_tokens=512,
        stop=["</s>"]
    )
    keyword = response["choices"][0]["message"]["content"].strip()
    logger.info(f"Search keyword: {keyword}")
    return keyword

def classify_handler(prompt: str) -> str:
    """Classify handler"""

    fragment_prompt = f"""
    [INST]
    Từ yêu cầu sau đây, hãy trích xuất các nhóm phân loại (classification targets) và mô tả của từng nhóm.

    Trả về kết quả dưới dạng JSON hợp lệ như sau:
    {{
        "classification_targets": {{
            "Tên nhóm 1": "Mô tả nhóm 1",
            "Tên nhóm 2": "Mô tả nhóm 2"
            ...
            "Tên nhóm n": "Mô tả nhóm n"
        }}
    }}

    Yêu cầu người dùng:
    "{prompt}"

    Chỉ trả về JSON, không thêm lời giải thích.
    [/INST]
    """

    response = llm.create_chat_completion(
        messages=[{"role": "user", "content": fragment_prompt}],
        temperature=0.2,
        max_tokens=512,
        stop=["</s>"]
    )

    targets = json.loads(response["choices"][0]["message"]["content"])["classification_targets"]
    logger.info(f"Classification targets: {targets}")
    return targets

def generate_classify_result(mcp_files: list, classification_targets: dict) -> dict:
    """Generate classify result using LLM"""
    file_info = [
        {
            "filename": f["filename"],
            "preview": f["content_preview"][:200] + "..." if len(f["content_preview"]) > 200 else f["content_preview"]
        }
        for f in mcp_files
    ]

    # Bước 2: Tạo prompt lấy kết quả
    fragment_prompt = f"""
        [INST]
        Dưới đây là các nhóm phân loại với mô tả chi tiết:
        {json.dumps(classification_targets, ensure_ascii=False, indent=2)}

        Và danh sách các file cần phân loại:
        {json.dumps(file_info, ensure_ascii=False, indent=2)}

        Hãy phân loại từng file vào **một nhóm phù hợp nhất**, dựa trên tên và nội dung xem trước (preview).
        Đưa kết quả vào vị trí tương ứng danh sách kết quả.
        Trả về kết quả dạng JSON hợp lệ:
        {{
            "classification_result": ["Tên nhóm", ..., "Tên nhóm"]
        }}
        Chỉ trả về JSON, không thêm lời giải thích.

        [/INST]
        """

    # Bước 3: Gửi prompt đến LLM
    response = llm.create_chat_completion(
        messages=[{"role": "user", "content": fragment_prompt}],
        temperature=0.2,
        max_tokens=1024,
        stop=["</s>"]
    )

    # Bước 4: Parse kết quả và gắn nhãn
    result = json.loads(response["choices"][0]["message"]["content"])
    group_labels = result["classification_result"]

    if len(group_labels) != len(mcp_files):
        raise ValueError("Số lượng nhóm trả về không khớp với số file.")

    for idx, label in enumerate(group_labels):
        mcp_files[idx]["label"] = label

    return mcp_files


def scan_handler(prompt: str) -> str:       
    """Scan handler"""
    Basepath = ""
    fragment_prompt = f"""
    [INST]
    Từ yêu cầu sau đây, hãy trích xuất đường dẫn thư mục cần quét.
    Yêu cầu người dùng:
    "{prompt}"
    Nếu không có đường dẫn thư mục cần quét, trả về ""
    [/INST]
    """
    response = llm.create_chat_completion(
        messages=[{"role": "user", "content": fragment_prompt}],
        temperature=0.2,
        max_tokens=512,
        stop=["</s>"]
    )
    directory = response["choices"][0]["message"]["content"].strip()
    logger.info(f"Scan directory: {directory}")
    return directory

def export_handler(prompt: str) -> str:
    """Export handler"""
    return prompt

def classify_by_topic_handler(prompt: str) -> str:
    """Classify by topic handler"""
    fragment_prompt = f"""
    [INST]
    Từ yêu cầu sau đây, hãy trích xuất **chính xác 1 từ khóa duy nhất của 1 chủ đề** cần phân loại.
    Yêu cầu người dùng:
    "{prompt}"
    [/INST]
    """
    response = llm.create_chat_completion(
        messages=[{"role": "user", "content": fragment_prompt}],
        temperature=0.2,
        max_tokens=512,
        stop=["</s>"]
    )
    topic = response["choices"][0]["message"]["content"].strip()
    logger.info(f"Classify by topic: {topic}")
    return topic