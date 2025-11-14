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
from config import MAX_FILE_SIZE, COZE_EXTRACT_TABLE_WORKFLOW_ID
from utils.exceptions import HTTP_413_REQUEST_ENTITY_TOO_LARGE
from utils.docx_utils import (
    extract_table_xml,
    get_paragraphs_before_table,
    get_paragraphs_after_table,
    extract_text_content,
    process_style_inheritance,
    extract_paragraphs_xml,
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

                # 提取表格前后的段落
                paragraphs_before_text = get_paragraphs_before_table(
                    doc, table_index, count=3
                )
                paragraphs_after_text = get_paragraphs_after_table(
                    doc, table_index, count=1
                )

                # 提取文本内容用于向量化
                text_content = extract_text_content(
                    table, paragraphs_before_text, paragraphs_after_text
                )

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
                style_info = process_style_inheritance(
                    table, paragraphs_before_objs, paragraphs_after_objs
                )

                # 获取段落对象的XML
                paragraphs_before_xml = "\n".join(extract_paragraphs_xml(paragraphs_before_objs))
                paragraphs_after_xml = "\n".join(extract_paragraphs_xml(paragraphs_after_objs))

                table = ET.fromstring(table_xml)
                text = ' '.join([text.strip() for text in table.itertext()])
                text = text.strip()
                text = f"表格内容总结后是：{text}"
                raw_xml = paragraphs_before_xml + "\n" + f"<w:tbl>{text}</w:tbl>" + "\n" + paragraphs_after_xml
                style_info_str = json.dumps(style_info, ensure_ascii=False)

                logger.info(f"""
                            .docx文件的表格在document.xml文件中的xml内容是：
                            {raw_xml}
                            .docx文件的表格在styles.xml文件中的样式信息是：
                            {style_info_str}
                            """)

                # 使用异步调用 LLM，避免阻塞事件循环
                try:
                    response = await async_coze.workflows.runs.create(
                        workflow_id=COZE_EXTRACT_TABLE_WORKFLOW_ID,
                        parameters={
                            "raw_xml": f"""
                            .docx文件的表格在document.xml文件中的xml内容是：
                            {raw_xml}
                            .docx文件的表格在styles.xml文件中的样式信息是：
                            {style_info_str}
                            """
                        }
                    )
                    logger.info(f"Coze API调用成功: {response}")
                    result = json.loads(response.data)
                    table_xml_from_llm = result.get("xml_content", "")
                    style_info = result.get("style_info", "")
                    
                    # re.sub(pattern, repl, string) 参数说明：
                    # pattern: 正则表达式模式，匹配要替换的内容
                    # repl: 替换的字符串（或函数），用于替换匹配到的内容
                    # string: 要搜索的源字符串
                    # 作用：在 table_xml_from_llm 中查找 <w:tbl>...</w:tbl>，用原始的 table_xml 替换它
                    table_xml = re.sub(r"<w:tbl>.*?</w:tbl>", table_xml, table_xml_from_llm)

                    logger.info(f"{table_xml}\n{style_info}")

                except Exception as e:
                    logger.error(f"LLM处理失败: {e}", exc_info=True)
                    # 如果LLM处理失败，使用原始数据
                    logger.warning("使用原始表格XML和样式信息")
                    # table_xml 和 style_info 保持原值，不进行修改

                # 生成唯一的表格ID
                table_id = str(uuid.uuid4())

                # 获取创建时间
                creation_time = datetime.now().isoformat()

                # 将 style_info 转换为 JSON 字符串（ChromaDB metadata 不支持嵌套字典）
                style_info_json = json.dumps(style_info, ensure_ascii=False)

                # 构建metadata结构
                # 注意：ChromaDB metadata 只支持基本类型（str, int, float, bool, None）
                # 嵌套字典需要序列化为 JSON 字符串
                metadata = {
                    "table_id": table_id,
                    "filename": file.filename,
                    "file_size": str(file_size),  # 确保是字符串类型
                    "table_index": str(table_index),  # 确保是字符串类型
                    "style_info": style_info_json,  # JSON 字符串
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
