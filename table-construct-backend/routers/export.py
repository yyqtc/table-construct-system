"""
导出路由
"""

from fastapi import APIRouter, BackgroundTasks
from fastapi.responses import FileResponse
from models import ExportRequest
from services.export_service import export_docx

router = APIRouter(prefix="/api", tags=["export"])


@router.post("/download")
async def export_docx_endpoint(
    request: ExportRequest, background_tasks: BackgroundTasks
) -> FileResponse:
    """
    导出接口
    接收表格ID数组，从ChromaDB查询对应的表格数据，组装成新的docx文件并返回
    """
    return await export_docx(request.table_ids, background_tasks)
