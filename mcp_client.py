#!/usr/bin/env python3
"""
MCP Client
Kết nối với MCP Filesystem Server từ ứng dụng Chat AI
"""
import requests
import json
import subprocess
import sys
from typing import Dict, List, Any, Optional
import logging
from config import CONTENT_PREVIEW_LIMIT

logger = logging.getLogger(__name__)

class MCPFilesystemClient:
    """Client để giao tiếp với MCP Filesystem Server"""
    
    def __init__(self):
        self.server_process = None
        self.is_connected = False
    
    async def start_server(self):
        """Khởi động MCP server"""
        try:
            # Chạy MCP server như một subprocess
            self.server_process = subprocess.Popen(
                [sys.executable, "mcp_filesystem_server.py"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                stdin=subprocess.PIPE,
                text=True
            )
            self.is_connected = True
            logger.info("MCP Filesystem Server đã khởi động")
            return True
        except Exception as e:
            logger.error(f"Lỗi khởi động MCP server: {e}")
            return False
    
    async def stop_server(self):
        """Dừng MCP server"""
        if self.server_process:
            self.server_process.terminate()
            self.server_process.wait()
            self.is_connected = False
            logger.info("MCP Filesystem Server đã dừng")
    
    async def send_command(self, command: str, params: Dict = None) -> Dict:
        """Gửi lệnh đến MCP server"""
        if not self.is_connected:
            return {"error": "MCP server chưa kết nối"}
        
        try:
            # Tạo JSON-RPC request
            request = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": command,
                "params": params or {}
            }
            
            # Gửi request (đây là ví dụ đơn giản, thực tế cần implement JSON-RPC đầy đủ)
            request_str = json.dumps(request) + "\n"
            
            if self.server_process and self.server_process.stdin:
                self.server_process.stdin.write(request_str)
                self.server_process.stdin.flush()
                
                # Đọc response
                response_str = self.server_process.stdout.readline()
                if response_str:
                    return json.loads(response_str)
            
            return {"error": "Không thể gửi lệnh"}
            
        except Exception as e:
            logger.error(f"Lỗi gửi lệnh MCP: {e}")
            return {"error": str(e)}

# Khởi tạo MCP client global
mcp_filesystem_client = MCPFilesystemClient()

class FilesystemManager:
    """Wrapper class để sử dụng dễ dàng từ ứng dụng chính"""
    
    def __init__(self):
        self.client = mcp_filesystem_client
    
    async def initialize(self):
        """Khởi tạo filesystem manager"""
        return await self.client.start_server()
    
    async def shutdown(self):
        """Tắt filesystem manager"""
        await self.client.stop_server()
    
    def scan_files(self, directory: str = ".") -> Dict:
        """Quét và index file trong thư mục"""
        try:
            # Import local filesystem indexer để chạy đồng bộ
            from mcp_filesystem_server import file_indexer
            from pathlib import Path
            
            files = file_indexer.scan_directory(Path(directory))
            
            result = {
                "success": True,
                "message": f"Đã quét và index {len(files)} file",
                "files": [
                    {
                        "filename": f.filename,
                        "label": f.label,
                        "size": f.size,
                        "type": f.file_type,
                        "content_preview": f.content_preview[:CONTENT_PREVIEW_LIMIT] + "..." if len(f.content_preview) > CONTENT_PREVIEW_LIMIT else f.content_preview
                    } for f in files
                ],
                "total": len(files)
            }
            
            logger.info(f"Filesystem scan complete: {len(files)} files indexed")
            return result
            
        except Exception as e:
            logger.error(f"Lỗi quét file: {e}")
            return {
                "success": False,
                "error": str(e),
                "files": [],
                "total": 0
            }
    
    def search_files(self, query: str) -> Dict:
        """Tìm kiếm file theo từ khóa"""
        try:
            from mcp_filesystem_server import file_indexer
            
            results = file_indexer.search_files(query)
            
            result = {
                "success": True,
                "query": query,
                "found": len(results),
                "files": [
                    {
                        "filename": f.filename,
                        "filepath": f.filepath,
                        "label": f.label,
                        "type": f.file_type,
                        "size": f.size,
                        "content_preview": f.content_preview[:CONTENT_PREVIEW_LIMIT] + "..." if len(f.content_preview) > CONTENT_PREVIEW_LIMIT else f.content_preview
                    } for f in results
                ]
            }
            
            logger.info(f"Search complete: {len(results)} files found for '{query}'")
            return result
            
        except Exception as e:
            logger.error(f"Lỗi tìm kiếm: {e}")
            return {
                "success": False,
                "error": str(e),
                "query": query,
                "found": 0,
                "files": []
            }
    
    def export_metadata(self) -> Dict:
        """Xuất metadata để gửi MCP Cloud"""
        try:
            from mcp_filesystem_server import file_indexer
            
            files = list(file_indexer.file_index.values())
            url = "http://localhost:8000/upload-metadata"

            for f in files:
                data = {
                    "filename": f.filename,
                    "label": f.label,
                    "content": getattr(f, "content", ""),
                    "timestamp": getattr(f, "timestamp", None),
                }

                try:
                    print(f"Đang gửi metadata cho file: {f.filename}")
                    response = requests.post(url, json=data)
                    response.raise_for_status()
                    print(f"✅ Gửi thành công metadata cho file: {f.filename}")
                except requests.exceptions.RequestException as e:
                    print(f"❌ Gửi metadata thất bại cho file: {f.filename} — {e}")

            
            result = {
                "success": True,
                "total_files": len(files),
            }
            
            logger.info(f"Metadata export complete: {len(files)} files")
            return result
            
        except Exception as e:
            logger.error(f"Lỗi xuất metadata: {e}")
            return {
                "success": False,
                "error": str(e),
                "metadata": [],
                "total_files": 0
            }
    
    def get_file_info(self, filepath: str) -> Dict:
        """Lấy thông tin chi tiết của file"""
        try:
            from mcp_filesystem_server import file_indexer
            
            metadata = file_indexer.file_index.get(filepath)
            if metadata:
                result = {
                    "success": True,
                    "file": {
                        "filename": metadata.filename,
                        "filepath": metadata.filepath,
                        "type": metadata.file_type,
                        "size": metadata.size,
                        "label": metadata.label,
                        "content_preview": metadata.content_preview,
                        "created_time": metadata.created_time,
                        "modified_time": metadata.modified_time
                    }
                }
                logger.info(f"File info retrieved: {metadata.filename}")
                return result
            else:
                return {
                    "success": False,
                    "error": f"Không tìm thấy file: {filepath}",
                    "file": None
                }
                
        except Exception as e:
            logger.error(f"Lỗi lấy thông tin file: {e}")
            return {
                "success": False,
                "error": str(e),
                "file": None
            }
    
    def classify_files_by_topic(self, topic: str) -> Dict:
        """Gán label cho từng file, sau đó gom nhóm ở MCP server."""
        try:
            from mcp_filesystem_server import file_indexer
            # Gán label
            file_indexer.classify_files_by_topic(topic)
            results = file_indexer.get_files_by_category(f"{topic}")
            files = [
                {
                    "filename": f.filename,
                    "filepath": f.filepath,
                    "label": f.label,
                    "type": f.file_type,
                    "size": f.size,
                    "content_preview": f.content_preview[:CONTENT_PREVIEW_LIMIT] + "..." if len(f.content_preview) > CONTENT_PREVIEW_LIMIT else f.content_preview
                } for f in results
            ]
            return {
                "success": True,
                "topic": topic,
                "found": len(files),
                "files": files
            }
        except Exception as e:
            logger.error(f"Lỗi phân loại theo chủ đề: {e}")
            return {
                "success": False,
                "error": str(e),
                "topic": topic,
                "files": []
            }




