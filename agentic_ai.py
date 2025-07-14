from typing import Dict

from llama_cpp import List
from pyparsing import Any
from action_plan import ActionPlan, get_json_response
from function_result import FunctionResult
from llm_processor import MCP_AVAILABLE, classify_by_topic_handler, classify_handler, format_mcp_result, generate_classify_result, generate_simple_response, search_handler
from mcp_client import process_filesystem_query


class AgenticProcessor:
    def __init__(self):
        self.context_data = {}  # Lưu trữ dữ liệu giữa các bước
        self.execution_history = []  # Lịch sử thực hiện
        
    def execute_step(self, step: Dict[str, Any], step_index: int, prompt: str) -> FunctionResult:
        """Thực hiện một bước trong action plan"""
        intent = step.get('function', '')
        step_description = step.get('description', '')
        print(f"Executing step {step_index + 1}: {intent} - {step_description}")
        try:            
            if intent == 'search':
                return self._execute_search(prompt, step)
            elif intent == 'search_exactly':
                return self._execute_search_and_read(prompt, step)
            elif intent == 'scan':
                return self._execute_scan(prompt, step)
            elif intent == 'classify':
                return self._execute_classify(prompt, step)
            elif intent == 'export':
                return self._execute_export(prompt, step)
            elif intent == 'classify_by_topic':
                return self._execute_classify_by_topic(prompt, step)
            elif intent == 'learn':
                return self._execute_add_feedback(prompt, step)
            elif intent == 'general':
                print(f"Thực hiện tác vụ chung: {step_description}")
                data_context = ''
                for i in range(len(self.execution_history)):
                        output = self.execution_history[i].get('output', '')
                        data_context += f"Bước {i+1}: {output}\n"
                generate_info = generate_simple_response(f"Với prompt {prompt} Hãy thực hiện tác vụ này :{step_description} 'với data hiện có là '  {data_context}. prompt không liên quan tới data hiện có. Chỉ trả về kết quả của tác vụ này.")
                return FunctionResult(
                    success=True,
                    data= f"{step_description} \n {generate_info}"
                ) 

            else:
                return FunctionResult(
                    success=False,
                    error=f"Hành động: {step_description}"
                )
                
        except Exception as e:
            print(f"Error executing step {step_index + 1}: {e}")
            # Make a recommentation based on the error
            recommendation = generate_simple_response(
                f"Với prompt hiện tại là '{prompt}', hãy gợi ý một hành động thay thế hoặc giải pháp cho lỗi: {str(e)}"
            )
            return FunctionResult(
                success=False,
                error=str(e) + f"\nGợi ý: {recommendation}",
            )
    
    def _execute_search(self, prompt: str, step: Dict[str, Any]) -> FunctionResult:
        """Thực hiện search với xử lý lỗi"""
        try:
            keyword = search_handler(prompt)
            if not keyword:
                return FunctionResult(
                    success=False,
                    error="Không thể xác định từ khóa tìm kiếm",
                    missing_data=["search_keyword"]
                )
            print(f"Searching for keyword: {keyword}")
            
            mcp_result = process_filesystem_query(keyword, "search")
            formatted_result = format_mcp_result(mcp_result, 'search', prompt)
            self.context_data['search_results'] = mcp_result
            self.context_data['search_keyword'] = keyword
            
            return FunctionResult(
                success=True,
                data=formatted_result,
            )
            
        except Exception as e:
            return FunctionResult(
                success=False,
                error=f"Search failed: {str(e)}"
            )
    def _execute_search_and_read(self, prompt: str, step: Dict[str, Any]) -> FunctionResult:
        """Thực hiện scan với xử lý lỗi"""
        try:
            mcp_result = process_filesystem_query(step.get("required_data", "")[0], "search_exactly")
            self.context_data['search_exactly'] = mcp_result
            if mcp_result == "Không tìm thầy file":
                return FunctionResult(
                    success=False,
                    error=f"Không tìm thấy file {step.get('required_data', '')[0]}",
                    missing_data=[f"file {step.get('required_data', '')[0]}"]
                )
            return FunctionResult(
                success=True,
                data=mcp_result,
            )
            
        except Exception as e:
            return FunctionResult(
                success=False,
                error=f"Read failed: {str(e)}"
            )
    def _execute_scan(self, prompt: str, step: Dict[str, Any]) -> FunctionResult:
        """Thực hiện scan với xử lý lỗi"""
        try:
            # Có thể sử dụng dữ liệu từ bước trước
            directory = self.context_data.get('target_directory', "")
            mcp_result = process_filesystem_query(directory, "scan")
            formatted_result = format_mcp_result(mcp_result, 'scan', prompt)
            
            # Lưu kết quả vào context
            self.context_data['scan_results'] = mcp_result
            
            return FunctionResult(
                success=True,
                data=formatted_result,
            )
            
        except Exception as e:
            return FunctionResult(
                success=False,
                error=f"Scan failed: {str(e)}"
            )
    def _execute_classify(self, prompt: str, step: Dict[str, Any]) -> FunctionResult:
        """Thực hiện classify với xử lý lỗi"""
        try:
            
            # Sử dụng scan results từ bước trước nếu có
            mcp_files = process_filesystem_query("", "scan_all")
            if not mcp_files:
                return FunctionResult(
                    success=False,
                    error="Không tìm thấy files để phân loại",
                    missing_data=["file_list"]
                )
            print("here now go to classify")
            mcp_result = generate_classify_result(mcp_files)
            formatted_result = format_mcp_result(mcp_result, 'classify', prompt)
            self.context_data['classify_results'] = mcp_result
            
            return FunctionResult(
                success=True,
                data=formatted_result,
            )
            
        except Exception as e:
            print(f"Error during classification: {e}")
            return FunctionResult(
                success=False,
                error=f"Classification failed: {str(e)}"
            )
    
    def _execute_export(self, prompt: str, step: Dict[str, Any]) -> FunctionResult:
        """Thực hiện export với xử lý lỗi"""
        try:
            # Có thể sử dụng dữ liệu từ các bước trước
            # export_data = self.context_data.get('classify_results') or \
            #              self.context_data.get('scan_results') or \
            #              self.context_data.get('search_results')
            
            # if not export_data:
            #     return FunctionResult(
            #         success=False,
            #         error="Không có dữ liệu để xuất metadata",
            #         missing_data=["export_data"]
            #     )
            
            mcp_result = process_filesystem_query("", "export")
            formatted_result = "Xuất metadata thành công"
            
            return FunctionResult(
                success=True,
                data=formatted_result,
            )
            
        except Exception as e:
            return FunctionResult(
                success=False,
                error=f"Export failed: {str(e)}"
            )
    def _execute_add_feedback(self, prompt: str, step: Dict[str, Any]) -> FunctionResult:
        try:
            formatted_result = generate_simple_response(
                f"""
                [INST]

                Hãy trích xuất phản hồi từ người dùng, trích xuất nó ngắn gọn
                Và đây là phản hồi của người dùng: 
                {prompt}
                **LƯU Ý**:
                - Chỉ trả về duy nhất phản hồi của người dùng, không thêm bất kỳ văn bản nào khác.
                - Trả về ngắn gọn, súc tích, không giải thích hay mô tả thêm. 
                [INST]


                """
            )
            with open("user_feedback.txt", 'a', encoding='utf-8') as f:
                f.write(formatted_result + "\n")   
            return FunctionResult(
                success=True,
                data=formatted_result,
            )
            
        except Exception as e:
            return FunctionResult(
                success=False,
                error=f"Export failed: {str(e)}"
            )
    def _execute_classify_by_topic(self, prompt: str, step: Dict[str, Any]) -> FunctionResult:
        """Thực hiện classify by topic với xử lý lỗi"""
        try:
            topic = classify_by_topic_handler(prompt)
            
            if not topic:
                return FunctionResult(
                    success=False,
                    error="Không thể xác định chủ đề phân loại",
                    missing_data=["topic"]
                )
            print(f"Classifying by topic: {topic}")
            mcp_result = process_filesystem_query(topic, "classify_by_topic")
            formatted_result = format_mcp_result(mcp_result, 'classify_by_topic', prompt)
            
            # Lưu kết quả vào context
            self.context_data['classify_by_topic_results'] = mcp_result
            
            return FunctionResult(
                success=True,
                data=formatted_result,
            )
            
        except Exception as e:
            return FunctionResult(
                success=False,
                error=f"Classify by topic {topic}: {str(e)}"
            )
    
    def handle_step_failure(self, failed_result: FunctionResult, step_index: int, 
                           remaining_steps: List[Dict[str, Any]], prompt: str) -> str:
        """Xử lý khi một bước thất bại"""
        error_msg = f"❌ Bước {step_index + 1} thất bại: {failed_result.error}\n"
        
        # Kiểm tra xem có thể tiếp tục với dữ liệu hiện có không
        if failed_result.missing_data:
            error_msg += f"⚠️  Thiếu dữ liệu: {', '.join(failed_result.missing_data)}\n"
            
            # Thử tìm dữ liệu thay thế từ context
            if self._can_continue_with_context(failed_result.missing_data):
                error_msg += "🔄 Tìm thấy dữ liệu thay thế, tiếp tục xử lý...\n"
                return error_msg
        
        # Kiểm tra xem có thể bỏ qua bước này không
        if self._can_skip_step(step_index, remaining_steps):
            error_msg += "⏭️  Bỏ qua bước này và tiếp tục...\n"
            return error_msg
        
        # Nếu không thể tiếp tục, dừng xử lý
        error_msg += "🛑 Không thể tiếp tục, dừng xử lý.\n"
        return error_msg
    
    def _can_continue_with_context(self, missing_data: List[str]) -> bool:
        """Kiểm tra xem có thể tiếp tục với dữ liệu hiện có không"""
        for data_type in missing_data:
            if data_type == "search_keyword" and 'search_results' in self.context_data:
                return True
            if data_type == "file_list" and 'scan_results' in self.context_data:
                return True
            if data_type == "export_data" and any(key in self.context_data for key in 
                                                ['classify_results', 'scan_results', 'search_results']):
                return True
        return False
    
    def _can_skip_step(self, step_index: int, remaining_steps: List[Dict[str, Any]]) -> bool:
        """Kiểm tra xem có thể bỏ qua bước này không"""
        # Logic để quyết định có thể bỏ qua bước nào
        # Ví dụ: có thể bỏ qua search nếu đã có scan results
        if step_index < len(remaining_steps) - 1:  # Không phải bước cuối
            return True
        return False


