import json
import re
from llama_cpp import Optional


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