"""
文件上传服务
"""

import os
import tempfile
import logging
import uuid
import json
import re
import xml.etree.ElementTree as ET

from datetime import datetime
from io import BytesIO
from fastapi import UploadFile, HTTPException
from pathlib import Path
from docx import Document
from docx.oxml.text.paragraph import CT_P
from docx.text.paragraph import Paragraph
from utils.mongo import collection as mongo_collection

from models import UploadResponse
from database import get_collection, get_model
from config import MAX_FILE_SIZE, COZE_SUMMARY_TABLE_WORKFLOW_ID, COZE_EXTRACT_PARA_WORKFLOW_ID, PDF_DIR_PATH, SOFFICE_PATH
from utils.exceptions import HTTP_413_REQUEST_ENTITY_TOO_LARGE
from utils.docx_utils import (
    extract_table_xml,
    extract_paragraphs_xml,
    get_styles_xml_from_docx_stream,
    extract_styles_from_document_xml_fragment,
    extract_style_from_styles_xml,
    get_default_style_id,
    create_docx_with_table_and_styles,
    double_spaces_in_preserve_text
)
from utils.subproccess import _execute_script_subprocess

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
                    doubled_xml_content = double_spaces_in_preserve_text(xml_content)
                    
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
                    table_style_info = {
                        "paragraph_style": None,
                        "table_style": None,
                        "run_style": None,
                        "cell_style": None,
                    }
                    
                    if styles_xml:
                        try:
                            # 从XML内容中提取样式XML
                            table_style_info = extract_styles_from_document_xml_fragment(xml_content, styles_xml)
                            
                            # 如果段落样式为None，尝试从段落对象中提取
                            if table_style_info.get("paragraph_style") is None:
                                para_style_found = False
                                
                                # 方法1: 检查段落对象是否有样式
                                for para in paragraphs_before_objs + paragraphs_after_objs:
                                    if hasattr(para, "style") and para.style is not None:
                                        try:
                                            style_id = para.style.style_id if hasattr(para.style, "style_id") else None
                                            style_name = para.style.name if hasattr(para.style, "name") else None
                                            
                                            logger.info(f"段落对象样式: style_id={style_id}, style_name={style_name}")
                                            
                                            if style_id:
                                                # 从styles.xml中提取段落样式XML
                                                para_style_xml = extract_style_from_styles_xml(
                                                    styles_xml, style_id, "paragraph"
                                                )
                                                if para_style_xml:
                                                    table_style_info["paragraph_style"] = para_style_xml
                                                    logger.info(f"从段落对象提取到段落样式: {style_id} ({style_name})")
                                                    para_style_found = True
                                                    break
                                        except Exception as e:
                                            logger.warning(f"从段落对象提取样式失败: {e}")
                                
                                # 方法2: 如果段落对象也没有样式，使用默认段落样式（通常是 "Normal" 或 "1"）
                                if not para_style_found:
                                    try:
                                        default_para_style_id = get_default_style_id(styles_xml, "paragraph")
                                        if default_para_style_id:
                                            para_style_xml = extract_style_from_styles_xml(
                                                styles_xml, default_para_style_id, "paragraph"
                                            )
                                            if para_style_xml:
                                                table_style_info["paragraph_style"] = para_style_xml
                                                logger.info(f"使用默认段落样式: {default_para_style_id}")
                                    except Exception as e:
                                        logger.warning(f"获取默认段落样式失败: {e}")
                            
                            logger.info(f"提取的样式信息: paragraph_style={table_style_info.get('paragraph_style') is not None}, "
                                      f"table_style={table_style_info.get('table_style') is not None}")
                        except Exception as e:
                            logger.error(f"提取样式信息失败: {e}", exc_info=True)
                            table_style_info = {
                                "paragraph_style": None,
                                "table_style": None,
                                "run_style": None,
                                "cell_style": None,
                            }
                except Exception as e:
                    logger.error(f"表格提取失败: {e}", exc_info=True)
                    continue

                # 生成唯一的表格ID
                table_id = str(uuid.uuid4())

                # 获取创建时间
                creation_time = datetime.now().isoformat()

                # 将样式信息存储到MongoDB
                mongo_id = None
                try:
                    if mongo_collection is not None:
                        style_document = {
                            "table_id": table_id,
                            "filename": file.filename,
                            "table_index": table_index,
                            "styles": table_style_info,  # 存储所有样式XML
                            "creation_time": creation_time,
                        }
                        result = mongo_collection.insert_one(style_document)
                        mongo_id = str(result.inserted_id)
                        logger.info(f"样式信息已存储到MongoDB: table_id={table_id}, mongo_id={mongo_id}")
                    else:
                        logger.warning("MongoDB collection未初始化，跳过样式信息存储")
                except Exception as e:
                    logger.error(f"存储样式信息到MongoDB失败: {e}", exc_info=True)
                    # 继续处理，不中断上传流程

                # 生成预览用pdf文件，先生成临时docx文件，再转换成pdf
                try:
                    temp_fd, temp_docx_path = tempfile.mkstemp(suffix='.docx', prefix=f'table_{table_id}_')
                    os.close(temp_fd)  # 关闭文件描述符，我们只需要路径
                            
                    # 创建DOCX文件
                    success = create_docx_with_table_and_styles(
                        xml_content,  # 表格XML
                        table_style_info,  # 样式字典
                        temp_docx_path
                    )
                            
                    if success:
                        logger.info(f"临时DOCX文件创建成功: table_id={table_id}, path={temp_docx_path}")
                    else:
                        temp_docx_path = None
                        logger.warning(f"临时DOCX文件创建失败: table_id={table_id}")
                        raise Exception("临时DOCX文件创建失败")

                    script_command = f"{SOFFICE_PATH} --headless --convert-to pdf {temp_docx_path} --outdir {PDF_DIR_PATH}"
                    result = _execute_script_subprocess(script_command)
                    if result == "执行失败！":
                        logger.error(f"libreoffice转换失败: table_id={table_id}, result={result}")
                        raise Exception("libreoffice转换失败")
                    else:
                        logger.info(f"libreoffice转换成功: table_id={table_id}, result={result}")
                        pdf_path = os.path.join(PDF_DIR_PATH, Path(temp_docx_path).name.replace(".docx", ".pdf"))
                
                except Exception as e:
                    logger.error(f"创建预览用pdf文件失败: table_id={table_id}, error={e}", exc_info=True)
                    temp_docx_path = None

                if temp_docx_path and os.path.exists(temp_docx_path):
                    os.unlink(temp_docx_path)

                # 构建metadata结构
                # 注意：ChromaDB metadata 只支持基本类型（str, int, float, bool, None）
                # 样式信息已存储到MongoDB，metadata中存储table_id和mongo_id用于关联
                metadata = {
                    "table_id": table_id,
                    "filename": file.filename,
                    "file_size": str(file_size),  # 确保是字符串类型
                    "table_index": str(table_index),  # 确保是字符串类型
                    "creation_time": creation_time,
                    "pdf_path": pdf_path
                }
                
                # 如果MongoDB插入成功，将mongo_id添加到metadata中
                if mongo_id:
                    metadata["mongo_id"] = mongo_id

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
                        documents=[doubled_xml_content],
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
