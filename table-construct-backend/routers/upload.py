"""
上传路由
"""

import logging
from fastapi import APIRouter, File, UploadFile, BackgroundTasks
from models import UploadResponse
from services.upload_service import upload_file, process_tables_background

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["upload"])


@router.post("/upload", response_model=UploadResponse)
async def upload_file_endpoint(
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = BackgroundTasks()
) -> UploadResponse:
    """
    文件上传接口
    接收multipart/form-data格式的.docx文件，解析并存入ChromaDB
    文件验证通过后立即返回响应，表格提取在后台异步处理
    """
    # 先读取文件内容（UploadFile只能读取一次）
    file_content = await file.read()
    file_size = len(file_content)
    
    # 调用upload_file进行文件验证和基本检查
    # 注意：这里需要创建一个新的UploadFile对象或者修改upload_file接受bytes
    # 为了简化，我们修改upload_file接受bytes参数
    response = await upload_file(file_content, file.filename, file_size)
    
    # 如果验证通过，将表格处理任务添加到后台
    if response.success and response.data:
        # 将耗时的表格处理任务添加到后台
        background_tasks.add_task(
            process_tables_background,
            file_content,
            file.filename,
            file_size
        )
        logger.info(f"已将表格处理任务添加到后台: filename={file.filename}")
    
    return response
