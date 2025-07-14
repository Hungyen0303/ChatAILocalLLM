import json
import re
from typing import Dict

from attr import dataclass
from helper import extract_json_from_text
from llm_processor import llm
from llama_cpp import Any, List, Optional

@dataclass
class ActionPlan:
    task_description: str = ""
    steps: List[Dict[str, Any]] = None
    expected_output: str = ""
    recommendations: Optional[str] = None
    def __init__(self, json_data: Dict[str, Any]):
        self.task_description: str = json_data.get("task_description", "")
        self.steps: List[Dict[str, Any]] = json_data.get("steps", [])
        self.expected_output: str = json_data.get("expected_output", "")
        self.recommendations: Optional[str] = json_data.get("recommendations", None)

    def __str__(self):
        result = f"📌 Task: {self.task_description}\n"
        for step in self.steps:
            result += (
                f"👉 Bước {step.get('step')}: {step.get('description')} "
                f"({step.get('function')})\n"
            )
        result += f"🎯 Kết quả mong đợi: {self.expected_output}"
        return result
def get_user_feedback() -> str:
    try:
        with open("user_feedback.txt", "r", encoding="utf-8") as f:
            feedback = f.read().strip()
            if feedback:
                return feedback
    except FileNotFoundError:
        print("⚠️ Không tìm thấy file user_feedback.txt")
    return ""
