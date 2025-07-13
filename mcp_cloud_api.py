from pydantic import BaseModel
from typing import Optional
import json
from datetime import datetime
from pathlib import Path

class Metadata(BaseModel):
    filename: str
    label: str
    content: Optional[str] = ""
    timestamp: Optional[str] = None  # ISO 8601


class MCPMetadataService:
    def __init__(self, store_dir: str = "metadata_store", filename: str = "metadata.json"):
        self.store_dir = Path(store_dir)
        self.store_path = Path(store_dir) / filename
        self.store_dir.mkdir(parents=True, exist_ok=True)
        self.store_path.touch(exist_ok=True)


    def save_metadata(self, metadata: dict):
        if not metadata.get("timestamp"):
            metadata["timestamp"] = datetime.now().isoformat()

        try:
            with self.store_path.open("a", encoding="utf-8") as f:
                f.write(json.dumps(metadata, ensure_ascii=False) + "\n")
            return {"status": "success", "filename": metadata["filename"]}
        except Exception as e:
            return {"status": "error", "detail": str(e)}


    def load_all(self):
        """Trả về danh sách tất cả metadata đã lưu"""
        try:
            with self.store_path.open("r", encoding="utf-8") as f:
                return [json.loads(line) for line in f if line.strip()]
        except Exception as e:
            return {"status": "error", "detail": str(e)}

    
    def load_by_filename(self, filename: str):
        """Trả về metadata theo filename"""
        try:
            with self.store_path.open("r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        metadata = json.loads(line)
                        if metadata.get("filename") == filename:
                            return metadata
            return {"status": "error", "detail": "Metadata not found for the given filename"}
        except Exception as e:
            return {"status": "error", "detail": str(e)}
    

    def load_by_metadata_filename(self, metadata_filename: str):
        """Trả về metadata theo tên file metadata"""
        try:
            metadata_path = self.store_dir / metadata_filename
            if not metadata_path.exists():
                return {"status": "error", "detail": "Metadata file does not exist"}

            with metadata_path.open("r", encoding="utf-8") as f:
                return [json.loads(line) for line in f if line.strip()]
        except Exception as e:
            return {"status": "error", "detail": str(e)}



# FastAPI application setup
from fastapi import FastAPI, HTTPException
# app = FastAPI(title="MCP Cloud JSON Store", version="1.0")
app = FastAPI(title="MCP Cloud JSON Store", version="1.0", docs_url="/docs", redoc_url=None)

mcp_service = MCPMetadataService()

@app.post("/upload-metadata")
def upload_metadata(data: Metadata):
    result = mcp_service.save_metadata(data.dict())
    if result["status"] == "success":
        return result
    else:
        raise HTTPException(status_code=500, detail=result["detail"])


@app.get("/metadata")
def get_all_metadata():
    return mcp_service.load_all()


@app.get("/metadata/{filename}")
def get_metadata_by_filename(filename: str):
    result = mcp_service.load_by_filename(filename)
    if "status" in result and result["status"] == "error":
        raise HTTPException(status_code=404, detail=result["detail"])
    return result


@app.get("/metadata-file/{metadata_filename}")
def get_metadata_by_metadata_filename(metadata_filename: str):
    result = mcp_service.load_by_metadata_filename(metadata_filename)
    if "status" in result and result["status"] == "error":
        raise HTTPException(status_code=404, detail=result["detail"])
    return result


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("mcp_cloud_api:app", host="0.0.0.0", port=8000, reload=True)
