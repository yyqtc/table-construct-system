"""
文件上传服务
"""

import logging
import uuid
import json
import re
import xml.etree.ElementTree as ET

from datetime import datetime
from io import BytesIO
from fastapi import UploadFile, HTTPException
from docx import Document
from docx.oxml.text.paragraph import CT_P
from docx.text.paragraph import Paragraph

from models import UploadResponse
from database import get_collection, get_model
from config import MAX_FILE_SIZE, COZE_SUMMARY_TABLE_WORKFLOW_ID, COZE_EXTRACT_PARA_WORKFLOW_ID
from utils.exceptions import HTTP_413_REQUEST_ENTITY_TOO_LARGE
from utils.docx_utils import (
    extract_table_xml,
    extract_paragraphs_xml,
    get_styles_xml_from_docx_stream,
    extract_styles_from_document_xml_fragment,
)

from utils.coze import async_coze

logger = logging.getLogger(__name__)


async def upload_file(file: UploadFile) -> UploadResponse:
    """
    处理文件上传

    Args:
        file: 上传的文件对象

    Returns:
        UploadResponse对象
    """
    try:
        logger.info(f"收到文件上传请求: filename={file.filename}")

        collection = get_collection()
        model = get_model()

        # 检查依赖是否初始化成功
        if collection is None or model is None:
            logger.error("文件上传失败: 系统初始化失败，ChromaDB或向量模型未初始化")
            return UploadResponse(
                success=False,
                message="系统初始化失败，请检查ChromaDB和向量模型",
                data=None,
            )

        # 文件格式验证
        if not file.filename:
            logger.warning("文件上传失败: 文件名为空")
            return UploadResponse(success=False, message="文件名不能为空", data=None)

        if not file.filename.lower().endswith(".docx"):
            logger.warning(f"文件上传失败: 不支持的文件格式 filename={file.filename}")
            return UploadResponse(
                success=False, message="只支持.docx格式的文件", data=None
            )

        # 读取文件内容到内存
        file_content = await file.read()
        file_size = len(file_content)
        logger.info(f"文件读取成功: filename={file.filename}, size={file_size} bytes")

        # 文件大小限制
        if file_size > MAX_FILE_SIZE:
            logger.warning(
                f"文件上传失败: 文件大小超过限制 filename={file.filename}, size={file_size} bytes"
            )
            raise HTTPException(
                status_code=HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"文件大小超过限制（最大50MB），当前文件大小：{file_size / (1024 * 1024):.2f}MB",
            )

        # 使用BytesIO将文件内容转换为文件对象
        file_stream = BytesIO(file_content)

        # 解析DOCX文件
        try:
            doc = Document(file_stream)
            logger.info(f"DOCX文件解析成功: filename={file.filename}")
        except Exception as e:
            logger.error(
                f"DOCX文件解析失败: filename={file.filename}, error={e}", exc_info=True
            )
            return UploadResponse(
                success=False, message=f"DOCX文件解析失败: {str(e)}", data=None
            )

        styles_xml = get_styles_xml_from_docx_stream(file_stream)
        logger.info(f"styles_xml: {styles_xml}")

        # 提取所有表格
        tables = doc.tables
        if not tables:
            logger.warning(f"文件上传失败: 文档中未找到表格 filename={file.filename}")
            return UploadResponse(success=False, message="文档中未找到表格", data=None)

        logger.info(f"文档中找到{len(tables)}个表格: filename={file.filename}")

        # 处理每个表格
        uploaded_tables = []
        for table_index, table in enumerate(tables):
            try:
                # 提取表格XML
                table_xml = extract_table_xml(table)

                # 处理样式继承
                target_table_elem = table._tbl
                body = doc.element.body
                paragraphs_before_objs = []
                paragraphs_after_objs = []
                para_objs_before = []
                found_table = False
                for elem in body:
                    if elem == target_table_elem:
                        found_table = True
                        continue
                    elif isinstance(elem, CT_P):
                        para = Paragraph(elem, doc)
                        para_text = para.text.strip()
                        if para_text:
                            if not found_table:
                                para_objs_before.append(para)
                            else:
                                paragraphs_after_objs.append(para)
                                if len(paragraphs_after_objs) >= 1:
                                    break

                paragraphs_before_objs = (
                    para_objs_before[-3:]
                    if len(para_objs_before) > 3
                    else para_objs_before
                )

                # 获取段落对象的XML
                paragraphs_before_xml = "\n".join(extract_paragraphs_xml(paragraphs_before_objs))
                paragraphs_after_xml = "\n".join(extract_paragraphs_xml(paragraphs_after_objs))

                # 提取表格文本内容用于Coze工作流
                table_xml_tree = ET.fromstring(table_xml)
                text = ','.join([text.strip() for text in table_xml_tree.itertext()])
                text = text.strip()

                try:
                    table_summary_wrapper = await async_coze.workflows.runs.create(
                        workflow_id=COZE_SUMMARY_TABLE_WORKFLOW_ID,
                        parameters={
                            "table_content": text
                        }
                    )
                    table_summary_wrapper = json.loads(table_summary_wrapper.data)
                    table_summary = table_summary_wrapper.get("table_summary", "")
                    logger.info(f"表格内容总结成功: {table_summary}")
                    xml_content = paragraphs_before_xml + "\n" + "<w:tbl></w:tbl>" + "\n" + paragraphs_after_xml
                    para_extract_wrapper = await async_coze.workflows.runs.create(
                        workflow_id=COZE_EXTRACT_PARA_WORKFLOW_ID,
                        parameters={
                            "table_summary": table_summary,
                            "xml_content": xml_content
                        }
                    )
                    para_extract_wrapper = json.loads(para_extract_wrapper.data)
                    xml_content = para_extract_wrapper.get("xml_content", "")
                    xml_content = re.sub(r"<w:tbl>.*?</w:tbl>", table_xml, xml_content)
                    logger.info(f"表格XML内容: {xml_content}")
                    
                    # 提取文本内容（处理多个根元素的情况）
                    try:
                        # 尝试解析为单个XML文档
                        table_xml_content = ET.fromstring(xml_content)
                        text_content = ','.join([text.strip() for text in table_xml_content.itertext()])
                    except ET.ParseError:
                        # 如果包含多个根元素，使用XML片段解析
                        # 将多个根元素包装在一个临时根元素中
                        wrapped_xml = f"<root>{xml_content}</root>"
                        try:
                            wrapped_tree = ET.fromstring(wrapped_xml)
                            text_content = ','.join([text.strip() for text in wrapped_tree.itertext()])
                        except Exception as e:
                            logger.warning(f"XML解析失败，使用正则提取文本: {e}")
                            # 使用正则表达式提取所有文本内容作为后备方案
                            text_matches = re.findall(r'<w:t[^>]*>(.*?)</w:t>', xml_content, re.DOTALL)
                            text_content = ','.join([text.strip() for text in text_matches if text.strip()])

                    # 提取样式信息（如果styles_xml存在）
                    if styles_xml:
                        try:
                            table_style_info = extract_styles_from_document_xml_fragment(xml_content, styles_xml)
                        except Exception as e:
                            logger.error(f"提取样式信息失败: {e}", exc_info=True)
                            table_style_info = {}
                    else:
                        table_style_info = {}
                except Exception as e:
                    logger.error(f"表格提取失败: {e}", exc_info=True)
                    continue

                # 生成唯一的表格ID
                table_id = str(uuid.uuid4())

                # 获取创建时间
                creation_time = datetime.now().isoformat()

                # 构建metadata结构
                # 注意：ChromaDB metadata 只支持基本类型（str, int, float, bool, None）
                # 嵌套字典需要序列化为 JSON 字符串
                metadata = {
                    "table_id": table_id,
                    "filename": file.filename,
                    "file_size": str(file_size),  # 确保是字符串类型
                    "table_index": str(table_index),  # 确保是字符串类型
                    "style_info": json.dumps(table_style_info, ensure_ascii=False),  # 序列化为JSON字符串
                    "creation_time": creation_time,
                }

                # 向量化文本内容
                try:
                    embedding = model.encode(text_content).tolist()
                except Exception as e:
                    logger.error(
                        f"文本向量化失败: filename={file.filename}, table_index={table_index}, error={e}",
                        exc_info=True,
                    )
                    return UploadResponse(
                        success=False, message=f"文本向量化失败: {str(e)}", data=None
                    )

                # 存入ChromaDB
                try:
                    collection.add(
                        ids=[table_id],
                        embeddings=[embedding],
                        metadatas=[metadata],
                        documents=[table_xml],
                    )
                    logger.info(
                        f"表格存储成功: filename={file.filename}, table_id={table_id}, table_index={table_index}"
                    )
                except Exception as e:
                    logger.error(
                        f"ChromaDB存储失败: filename={file.filename}, table_index={table_index}, error={e}",
                        exc_info=True,
                    )
                    return UploadResponse(
                        success=False, message=f"ChromaDB存储失败: {str(e)}", data=None
                    )

                uploaded_tables.append(
                    {
                        "table_id": table_id,
                        "table_index": table_index,
                        "metadata": metadata,
                    }
                )

            except Exception as e:
                logger.error(
                    f"处理表格失败: filename={file.filename}, table_index={table_index}, error={e}",
                    exc_info=True,
                )
                # 继续处理下一个表格，不中断整个上传过程
                continue

        if not uploaded_tables:
            logger.error(f"文件上传失败: 所有表格处理失败 filename={file.filename}")
            return UploadResponse(success=False, message="所有表格处理失败", data=None)

        logger.info(
            f"文件上传成功: filename={file.filename}, tables_count={len(uploaded_tables)}"
        )
        return UploadResponse(
            success=True,
            message=f"成功上传文件，处理了{len(uploaded_tables)}个表格",
            data={
                "filename": file.filename,
                "file_size": file_size,
                "tables_count": len(uploaded_tables),
                "uploaded_tables": uploaded_tables,
            },
        )

    except HTTPException:
        # 重新抛出HTTP异常（如413错误）
        raise
    except Exception as e:
        logger.error(
            f"文件上传失败: filename={file.filename if hasattr(file, 'filename') else 'unknown'}, error={e}",
            exc_info=True,
        )
        return UploadResponse(
            success=False, message=f"文件上传失败: {str(e)}", data=None
        )