def get_prompt(user_input: str) -> str:
    user_feedback = get_user_feedback()
    return f"""
[INST]
Bạn là một AI Assistant tạo kế hoạch hành động. Trả về **chỉ một JSON object**, không thêm bất kỳ văn bản, giải thích, markdown, hay ký tự nào ngoài JSON.

**QUY TẮC**:
- JSON phải bắt đầu bằng {{ và kết thúc bằng }}
- Không thêm dòng trống, comment, hoặc bất kỳ nội dung nào ngoài JSON
- Nếu hành động không thuộc danh sách FUNCTIONS, sử dụng "general"
- "general" luôn là bước cuối cùng (nếu cần thiết , nếu function có đáp ứng đủ thì không cần bước này)
- Nếu tồn tại các bước classify_by_topic hoặc classify, không cần bước search
- Mỗi bước phải có: step (số), description (mô tả), function (tên hàm), parameters (object, có thể rỗng), required_data (array)
- Chỉ sử dụng các hàm do người dùng yêu cầu, không tự động thêm bước nào khác. 
- Bắt buộc tuân theo user feedback với {user_feedback} , nếu rỗng thì có thể bỏ qua

**FUNCTIONS CÓ SẴN**:
- scan: Quét nội dung file để lấy thông tin chi tiết
- read: Đọc nội dung file
- write: Ghi/tạo file mới
- classify: Yêu cầu Phân loại tất cả file theo nội dung hoặc metadata, không được thêm bước search
- classify_by_topic : Phân loại file theo chủ đề, không được thêm bước search
- search_exactly: Tìm kiếm file theo tên chính xác ví dụ như so sánh hai file , tóm tắt nội dung file
- search:  nếu có classify_by_topic hoặc classify thì không tuyệt đối không thêm bước này. Chức năng :  Tìm kiếm file theo tên hoặc nội dung, 
- export : Xuất dữ liệu , meta ra định dạng
- learn : Khi người dùngcung cấp phản hồi, sử dụng hàm này để ghi lại phản hồi đó , hoặc khi người dùng muốn hệ thống nhớ rules của câu trả lời. Hoặc người dùng muốn mình ghi nhớ quy tác trả lời 
**search_exactly**: 
- Dùng khi cần TÌM FILE CỤ THỂ theo tên
- Trigger words: "file [tên]", "so sánh [file1] và [file2]", "tóm tắt [filename]"
- Ví dụ: "so sánh marketing 2024 và 2025", "đọc file budget.xlsx"
- Với required_data cho function này : Danh sách các file cần thiết để thực hiện bước này, ví dụ ["marketing-2024.docx"]
**search**: 
- Dùng khi tìm kiếm theo NỘI DUNG/chủ đề
- Trigger words: "tìm", "search", "có file nào", "file về"
- Ví dụ: "tìm file về marketing", "có file nào nói về budget"
**TRIGGER WORDS**:
- learn: "lần sau", "đừng", "không cần", "thay đổi cách", "tôi muốn bạn", "nhớ rằng", "từ giờ", "phản hồi"
- search_exactly: "file [tên]", "so sánh [file1] và [file2]", "tóm tắt [filename]"
- search: "tìm", "search", "có file nào", "file về"
**Quy tắc ưu tiên:**
1. Nếu có tên file cụ thể → search_exactly
2. Nếu có từ khóa chung → search
3. Nếu đã có classify/classify_by_topic → KHÔNG cần search
JSON **bắt buộc phải có đầy đủ các trường sau**:
task_description: mô tả ngắn gọn yêu cầu người dùng
steps: danh sách các bước hành động theo yêu cầu
expected_output: kết quả đầu ra mà người dùng mong muốn
recommendations: gợi ý thêm các chức năng hoặc hành động hữu ích 
Bắt buộc phải trả đủ ngoặc đóng và không có lỗi cú pháp JSON.
**VÍ DỤ learn**:
- "Lần sau không cần chào tôi đâu" → learn
- "Lần sau không cần đưa ra gợi ý" → learn  
- "Nhớ rằng tôi không thích..." → learn
**VÍ DỤ**:
Yêu cầu: So sánh file marketing 2024 và 2025
{{
  "task_description": "So sánh file marketing 2024 và 2025",
  "steps": [
    {{
      "step": 1,
      "description": "Tìm file marketing 2024",
      "function": "search",
      "parameters": {{"query": "marketing 2024"}},
      "required_data": ["file marketing 2024"]
    }},
    {{
      "step": 2,
      "description": "Tìm file marketing 2025",
      "function": "search",
      "parameters": {{"query": "marketing 2025"}},
      "required_data": ["file marketing 2025"]
    }},
    {{
      "step": 3,
      "description": "So sánh nội dung hai file",
      "function": "general",
      "parameters": {{}},
      "required_data": ["so sánh chi tiết"]
    }}
  ],
  "expected_output": "Báo cáo so sánh marketing 2024 vs 2025",
  "recommendations": "Bạn có thể thêm bước phân loại file theo chủ đề nếu cần thiết.",
}}

**Yêu cầu người dùng**:
"{user_input}"

**JSON Output**:
[/INST]
"""

def get_json_response(user_input: str, max_retries: int = 3) -> Optional[ActionPlan]:
    prompt = get_prompt_english(user_input)
    
    for attempt in range(max_retries):
        try:
            output = llm.create_chat_completion(
                messages=[{"role": "user", "content": prompt}],
                max_tokens=4096,
                temperature=0.0,
            )
            
            raw_output = output["choices"][0]["message"]["content"]
            print(f"raw_output: {raw_output}")
            json_text = extract_json_from_text(raw_output)
            if json_text:
                parsed = json.loads(json_text)
                action_plan =  ActionPlan(**parsed)
                return action_plan
            else:
                print(f"⚠️ Thử {attempt + 1}/{max_retries}: Không tìm thấy JSON hợp lệ")
                
        except Exception as e:
            print(f"⚠️ Thử {attempt + 1}/{max_retries}: Lỗi - {e}")
            
    return None

