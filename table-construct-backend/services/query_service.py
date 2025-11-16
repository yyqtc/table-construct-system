"""
查询服务
"""

import logging
import json
import tempfile
import os
from typing import Optional, List
from models import QueryResponse
from database import get_collection, get_model
from utils.xml_converter import xml_to_html, html_to_xml
from utils.mongo import collection as mongo_collection
from utils.docx_utils import create_docx_with_table_and_styles

logger = logging.getLogger(__name__)


async def query_tables(
    query: str, top_k: int, threshold: Optional[float]
) -> QueryResponse:
    """
    执行向量相似度搜索

    Args:
        query: 查询文本
        top_k: 返回数量
        threshold: 相似度阈值

    Returns:
        QueryResponse对象
    """
    try:
        logger.info(
            f"收到查询请求: query={query[:50]}..., top_k={top_k}, threshold={threshold}"
        )

        collection = get_collection()
        model = get_model()

        # 检查依赖是否初始化成功
        if collection is None or model is None:
            logger.error("查询失败: 系统初始化失败，ChromaDB或向量模型未初始化")
            return QueryResponse(
                success=False,
                message="系统初始化失败，请检查ChromaDB和向量模型",
                data=None,
            )

        # 参数验证
        if not query or not query.strip():
            logger.warning("查询失败: 查询文本为空")
            return QueryResponse(success=False, message="查询文本不能为空", data=None)

        if top_k <= 0:
            logger.warning(f"查询失败: top_k={top_k} 必须大于0")
            return QueryResponse(success=False, message="top_k必须大于0", data=None)

        # 将查询文本转换为向量
        query_vector = model.encode(query).tolist()

        # 使用 ChromaDB 的 query 方法进行向量相似度搜索
        results = collection.query(query_embeddings=[query_vector], n_results=top_k)

        # 处理查询结果
        matches = []
        if results and "ids" in results and len(results["ids"]) > 0:
            ids = results["ids"][0]
            distances = results["distances"][0] if "distances" in results else []
            metadatas = results["metadatas"][0] if "metadatas" in results else []
            documents = results["documents"][0] if "documents" in results else []

            for i, table_id in enumerate(ids):
                # 计算相似度（ChromaDB返回的是距离，相似度 = 1 - 距离）
                distance = distances[i] if i < len(distances) else 1.0
                similarity = 1.0 - distance

                # 如果设置了阈值，过滤相似度低于阈值的结果
                if threshold is not None and similarity < threshold:
                    continue

                metadata = metadatas[i] if i < len(metadatas) else {}
                document = documents[i] if i < len(documents) else ""

                # 从MongoDB获取样式信息
                style_info = None
                if mongo_collection is not None:
                    try:
                        style_doc = mongo_collection.find_one({"table_id": table_id})
                        if style_doc and "styles" in style_doc:
                            style_info = style_doc["styles"]
                    except Exception as e:
                        logger.warning(f"从MongoDB获取样式信息失败: table_id={table_id}, error={e}")

                # 将样式信息添加到metadata中
                if style_info:
                    metadata["style_info"] = style_info

                # 创建临时DOCX文件（包含表格和样式）
                temp_docx_path = None
                try:
                    if document:  # 如果有表格XML
                        # 创建临时文件
                        temp_fd, temp_docx_path = tempfile.mkstemp(suffix='.docx', prefix=f'table_{table_id}_')
                        os.close(temp_fd)  # 关闭文件描述符，我们只需要路径
                        
                        # 创建DOCX文件
                        styles_dict = style_info if style_info else {}

                        success = create_docx_with_table_and_styles(
                            document,  # 表格XML
                            styles_dict,  # 样式字典
                            temp_docx_path
                        )
                        
                        if success:
                            logger.info(f"临时DOCX文件创建成功: table_id={table_id}, path={temp_docx_path}")
                        else:
                            logger.warning(f"临时DOCX文件创建失败: table_id={table_id}")
                            temp_docx_path = None
                except Exception as e:
                    logger.error(f"创建临时DOCX文件失败: table_id={table_id}, error={e}", exc_info=True)
                    temp_docx_path = None

                match_result = {
                    "table_id": table_id,
                    "similarity": round(similarity, 4),
                    "distance": round(distance, 4),
                    "table_xml": document,
                    "table_html": table_html,
                    "table_xml_from_html": table_xml_from_html,
                    "metadata": metadata,
                    "temp_docx_path": temp_docx_path,  # 临时DOCX文件路径
                }
                matches.append(match_result)

        logger.info(f"查询成功: 找到{len(matches)}个匹配结果")
        return QueryResponse(
            success=True,
            message=f"查询成功，找到{len(matches)}个匹配结果",
            data=matches,
        )

    except Exception as e:
        logger.error(f"查询失败: {e}", exc_info=True)
        return QueryResponse(success=False, message=f"查询失败: {str(e)}", data=None)
