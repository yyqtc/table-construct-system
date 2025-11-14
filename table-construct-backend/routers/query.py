"""
查询路由
"""

from fastapi import APIRouter, Query
from typing import Optional
from models import QueryRequest, QueryResponse
from services.query_service import query_tables

router = APIRouter(prefix="/api", tags=["query"])


@router.get("/query", response_model=QueryResponse)
async def query_tables_get(
    query: str = Query(..., description="查询文本"),
    top_k: int = Query(10, description="返回数量"),
    threshold: Optional[float] = Query(None, description="相似度阈值"),
) -> QueryResponse:
    """
    查询接口 - GET 方法
    使用 ChromaDB 进行向量相似度搜索
    """
    return await query_tables(query, top_k, threshold)


@router.post("/query", response_model=QueryResponse)
async def query_tables_post(request: QueryRequest) -> QueryResponse:
    """
    查询接口 - POST 方法
    使用 ChromaDB 进行向量相似度搜索
    """
    return await query_tables(request.query, request.top_k, request.threshold)
