import gradio as gr
import os
import logging
from agentic_ai import process_prompt_agent
from llm_processor import process_prompt

logger = logging.getLogger(__name__)

def chat_with_llm(message, history):
    """Simple chat interface with LLM"""
    try:
        # Process with simplified LLM processor
        history.append({"role": "user", "content": message})
        response = process_prompt_agent(message)
        
        # Add to history using messages format
        history.append({"role": "assistant", "content": response})
        
        return history, ""
        
    except Exception as e:
        logger.error(f"Chat error: {e}")
        error_msg = f"Lỗi xử lý: {str(e)}"
        history.append({"role": "user", "content": message})
        history.append({"role": "assistant", "content": error_msg})
        return history, ""

def create_interface():
    """Create modern and visually appealing Gradio interface"""
    
    # Custom CSS for modern look
    custom_css = """
    /* Main container styling */
    .gradio-container {
        max-width: 1200px !important;
        margin: 0 auto !important;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif !important;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
        min-height: 100vh !important;
    }
    
    /* Header styling */
    .header-section {
        background: rgba(255, 255, 255, 0.95) !important;
        padding: 30px !important;
        border-radius: 15px !important;
        margin: 20px 0 !important;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1) !important;
        backdrop-filter: blur(10px) !important;
        border: 1px solid rgba(255, 255, 255, 0.2) !important;
    }
    
    .header-section h1 {
        color: #2c3e50 !important;
        font-size: 2.5em !important;
        font-weight: 700 !important;
        margin-bottom: 10px !important;
        text-align: center !important;
    }
    
    .header-section p {
        color: #34495e !important;
        font-size: 1.2em !important;
        text-align: center !important;
        margin-bottom: 20px !important;
    }
    
    /* Features grid */
    .features-grid {
        display: grid !important;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)) !important;
        gap: 15px !important;
        margin-top: 20px !important;
    }
    
    .feature-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
        color: white !important;
        padding: 15px !important;
        border-radius: 10px !important;
        text-align: center !important;
        font-weight: 500 !important;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1) !important;
    }
    
    /* Chat container */
    .chat-container {
        background: rgba(255, 255, 255, 0.95) !important;
        border-radius: 15px !important;
        padding: 20px !important;
        margin: 20px 0 !important;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1) !important;
        backdrop-filter: blur(10px) !important;
        border: 1px solid rgba(255, 255, 255, 0.2) !important;
    }
    
    /* Chatbot styling */
    .chatbot {
        height: 500px !important;
        border-radius: 10px !important;
        border: 2px solid #e3f2fd !important;
        background: #fafafa !important;
    }
    
    /* Input section */
    .input-section {
        background: rgba(255, 255, 255, 0.95) !important;
        padding: 20px !important;
        border-radius: 15px !important;
        margin: 20px 0 !important;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1) !important;
    }
    
    /* Textbox styling */
    .textbox input {
        border-radius: 25px !important;
        border: 2px solid #e3f2fd !important;
        padding: 12px 20px !important;
        font-size: 16px !important;
        transition: all 0.3s ease !important;
    }
    
    .textbox input:focus {
        border-color: #667eea !important;
        box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1) !important;
        outline: none !important;
    }
    
    /* Button styling */
    .primary-btn {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
        border: none !important;
        border-radius: 25px !important;
        padding: 12px 30px !important;
        color: white !important;
        font-weight: 600 !important;
        font-size: 16px !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3) !important;
    }
    
    .primary-btn:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4) !important;
    }
    
    .secondary-btn {
        background: #95a5a6 !important;
        border: none !important;
        border-radius: 25px !important;
        padding: 10px 25px !important;
        color: white !important;
        font-weight: 500 !important;
        transition: all 0.3s ease !important;
    }
    
    .secondary-btn:hover {
        background: #7f8c8d !important;
        transform: translateY(-1px) !important;
    }
    
    /* Footer section */
    .footer-section {
        background: rgba(255, 255, 255, 0.9) !important;
        padding: 20px !important;
        border-radius: 15px !important;
        margin: 20px 0 !important;
        text-align: center !important;
        color: #7f8c8d !important;
    }
    
    /* Responsive design */
    @media (max-width: 768px) {
        .gradio-container {
            margin: 10px !important;
            max-width: 100% !important;
        }
        
        .header-section h1 {
            font-size: 2em !important;
        }
        
        .features-grid {
            grid-template-columns: 1fr !important;
        }
    }
    """
    
    with gr.Blocks(
        title="Chat AI Local LLM - Document Management",
        css=custom_css,
        theme=gr.themes.Soft()
    ) as demo:
        
        # Header Section
        with gr.Row(elem_classes=["header-section"]):
            gr.HTML("""
            <div>
                <h1>🤖 Document Management System</h1>
                <p><strong>Chat AI Local LLM với MCP Filesystem</strong></p>
                <div class="features-grid">
                    <div class="feature-card">Tìm kiếm thông minh</div>
                    <div class="feature-card">Quét thư mục tự động</div>
                    <div class="feature-card">Phân loại file</div>
                    <div class="feature-card">Xuất metadata</div>
                    <div class="feature-card">Chat tự nhiên</div>
                </div>
            </div>
            """)
        
        # Chat Section
        with gr.Row(elem_classes=["chat-container"]):
            with gr.Column():
                gr.Markdown("### 💬 Giao diện Chat")
                
                # Chat interface with messages format
                chatbot = gr.Chatbot(
                    label="",
                    elem_classes=["chatbot"],
                    show_label=False,
                    height=500,
                    type="messages",
                    placeholder="Chưa có tin nhắn nào. Hãy bắt đầu cuộc trò chuyện!"
                )
        
        # Input Section
        with gr.Row(elem_classes=["input-section"]):
            with gr.Column(scale=1):
                gr.Markdown("### ✏️ Nhập tin nhắn")
                
                with gr.Row():
                    msg = gr.Textbox(
                        label="",
                        placeholder="Nhập câu hỏi hoặc yêu cầu... (VD: tìm file python, quét thư mục)",
                        scale=4,
                        elem_classes=["textbox"],
                        show_label=False
                    )
                    submit_btn = gr.Button(
                        "📤 Gửi", 
                        scale=1, 
                        variant="primary",
                        elem_classes=["primary-btn"]
                    )
                
                with gr.Row():
                    gr.Examples(
                        examples=[
                            "Tìm file có từ python",
                            "Quét thư mục và hiển thị file",
                            "Phân loại tất cả file",
                            "Phân loại các file liên quan đến tài chính",
                            "Xuất metadata để backup",
                            "Có file nào về machine learning không?" , 
                            "Hãy so sánh hai file marketing-2024.docx và marketing-2025.docx",
                            "Tôi không muốn bạn gợi ý hay recommend trong câu trả lời cho những lần trả lời sau",
                        ],
                        inputs=msg,
                        label="💡 Ví dụ câu hỏi:"
                    )
                    
                    clear_btn = gr.Button(
                        "🗑️ Xóa lịch sử", 
                        elem_classes=["secondary-btn"]
                    )
        
        # Event handlers
        msg.submit(
            chat_with_llm,
            inputs=[msg, chatbot],
            outputs=[chatbot, msg]
        )
        
        submit_btn.click(
            chat_with_llm,
            inputs=[msg, chatbot],
            outputs=[chatbot, msg]
        )
        
        clear_btn.click(
            lambda: ([], ""),
            outputs=[chatbot, msg]
        )
        
        # Footer Section
        with gr.Row(elem_classes=["footer-section"]):
            gr.Markdown("""
            ---
            **🎯 Hướng dẫn sử dụng:**
            
            • **Tìm kiếm:** "tìm file python" hoặc "có file nào về AI"
            
            • **Quét thư mục:** "quét thư mục" hoặc "hiển thị danh sách file"
            
            • **Phân loại:** "phân loại file" hoặc "sắp xếp tài liệu"
            
            • **Xuất dữ liệu:** "xuất metadata" hoặc "backup file info"
            
            Hệ thống sẽ tự động phát hiện ý định và thực hiện yêu cầu của bạn! 🚀
            """)
    
    return demo

def run_ui():
    """Run the web interface"""
    logger.info("Starting web interface...")
    
    try:
        demo = create_interface()
        
        demo.launch(
            server_name="0.0.0.0",
            server_port=7860,
            share=False,
            show_error=True,
            quiet=False
        )
        
    except Exception as e:
        logger.error(f"Failed to start web interface: {e}")
        raise

if __name__ == "__main__":
    run_ui()