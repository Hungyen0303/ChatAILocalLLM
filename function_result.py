from dataclasses import dataclass
from llama_cpp import List
from pyparsing import Any
@dataclass
class FunctionResult:
    """Kết quả từ việc thực hiện function"""
    success: bool
    data: Any = None
    error: str = None
    missing_data: List[str] = None