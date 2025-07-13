import json
import re
from typing import Dict

from attr import dataclass
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
    
def get_prompt(user_input: str) -> str:
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
- 
**FUNCTIONS CÓ SẴN**:
- scan: Quét nội dung file để lấy thông tin chi tiết
- read: Đọc nội dung file
- write: Ghi/tạo file mới
- classify: Yêu cầu Phân loại tất cả file theo nội dung hoặc metadata 
- classify_by_topic : Phân loại file theo chủ đề
- search: Tìm kiếm file theo tên hoặc nội dung, chỉ thực hiện khi người dùng yêu cầu và có từ khóa rõ ràng, nếu có classify_by_topic hoặc classify thì không cần bước này
- export : Xuất dữ liệu , meta ra định dạng
- general: Thực hiện các tác vụ chung khác
JSON **bắt buộc phải có đầy đủ các trường sau**:
task_description: mô tả ngắn gọn yêu cầu người dùng
steps: danh sách các bước hành động theo yêu cầu
expected_output: kết quả đầu ra mà người dùng mong muốn
recommendations: gợi ý thêm các chức năng hoặc hành động hữu ích 
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
  "recommendations": "Bạn có thể thêm bước phân loại file theo chủ đề nếu cần thiết."
}}

**Yêu cầu người dùng**:
"{user_input}"

**JSON Output**:
[/INST]
"""
def extract_json_from_text(text: str) -> Optional[str]:
    json_pattern = r'\{[\s\S]*\}'
    match = re.search(json_pattern, text, re.DOTALL)
    
    if not match:
        return None
    
    json_str = match.group(0)
    json_str = json_str.strip()
    if json_str.startswith("```json"):
        json_str = json_str[7:].rstrip("```").strip()
    
    try:
        json.loads(json_str)
        return json_str
    except json.JSONDecodeError:
        return None
def get_json_response(user_input: str, max_retries: int = 3) -> Optional[ActionPlan]:
    prompt = get_prompt(user_input)
    
    for attempt in range(max_retries):
        try:
            output = llm.create_chat_completion(
                messages=[{"role": "user", "content": prompt}],
                max_tokens=2048,
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
    

