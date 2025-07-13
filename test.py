from dataclasses import dataclass
from typing import Any, List, Dict
import json

@dataclass
class ActionPlan:
    task_description: str = ""
    steps: List[Dict[str, Any]] = None
    expected_output: str = ""

    def __str__(self):
        result = f"📌 Task: {self.task_description}\n"
        for step in self.steps:
            result += (
                f"👉 Bước {step.get('step')}: {step.get('description')} "
                f"({step.get('function')})\n"
            )
        result += f"🎯 Kết quả mong đợi: {self.expected_output}"
        return result

# Dữ liệu JSON
jsonTest = '''
{
  "task_description": "Tìm file có từ python",
  "steps": [
    {
      "step": 1,
      "description": "Tìm file có từ python",
      "function": "search",
      "parameters": {"query": "python"},
      "required_data": ["file có từ python"]
    },
    {
      "step": 2,
      "description": "General",
      "function": "general",
      "parameters": {},
      "required_data": []
    }
  ],
  "expected_output": "Danh sách file có từ python"
}
'''

# Tạo đối tượng ActionPlan
data = json.loads(jsonTest)
actionPlan = ActionPlan(**data)

# In kết quả
print("Task Description:", actionPlan.task_description)
print(actionPlan)