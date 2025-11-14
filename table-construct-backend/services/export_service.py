"""
导出服务
"""

import logging
import os
import tempfile
from fastapi import BackgroundTasks, HTTPException
from fastapi.responses import FileResponse
from docx import Document
from docx.oxml import parse_xml

from database import get_collection
from utils.exceptions import (
    HTTP_400_BAD_REQUEST,
    HTTP_404_NOT_FOUND,
    HTTP_500_INTERNAL_SERVER_ERROR,
)
from utils.docx_utils import cleanup_temp_file

logger = logging.getLogger(__name__)


async def export_docx(
    table_ids: list, background_tasks: BackgroundTasks
) -> FileResponse:
    """
    导出表格为DOCX文件

    Args:
        table_ids: 表格ID列表
        background_tasks: 后台任务

    Returns:
        FileResponse对象
    """
    try:
        logger.info(f"收到文件下载请求: table_ids_count={len(table_ids)}")

        collection = get_collection()

        # 检查依赖是否初始化成功
        if collection is None:
            logger.error("文件下载失败: ChromaDB未初始化")
            raise HTTPException(
                status_code=HTTP_500_INTERNAL_SERVER_ERROR,
                detail="系统初始化失败，请检查ChromaDB",
            )

        # 参数验证
        if not table_ids or len(table_ids) == 0:
            logger.warning("文件下载失败: 表格ID数组为空")
            raise HTTPException(
                status_code=HTTP_400_BAD_REQUEST, detail="表格ID数组不能为空"
            )

        # 从ChromaDB查询表格数据
        try:
            results = collection.get(ids=table_ids)
            logger.info(f"ChromaDB查询成功: 请求{len(table_ids)}个表格ID")
        except Exception as e:
            logger.error(f"ChromaDB查询失败: error={e}", exc_info=True)
            raise HTTPException(
                status_code=HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"ChromaDB查询失败: {str(e)}",
            )

        # 检查查询结果
        if not results or "ids" not in results or len(results["ids"]) == 0:
            logger.warning(f"文件下载失败: 未找到指定的表格数据 table_ids={table_ids}")
            raise HTTPException(
                status_code=HTTP_404_NOT_FOUND, detail="未找到指定的表格数据"
            )

        # 创建新的docx文档
        doc = Document()

        # 获取查询到的数据
        ids = results["ids"]
        documents = results.get("documents", [])
        metadatas = results.get("metadatas", [])

        # 按照请求的ID顺序组装表格
        id_to_data = {}
        for i, table_id in enumerate(ids):
            id_to_data[table_id] = {
                "document": documents[i] if i < len(documents) else "",
                "metadata": metadatas[i] if i < len(metadatas) else {},
            }

        # 按照请求顺序添加表格和前后段落
        inserted_count = 0
        for table_id in table_ids:
            if table_id not in id_to_data:
                logger.warning(f"表格ID未找到: table_id={table_id}")
                continue

            data = id_to_data[table_id]
            table_xml = data["document"]
            metadata = data["metadata"]

            if not table_xml:
                logger.warning(f"表格XML为空: table_id={table_id}")
                continue

            try:
                # 获取前后段落文本
                paragraphs_before_text = metadata.get("paragraphs_before", "")
                paragraphs_after_text = metadata.get("paragraphs_after", "")

                # 插入前面的段落
                if paragraphs_before_text:
                    para_before_lines = paragraphs_before_text.split("\n")
                    for para_text in para_before_lines:
                        if para_text.strip():
                            doc.add_paragraph(para_text.strip())

                # 解析XML并插入表格
                tbl_element = parse_xml(table_xml)
                doc.element.body.append(tbl_element)
                inserted_count += 1
                logger.info(f"表格插入成功: table_id={table_id}")

                # 插入后面的段落
                if paragraphs_after_text:
                    para_after_lines = paragraphs_after_text.split("\n")
                    for para_text in para_after_lines:
                        if para_text.strip():
                            doc.add_paragraph(para_text.strip())
            except Exception as e:
                logger.error(
                    f"插入表格失败: table_id={table_id}, error={e}", exc_info=True
                )
                continue

        # 检查是否成功插入了表格
        if inserted_count == 0:
            logger.error(f"文件下载失败: 未能成功插入任何表格 table_ids={table_ids}")
            raise HTTPException(
                status_code=HTTP_400_BAD_REQUEST,
                detail="未能成功插入任何表格，请检查表格ID和数据",
            )

        # 保存到临时文件
        temp_file = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="wb", suffix=".docx", delete=False
            ) as tmp:
                temp_file = tmp.name
                doc.save(tmp.name)

            logger.info(
                f"文件保存成功: temp_file={temp_file}, inserted_count={inserted_count}"
            )

            # 添加后台任务清理临时文件
            background_tasks.add_task(cleanup_temp_file, temp_file)

            # 返回文件供下载
            logger.info(
                f"文件下载响应: filename=exported_tables.docx, inserted_count={inserted_count}"
            )
            return FileResponse(
                temp_file,
                media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                filename="exported_tables.docx",
            )
        except Exception as e:
            # 清理临时文件
            if temp_file and os.path.exists(temp_file):
                try:
                    os.unlink(temp_file)
                except:
                    pass
            logger.error(f"文件保存失败: error={e}", exc_info=True)
            raise HTTPException(
                status_code=HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"文件保存失败: {str(e)}",
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"导出失败: error={e}", exc_info=True)
        raise HTTPException(
            status_code=HTTP_500_INTERNAL_SERVER_ERROR, detail=f"导出失败: {str(e)}"
        )
