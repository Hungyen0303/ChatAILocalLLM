import gradio as gr
import pandas as pd
from llm_processor import process_prompt, process_prompt_alternative


#Nam thuận sửa phần này nha , xong thay vào hàm query ở dưới 
def process_query(query):
    results = [
        {"filename": "marketing_plan.pdf", "label": "Nhóm A"},
        {"filename": "sales_strategy.docx", "label": "Nhóm B"}
    ]
    df = pd.DataFrame(results)
    response = f"🔍 Đã tìm thấy {len(results)} tệp khớp với: '{query}'"
    return response, df


# Nam thuận
def chat_interface(query, filename=None, new_label=None):
    if filename and new_label:
        return update_label(filename, new_label), None
    response, df = process_query(query)
    return response, df


# Tấn sang sửa khúc này 
def update_label(filename, new_label):
    return f"✅ Đã cập nhật nhãn cho `{filename}` thành **{new_label}**"




# Nháp để query thử LLM 
def chat_interface2(query):
    """
    Xử lý câu hỏi từ người dùng và trả về phản hồi từ LLM.
    """
    if not query:
        return "Vui lòng nhập câu hỏi!"
    
    try:
        response = process_prompt(query)
    except:
        response = process_prompt_alternative(query)
    
    return response
# CSS tùy chỉnh giao diện
css = """
body {
    font-family: 'Segoe UI', sans-serif;
    background-color: #f4f6f8;
    color: #333;
}
.gradio-container {
    max-width: 850px;
    margin: auto;
    padding: 30px;
    background: #ffffff;
    border-radius: 16px;
    box-shadow: 0 8px 20px rgba(0,0,0,0.08);
}
#chat-input {
    border-radius: 12px;
    border: 1px solid #d0d7de;
    padding: 12px;
    font-size: 16px;
    background-color: #fefefe;
}
#result-table {
    background-color: #ffffff;
    border-radius: 12px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.05);
    font-size: 15px;
}
#submit-btn, #update-btn {
    background-color: #2563eb;
    color: white;
    border-radius: 8px;
    padding: 10px 24px;
    font-weight: 600;
    border: none;
    transition: background-color 0.3s ease;
}
#submit-btn:hover, #update-btn:hover {
    background-color: #1e40af;
}
"""

def run_ui():
    with gr.Blocks(theme=gr.themes.Soft(), css=css) as demo:
        gr.Markdown("## 🤖 Chat AI Tìm kiếm & Phân loại File")
        gr.Markdown("Nhập câu hỏi bên dưới để tìm kiếm file hoặc cập nhật nhãn cho tệp dữ liệu.")

        with gr.Column():
            with gr.Row():
                query_input = gr.Textbox(
                    label="🔎 Nhập câu hỏi",
                    placeholder="VD: Tìm file có từ khóa 'kế hoạch 2024'",
                    elem_id="chat-input"
                )
                submit_btn = gr.Button("Tìm kiếm", elem_id="submit-btn")

            output_text = gr.Textbox(label="📋 Kết quả", interactive=False)
            output_table = gr.DataFrame(label="📁 Danh sách tệp tìm được", elem_id="result-table", interactive=False)

        gr.Markdown("---")
        gr.Markdown("### 🛠️ Cập nhật nhãn cho tệp (RLHF)")

        with gr.Row():
            filename_input = gr.Textbox(label="Tên tệp", placeholder="VD: marketing_plan.pdf", elem_id="filename-input")
            label_input = gr.Textbox(label="Nhãn mới", placeholder="VD: Nhóm A", elem_id="label-input")
            update_btn = gr.Button("Cập nhật nhãn", elem_id="update-btn")

        submit_btn.click(
            fn=chat_interface2,
            inputs=[query_input],
            outputs=[output_text]
        )

        update_btn.click(
            fn=chat_interface,
            inputs=[query_input, filename_input, label_input],
            outputs=[output_text, output_table]
        )

        demo.launch()