processor = AgenticProcessor()

def make_recommendation(prompt: str ) -> str:
    """Tạo gợi ý hành động dựa trên prompt"""


    context = "Ngữ cảnh hiện tại là: " + str(processor.execution_history[-1].get('error', ''))
    system_prompt = f"""Bạn là một AI Assistant tạo kế hoạch hành động. Hãy gợi ý một hành động thay
    thế hoặc giải pháp cho người dùng dựa trên prompt sau: {prompt}
    Với ngữ cảnh hiện tại là: {context} 
    Gợi ý phải dựa trên bước thực hiện chưa thành công với isSuccess là False
    Hãy trả lời ngắn gọn bằng tiếng việt , ví dụ như
    "Tôi không tìm thấy file này, bạn hãy upload vào hoặc kiểm tra lại" hoặc "Thử phân loại lại theo chủ đề khác".
    """
    try:
        # Sử dụng LLM để tạo gợi ý
        recommendation = generate_simple_response(f"{system_prompt} ")
        return recommendation
    except Exception as e:
        print(f"Error generating recommendation: {e}")
        return "Không thể tạo gợi ý, vui lòng thử lại sau."

def process_prompt_agent(prompt: str) -> str:
    """
    Xử lý prompt như một agentic AI với khả năng xử lý lỗi và chuyển tiếp dữ liệu
    """
    try:
        # Lấy action plan từ prompt
        action_plan_data = get_json_response(prompt)
        
        # Kiểm tra xem có cần sử dụng MCP không
        if not MCP_AVAILABLE:
            print("MCP không khả dụng, sử dụng chế độ đơn giản...")
            return generate_simple_response(prompt)
        
        # Kiểm tra xem có steps nào cần xử lý không
        if not action_plan_data.steps or action_plan_data.steps[0].get('function') == 'general':
            print("Không có bước cụ thể, sử dụng chế độ đơn giản...")
            return generate_simple_response(prompt)
        
        # Khởi tạo processor
        final_result = ""

        final_result += f"🎯 Đang xử lý: {action_plan_data.task_description}\n\n"
        
        # Thực hiện từng bước
        for i, step in enumerate(action_plan_data.steps):
            step_result = processor.execute_step(step, i, prompt)
            
            if step_result.success:
                if len(step) > 1 : 
                    final_result += f"✅ Bước {i+1}: {step_result.data}\n"
                processor.execution_history.append({
                    'step': i+1,
                    'success': True,
                    'output': step_result.data
                })
            else:
                # Xử lý lỗi
                error_handling = processor.handle_step_failure(
                    step_result, i, action_plan_data.steps[i+1:], prompt
                )
                final_result += error_handling
                
                processor.execution_history.append({
                    'step': i+1,
                    'success': False,
                    'error': step_result.error
                })
                break
                if "🛑" in error_handling:
                    break
        
        if processor.execution_history[-1].get('success', '') == True:
            final_result += f"\n📋 Tóm tắt: Đã thực hiện {len(processor.execution_history)} bước"
            success_count = sum(1 for h in processor.execution_history if h['success'])
            final_result += f" ({success_count} thành công, {len(processor.execution_history) - success_count} thất bại)"
            if action_plan_data.recommendations != None  and action_plan_data.recommendations != "" and action_plan_data.recommendations != "[]": 
                final_result += f"\n💡 Gợi ý: {action_plan_data.recommendations}"
            processor.execution_history.clear()
            return final_result.strip()
        else : 
            return make_recommendation(prompt)
        
    except Exception as e:
        print(f"Critical error in process_prompt_agent: {e}")
        return f"❌ Lỗi nghiêm trọng: {str(e)}\n🔄 Chuyển sang chế độ đơn giản..."