# Hàm fallback
def fallback_json_response(user_input: str) -> Optional[ActionPlan]:
    simple_prompt = f"""
[INST]
Trả về **chỉ một JSON object** cho kế hoạch hành động dựa trên yêu cầu: "{user_input}".
Không thêm văn bản, giải thích, hoặc markdown. JSON phải bắt đầu bằng {{ và kết thúc bằng }}.
Ví dụ: {{"task_description": "Ví dụ", "steps": [], "expected_output": "Kết quả"}}
[/INST]
"""
    try:
        output = llm.create_chat_completion(
            messages=[{"role": "user", "content": simple_prompt}],
            max_tokens=512,
            temperature=0.0,
        )
        
        raw_output = output["choices"][0]["message"]["content"]
        json_text = extract_json_from_text(raw_output)
        
        if json_text:
            parsed = json.loads(json_text)
            return ActionPlan(parsed)
        return None
    except Exception as e:
        print(f"❌ Fallback error: {e}")
        return None
    




def get_prompt_2(user_input: str) -> str:
    user_feedback = get_user_feedback()
    print(f"User feedback: {user_feedback}")
    return f"""
[INST]
Bạn là AI Assistant tạo kế hoạch hành động. Trả về **chỉ JSON object**, không thêm văn bản, giải thích, markdown nào khác.

**QUY TẮC JSON**:
- Bắt đầu {{ kết thúc }}
- Không dòng trống, comment, nội dung ngoài JSON
- Mỗi bước: step (số), description (mô tả), function (tên hàm), parameters (object), required_data (array)
- Tuân theo user feedback: {user_feedback}
- "general" chỉ dùng khi cần thiết và là bước cuối

**FUNCTIONS**:
- scan: Quét nội dung file chi tiết
- read: Đọc nội dung file  
- write: Ghi/tạo file mới
- classify: Phân loại file theo nội dung/metadata (không cần search)
- classify_by_topic: Phân loại file theo chủ đề (không cần search)
- search_exactly: Tìm file theo tên chính xác
- search: Tìm file theo nội dung/chủ đề (không dùng nếu có classify)
- export: Xuất dữ liệu ra định dạng
- feedback: Ghi lại phản hồi/yêu cầu thay đổi cách trả lời của người dùng
**ƯU TIÊN**:
1. Feedback/yêu cầu thay đổi → feedback
2. Tên file cụ thể → search_exactly
3. Từ khóa chung → search  
4. Có classify/classify_by_topic → KHÔNG search

**TRIGGER WORDS**:
- feedback: "lần sau", "đừng", "không cần", "thay đổi cách", "tôi muốn bạn", "nhớ rằng", "từ giờ", "phản hồi"
- search_exactly: "file [tên]", "so sánh [file1] và [file2]", "tóm tắt [filename]"
- search: "tìm", "search", "có file nào", "file về"

**JSON FIELDS**:
- task_description: Mô tả ngắn gọn yêu cầu
- steps: Danh sách bước hành động
- expected_output: Kết quả mong muốn
- recommendations: Gợi ý thêm chức năng hữu ích

**VÍ DỤ FEEDBACK**:
- "Lần sau không cần chào tôi đâu" → feedback
- "Tôi muốn bạn trả lời ngắn gọn hơn" → feedback  
- "Nhớ rằng tôi không thích..." → feedback

**VÍ DỤ**:
{{
  "task_description": "So sánh file marketing 2024 và 2025",
  "steps": [
    {{
      "step": 1,
      "description": "Tìm file marketing 2024",
      "function": "search",
      "parameters": {{"query": "marketing 2024"}},
      "required_data": ["file marketing 2024"]
    }},
    {{
      "step": 2,
      "description": "Tìm file marketing 2025", 
      "function": "search",
      "parameters": {{"query": "marketing 2025"}},
      "required_data": ["file marketing 2025"]
    }},
    {{
      "step": 3,
      "description": "So sánh nội dung hai file",
      "function": "general",
      "parameters": {{}},
      "required_data": ["so sánh chi tiết"]
    }}
  ],
  "expected_output": "Báo cáo so sánh marketing 2024 vs 2025",
  "recommendations": "Có thể thêm phân loại file theo chủ đề nếu cần thiết"
}}

**Yêu cầu**: "{user_input}"

**JSON**:
[/INST]
"""