# Instance global để sử dụng trong ứng dụng
filesystem_manager = FilesystemManager()

# Hàm tiện ích để gọi từ LLM processor
def process_filesystem_query(query: str, query_type: str = "search") -> str:
    """
    Xử lý query liên quan đến filesystem
    
    Args:
        query: Nội dung query của user
        query_type: Loại query (search, scan, export)
    
    Returns:
        str: Kết quả dưới dạng text để hiển thị cho user
    """
    try:
        if query_type == "search":
            result = filesystem_manager.search_files(query)
            if result["success"]:
                if result["found"] > 0:
                    files_text = "\n".join([
                        f"• {f['filename']} ({f['label']}) - {f['size']} bytes"
                        for f in result["files"]
                    ])
                    return f"Tìm thấy {result['found']} file có '{query}':\n\n{files_text}\n\nMetadata đã được chuẩn bị để gửi MCP Cloud."
                else:
                    return f"Không tìm thấy file nào có '{query}'"
            else:
                return f"Lỗi tìm kiếm: {result['error']}"
        
        elif query_type == "scan":
            result = filesystem_manager.scan_files()
            if result["success"]:
                categories = {}
                for f in result["files"]:
                    label = f["label"]
                    if label not in categories:
                        categories[label] = 0
                    categories[label] += 1
                
                category_text = "\n".join([f"• {label}: {count} file" for label, count in categories.items()])
                return f"Đã quét và index {result['total']} file:\n\n{category_text}\n\nTất cả file đã được phân loại và sẵn sàng tìm kiếm."
            else:
                return f"Lỗi quét file: {result['error']}"
            
        elif query_type == "scan_all":
            result = filesystem_manager.scan_files()
            if result["success"]:
                # categories = {}
                # for f in result["files"]:
                #     label = f["label"]
                #     if label not in categories:
                #         categories[label] = 0
                #     categories[label] += 1
                return result["files"]
            else:
                return f"Lỗi quét file: {result['error']}"
        elif query_type == "export":
            result = filesystem_manager.export_metadata()
            if result["success"]:
                return f"Đã xuất metadata của {result['total_files']} file sẵn sàng gửi MCP Cloud.\n\nCác file đã được phân loại và chuẩn bị metadata."
            else:
                return f"Lỗi xuất metadata: {result['error']}"
        
        elif query_type == "classify_by_topic":
            result = filesystem_manager.classify_files_by_topic(query)
            if result["success"]:
                if result["found"] > 0:
                    files_text = "\n".join([
                        f"• {f['filename']}" for f in result["files"]
                    ])
                    return f"Tìm thấy {result['found']} file liên quan đến nhóm '{query}':\n{files_text}"
                else:
                    return f"Không tìm thấy file nào liên quan đến nhóm '{query}'"
            else:
                return f"Lỗi phân loại theo chủ đề: {result['error']}"
        
        else:
            return f"Loại query không được hỗ trợ: {query_type}"
            
    except Exception as e:
        logger.error(f"Lỗi xử lý filesystem query: {e}")
        return f"Lỗi hệ thống: {e}"

# Hàm để khởi tạo filesystem khi chạy ứng dụng
def initialize_filesystem():
    """Khởi tạo filesystem manager khi chạy ứng dụng"""
    try:
        # Quét file ban đầu
        result = filesystem_manager.scan_files()
        if result["success"]:
            logger.info(f"Filesystem initialized: {result['total']} files indexed")
            return True
        else:
            logger.error(f"Failed to initialize filesystem: {result['error']}")
            return False
    except Exception as e:
        logger.error(f"Error initializing filesystem: {e}")
        return False 