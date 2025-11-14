"""
上传路由
"""

from fastapi import APIRouter, File, UploadFile
from models import UploadResponse
from services.upload_service import upload_file

router = APIRouter(prefix="/api", tags=["upload"])


@router.post("/upload", response_model=UploadResponse)
async def upload_file_endpoint(file: UploadFile = File(...)) -> UploadResponse:
    """
    文件上传接口
    接收multipart/form-data格式的.docx文件，解析并存入ChromaDB
    """
    return await upload_file(file)