def get_prompt_english(user_input: str) -> str:
    user_feedback = get_user_feedback()
    return f"""
[INST]
You are an AI Assistant that creates action plans. Return **only a JSON object**, do not add any text, explanation, markdown, or any characters other than JSON.

**RULES**:
- JSON must start with {{ and end with }}
- Do not add blank lines, comments, or any content other than JSON
- If action is not in the FUNCTIONS list, use "general"
- "general" is always the last step (if necessary, if function is sufficient then this step is not needed)
- If classify_by_topic or classify steps exist, do not add search step
- Each step must have: step (number), description (Vietnamese description), function (function name), parameters (object, can be empty), required_data (array)
- Only use functions as requested by user, do not automatically add other steps
- Must follow user feedback with {user_feedback}, if empty then can ignore

**AVAILABLE FUNCTIONS**:
- scan: Scan file content to get detailed information
- read: Read file content
- write: Write/create new file
- classify: Required to classify all files by content or metadata, must not add search step
- classify_by_topic: Classify files by topic, must not add search step
- search_exactly: Search for files by exact name, for example comparing two files, summarizing file content
- search: if classify_by_topic or classify exists then absolutely do not add this step. Function: Search files by name or content
- export: Export data, metadata to format
- learn: When user provides feedback, use this function to record that feedback, or when user wants system to remember answer rules, or when user wants to remember response rules

**search_exactly**: 
- Use when need to FIND SPECIFIC FILES by name
- Trigger words: "file [name]", "compare [file1] and [file2]", "summarize [filename]"
- Examples: "compare marketing 2024 and 2025", "read file budget.xlsx"
- With required_data for this function: List of files needed to perform this step, example ["marketing-2024.docx"]

**search**: 
- Use when searching by CONTENT/topic
- Trigger words: "find", "search", "any file", "file about"
- Examples: "find file about marketing", "any file talking about budget"

**TRIGGER WORDS**:
- learn: "next time", "don't", "no need", "change the way", "I want you", "remember that", "from now", "feedback"
- search_exactly: "file [name]", "compare [file1] and [file2]", "summarize [filename]"
- search: "find", "search", "any file", "file about"

**Priority rules:**
1. If there is specific file name → search_exactly
2. If there are general keywords → search
3. If already have classify/classify_by_topic → DO NOT need search

JSON **must have all the following fields**:
task_description: brief description of user request (in Vietnamese)
steps: list of action steps as requested (descriptions in Vietnamese)
expected_output: output result user expects (in Vietnamese)
recommendations: suggestions for additional useful functions or actions (in Vietnamese)

Must return complete closing brackets and no JSON syntax errors.

**learn EXAMPLES**:
- "Next time no need to greet me" → learn
- "Next time no need to give suggestions" → learn  
- "Remember that I don't like..." → learn

**EXAMPLE**:
Request: Compare marketing 2024 and 2025 files
{{
  "task_description": "So sánh file marketing 2024 và 2025",
  "steps": [
    {{
      "step": 1,
      "description": "Tìm file marketing 2024",
      "function": "search",
      "parameters": {{"query": "marketing 2024"}},
      "required_data": ["file marketing 2024"]
    }},
    {{
      "step": 2,
      "description": "Tìm file marketing 2025",
      "function": "search",
      "parameters": {{"query": "marketing 2025"}},
      "required_data": ["file marketing 2025"]
    }},
    {{
      "step": 3,
      "description": "So sánh nội dung hai file",
      "function": "general",
      "parameters": {{}},
      "required_data": ["so sánh chi tiết"]
    }}
  ],
  "expected_output": "Báo cáo so sánh marketing 2024 vs 2025",
  "recommendations": "Bạn có thể thêm bước phân loại file theo chủ đề nếu cần thiết"
}}

**User request**:
"{user_input}"

**JSON Output**:
[/INST]
"""