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

def detect_intent_and_extract(prompt: str) -> tuple:
    """Detect intent and extract data using patterns - preserve original prompt"""
    prompt_lower = prompt.lower().strip()
    
    # Enhanced search patterns with more variations
    search_patterns = [
        # Quoted search terms
        (r'tìm file.*?["\']([^"\']+)["\']', 'search'),
        (r'tìm.*?file.*?["\']([^"\']+)["\']', 'search'),
        (r'file.*?có.*?["\']([^"\']+)["\']', 'search'),
        (r'search.*?["\']([^"\']+)["\']', 'search'),
        
        # Natural language patterns
        (r'(?:tôi )?(?:cần )?(?:muốn )?tìm file\s+(.+?)(?:\s+trong|\s*$)', 'search'),
        (r'(?:tôi )?(?:cần )?(?:muốn )?tìm.*?file.*?(\w.+?)(?:\s+trong|\s*$)', 'search'),
        (r'(?:tôi )?(?:cần )?(?:muốn )?search.*?file.*?(\w.+?)(?:\s+trong|\s*$)', 'search'),
        (r'file.*?có.*?(\w.+?)(?:\s+không|\s*$)', 'search'),
        (r'có file.*?về\s+(.+?)(?:\s*$)', 'search'),
        (r'(?:tôi )?(?:cần )?tìm\s+(.+?)(?:\s+file|\s*$)', 'search'),
        
        # More flexible patterns
        (r'(?:tôi )?(?:cần )?(?:muốn )?(?:tìm|search|tim)\s+(?:file\s+)?(.+?)(?:\s+(?:trong|ở|tại)|\s*$)', 'search'),
    ]
    
    # Check search patterns first
    for pattern, intent in search_patterns:
        match = re.search(pattern, prompt_lower)
        if match:
            query = match.group(1).strip()
            # Clean up extracted query
            query = clean_extracted_query(query)
            if query and len(query) > 1:
                return intent, query, prompt  # Return original prompt too
    
    # Simple intent patterns
    if any(word in prompt_lower for word in ['quét', 'scan', 'liệt kê', 'hiển thị file', 'danh sách']):
        return 'scan', '', prompt
    
    if any(word in prompt_lower for word in ['phân loại', 'classify', 'nhóm', 'categorize', 'sắp xếp']):
        return 'classify', '', prompt
    
    if any(word in prompt_lower for word in ['xuất', 'export', 'metadata', 'gửi cloud']):
        return 'export', '', prompt
    
    # Fallback for search without clear patterns
    search_keywords = ['tìm', 'search', 'file', 'tài liệu', 'tim']
    if any(keyword in prompt_lower for keyword in search_keywords):
        # Extract search terms by removing common words
        stop_words = {'tôi', 'cần', 'muốn', 'tìm', 'tim', 'file', 'có', 'nào', 'kiếm', 'tài', 'liệu', 'về', 'trong', 'search', 'ở', 'tại'}
        words = [w for w in prompt.split() if w.lower() not in stop_words and len(w) > 1]
        if words:
            query = ' '.join(words[:5])  # Take first 5 meaningful words
            return 'search', query, prompt
    
    return 'general', '', prompt

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

def generate_simple_response(prompt: str) -> str:
    """Generate simple LLM response - only for general chat"""
    try:
        response = llm.create_chat_completion(
            messages=[
                {"role": "system", "content": "Bạn là trợ lý AI. Trả lời ngắn gọn."},
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

def process_prompt(prompt: str) -> str:
    """Main prompt processing - preserve original context"""
    
    # Detect intent and extract data using patterns - get original prompt back
    intent, query, original_prompt = detect_intent_and_extract(prompt)
    
    # Process with MCP if available and not general chat
    if MCP_AVAILABLE and intent != 'general':
        try:
            # Call appropriate MCP function
            if intent == 'search':
                mcp_result = process_filesystem_query(query, "search")
                logger.info(f"Search '{query}' returned: {mcp_result[:200]}...")
            elif intent == 'scan':
                mcp_result = process_filesystem_query("", "scan")
                logger.info(f"Scan returned: {mcp_result[:200]}...")
            elif intent == 'classify':
                mcp_result = process_filesystem_query("", "classify")
                logger.info(f"Classify returned: {mcp_result[:200]}...")
            elif intent == 'export':
                mcp_result = process_filesystem_query("", "export")
                logger.info(f"Export returned: {mcp_result[:200]}...")
            else:
                return generate_simple_response(original_prompt)
            
            # Format result using patterns (no LLM) - pass original prompt
            formatted_result = format_mcp_result(mcp_result, intent, query, original_prompt)
            logger.info(f"Formatted result: {formatted_result[:100]}...")
            return formatted_result
                
        except Exception as e:
            logger.error(f"MCP error: {e}")
            # Handle error with patterns (no LLM) - preserve context
            return handle_error_with_pattern(str(e), intent, original_prompt)
    
    # Only use LLM for general chat - use original prompt
    return generate_simple_response(original_prompt)