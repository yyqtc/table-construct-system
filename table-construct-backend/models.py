"""
Pydantic 数据模型定义
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel


class QueryRequest(BaseModel):
    """查询请求模型"""

    query: str
    top_k: Optional[int] = 10
    threshold: Optional[float] = None


class QueryResponse(BaseModel):
    """查询响应模型"""

    success: bool
    message: str
    data: Optional[List[Dict[str, Any]]] = None


class UploadResponse(BaseModel):
    """上传响应模型"""

    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None


class ExportRequest(BaseModel):
    """导出请求模型"""

    table_ids: List[str]
