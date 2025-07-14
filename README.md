
Thành viên 

Nguyễn Lâm Quế Anh - 20120428
Nguyễn Đình Nam Thuận - 21120339
Nguyễn Hưng Yên - 21120372
Trần Tấn Sang- 21120618



# Lưu Ý 2:  models -> rất nặng. Máy ai dưới 16Gb nhớ đọc Lưu ý 1.
            Nhớ đổi   n_threads= số core CPU,

# Document Management System - DoAnCNM

## Tổng quan

## Tính năng hiện tại

- **Quét thư mục tự động**: Index và phân loại file
- **Tìm kiếm thông minh**: Tìm kiếm theo nội dung và tên file
- **Phân loại tự động**: 5 nhóm phân loại (A-E)
- **Xuất metadata**: Chuẩn bị dữ liệu cho cloud storage
- **Giao diện chat**: Tương tác tự nhiên với AI
- **MCP Protocol**: Chuẩn giao tiếp Model Context Protocol

## Cấu trúc hệ thống

```
Root/
 ├──ChatAILocalLLM/
 ├   ├── main.py                 # Entry point chính
 ├   ├── ui.py                   # Giao diện UI
 ├   ├── llm_processor.py        # Liên kết & xử lý LLM với MCP server
 ├   ├── mcp_client.py          # MCP Filesystem client
 ├   ├── mcp_filesystem_server.py # MCP server 
 ├   ├── config.py              # Cấu hình hệ thống
 ├   ├── test_mcp.py           # Test và tạo dữ liệu mẫu
 ├   ├── requirements.txt       # Dependencies
 ├   └── test_files/           # Thư mục file mẫu
 ├
 └──models/   
```

## Cài đặt

### 1. Cài đặt dependencies
ChatAILocalLLM/> 
```bash
pip install -r requirements.txt
```

### 2. Tải model LLM
Root/>
```bash
python downloadModel.py
```

### 3. Tạo dữ liệu mẫu

### 4. Chạy hệ thống
Root/>
```bash
python main.py
```

## Sử dụng

### Giao diện Web
- Truy cập: `http://localhost:7860`
- **Chat Interface**: Tương tác tự nhiên với AI
- **Direct Actions**: Thực hiện chức năng trực tiếp
- **System Info**: Thông tin hệ thống

### Các lệnh chat
- "Quét thư mục" - Hiển thị tất cả file
- "Tìm file kế hoạch" - Tìm kiếm theo từ khóa
- "Phân loại file" - Xem phân loại
- "Xuất metadata" - Chuẩn bị cho cloud

## Phân loại file

| Nhóm | Mô tả | Từ khóa |
|------|-------|---------|
| A | Kế hoạch, chiến lược | kế hoạch, plan, chiến lược |
| B | Marketing, bán hàng | marketing, quảng cáo, sales |
| C | Báo cáo, thống kê | báo cáo, report, thống kê |
| D | Hướng dẫn, manual | hướng dẫn, guide, manual |
| E | Khác | Không thuộc nhóm trên |

## Cấu hình hệ thống

### Model LLM
- **Model**: Llama-3-8B-Instruct (Q3_K_M)
- **Context**: 1024 tokens
- **Max tokens**: 128
- **Temperature**: 0.1 (deterministic)

### File hỗ trợ
- PDF, DOCX, PPTX, TXT
- Trích xuất nội dung tự động
- Preview nội dung trong kết quả

## API MCP

### Scan Directory
```python
fs_manager.scan_files(directory)
```

### Search Files
```python
fs_manager.search_files(query)
```

### Classify Files
```python
fs_manager.classify_files(category)
```

### Export Metadata
```python
fs_manager.export_metadata()
```

## Logs và Debug

### System logs
- `system.log` - Log hệ thống chính
- Console output - Real-time status

### Error handling
- Graceful degradation
- Alternative processing methods
- Comprehensive error logging

## Performance

### Tối ưu hóa
- Context ngắn (1024 vs 4096)
- Tokens giới hạn (128 vs 512)
- Temperature thấp (0.1 vs 0.7)
- Efficient pattern matching

### Benchmark
- Scan directory: ~2-5s
- Search files: ~1-3s
- LLM response: ~2-5s

## Troubleshooting

### Model không tải được
```bash
# Kiểm tra đường dẫn model
python -c "from config import get_model_path; print(get_model_path())"

# Tải lại model
python downloadModel.py
```

### MCP không hoạt động
```bash
# Test MCP client
python test_mcp.py
```

### Dependencies thiếu
```bash
pip install -r requirements.txt --upgrade
```

## Kiến trúc kỹ thuật

### MCP Protocol
- Client-Server architecture
- JSON-RPC communication
- Modular design

### LLM Integration
- llama-cpp-python
- Chat completion format
- Optimized parameters

### UI Framework
- Gradio web interface
- Responsive design
- Professional styling

## Đóng góp

1. Fork repository
2. Tạo feature branch
3. Commit changes
4. Submit pull request

## License

Academic project - Educational use only

## Liên hệ

DoAnCNM - Document Management System
Chat AI Local LLM với MCP Filesystem 
