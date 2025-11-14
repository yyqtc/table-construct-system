"""
DOCX 文档处理工具函数
"""

import os
import re
from typing import List, Optional, Dict, Any
from docx import Document
from docx.document import Document as DocumentType
from docx.oxml.table import CT_Tbl
from docx.oxml.text.paragraph import CT_P
from docx.table import Table
from docx.text.paragraph import Paragraph


def extract_table_xml(table: Table) -> str:
    """
    提取表格的XML内容

    Args:
        table: python-docx Table对象

    Returns:
        表格的XML字符串
    """
    # 获取表格的底层XML元素
    tbl_element = table._tbl
    return tbl_element.xml


def extract_paragraph_xml(paragraph: Paragraph) -> str:
    """
    提取段落的XML内容

    Args:
        paragraph: python-docx Paragraph对象

    Returns:
        段落的XML字符串
    """
    # 获取段落的底层XML元素
    para_element = paragraph._p
    return para_element.xml


def extract_paragraphs_xml(paragraphs: List[Paragraph]) -> List[str]:
    """
    提取多个段落的XML内容

    Args:
        paragraphs: Paragraph对象列表

    Returns:
        段落XML字符串列表
    """
    return [extract_paragraph_xml(para) for para in paragraphs]


def get_paragraphs_before_table(
    doc: DocumentType, table_index: int, count: int = 3
) -> List[str]:
    """
    获取表格前面的段落文本

    Args:
        doc: Document对象
        table_index: 表格在文档中的索引位置
        count: 需要获取的段落数量，默认3个

    Returns:
        段落文本列表
    """
    paragraphs = []

    # 获取文档中的所有表格
    tables = doc.tables
    if table_index >= len(tables):
        return paragraphs

    # 获取目标表格的XML元素
    target_table_elem = tables[table_index]._tbl

    # 遍历文档body中的所有元素，找到目标表格前面的段落
    body = doc.element.body
    para_texts = []

    for elem in body:
        if elem == target_table_elem:
            # 找到目标表格，停止收集
            break
        elif isinstance(elem, CT_P):
            # 这是一个段落元素，提取文本
            para_text = ""
            # 遍历段落中的所有文本节点
            for t_elem in elem.iter():
                if t_elem.tag.endswith("}t"):  # w:t 标签
                    if t_elem.text:
                        para_text += t_elem.text
            if para_text.strip():
                para_texts.append(para_text.strip())

    # 取最后count个段落
    start_idx = max(0, len(para_texts) - count)
    paragraphs = para_texts[start_idx:]

    return paragraphs


def get_paragraphs_after_table(
    doc: DocumentType, table_index: int, count: int = 1
) -> List[str]:
    """
    获取表格后面的段落文本

    Args:
        doc: Document对象
        table_index: 表格在文档中的索引位置
        count: 需要获取的段落数量，默认1个

    Returns:
        段落文本列表
    """
    paragraphs = []

    # 获取文档中的所有表格
    tables = doc.tables
    if table_index >= len(tables):
        return paragraphs

    # 获取目标表格的XML元素
    target_table_elem = tables[table_index]._tbl

    # 遍历文档body中的所有元素，找到目标表格后面的段落
    body = doc.element.body
    para_texts = []
    found_table = False

    for elem in body:
        if elem == target_table_elem:
            # 找到目标表格，开始收集后面的段落
            found_table = True
            continue
        elif found_table and isinstance(elem, CT_P):
            # 这是一个段落元素，提取文本
            para_text = ""
            # 遍历段落中的所有文本节点
            for t_elem in elem.iter():
                if t_elem.tag.endswith("}t"):  # w:t 标签
                    if t_elem.text:
                        para_text += t_elem.text
            if para_text.strip():
                para_texts.append(para_text.strip())
                if len(para_texts) >= count:
                    break

    paragraphs = para_texts

    return paragraphs


def extract_text_content(
    table: Table, paragraphs_before: List[str], paragraphs_after: List[str]
) -> str:
    """
    提取表格及其前后段落的文本内容，用于向量化

    Args:
        table: Table对象
        paragraphs_before: 表格前面的段落文本列表
        paragraphs_after: 表格后面的段落文本列表

    Returns:
        合并后的文本内容
    """
    text_parts = []

    # 添加前面的段落
    for para in paragraphs_before:
        text_parts.append(para)

    # 提取表格文本内容
    table_text = []
    for row in table.rows:
        row_text = []
        for cell in row.cells:
            cell_text = cell.text.strip()
            if cell_text:
                row_text.append(cell_text)
        if row_text:
            table_text.append(" | ".join(row_text))

    if table_text:
        text_parts.append("\n".join(table_text))

    # 添加后面的段落
    for para in paragraphs_after:
        text_parts.append(para)

    return "\n".join(text_parts)


def extract_document_title(doc: DocumentType) -> Optional[str]:
    """
    提取文档标题

    Args:
        doc: Document对象

    Returns:
        文档标题字符串，如果未找到则返回None
    """
    try:
        if hasattr(doc, "core_properties") and doc.core_properties is not None:
            title = doc.core_properties.title
            if title and title.strip():
                return title.strip()

        if hasattr(doc, "paragraphs") and doc.paragraphs:
            for para in doc.paragraphs[:5]:
                if para.text and para.text.strip():
                    para_text = para.text.strip()
                    style_name = para.style.name if hasattr(para.style, "name") else ""
                    if "Heading" in style_name or "Title" in style_name:
                        return para_text
                    if len(para_text) > 0 and len(para_text) < 200:
                        return para_text

        return None
    except Exception:
        return None


def extract_table_caption(paragraphs_before: List[str]) -> Optional[str]:
    """
    提取表格标题/说明

    Args:
        paragraphs_before: 表格前面的段落文本列表

    Returns:
        表格标题字符串，如果未找到则返回None
    """
    try:
        if not paragraphs_before:
            return None

        caption_patterns = [
            r"^表\s*\d+[\.\s：:].*",
            r"^Table\s*\d+[\.\s:].*",
            r"^表\s*[一二三四五六七八九十]+[\.\s：:].*",
            r"^表格\s*\d+[\.\s：:].*",
        ]

        for para_text in paragraphs_before:
            para_text = para_text.strip()
            if not para_text:
                continue

            for pattern in caption_patterns:
                if re.match(pattern, para_text, re.IGNORECASE):
                    return para_text

            if len(para_text) < 100 and ("表" in para_text or "Table" in para_text):
                return para_text

        if paragraphs_before:
            first_para = paragraphs_before[0].strip()
            if first_para and len(first_para) < 100:
                return first_para

        return None
    except Exception:
        return None


def cleanup_temp_file(file_path: str):
    """清理临时文件"""
    try:
        if file_path and os.path.exists(file_path):
            os.unlink(file_path)
    except Exception:
        pass


def process_style_inheritance(
    table: Table, paragraphs_before: List[Paragraph], paragraphs_after: List[Paragraph]
) -> Dict[str, Any]:
    """
    处理样式继承逻辑

    Args:
        table: Table对象
        paragraphs_before: 表格前面的段落对象列表
        paragraphs_after: 表格后面的段落对象列表

    Returns:
        样式信息字典
    """
    from docx.enum.style import WD_STYLE_TYPE
    import logging

    logger = logging.getLogger(__name__)

    style_metadata = {
        "table_styles": {},
        "paragraph_styles": {},
        "style_inheritance": {},
    }

    try:
        document = None

        if hasattr(table, "_parent") and table._parent is not None:
            if hasattr(table._parent, "document"):
                document = table._parent.document
            elif hasattr(table._parent, "part") and hasattr(
                table._parent.part, "document"
            ):
                document = table._parent.part.document

        if document is None and len(paragraphs_before) > 0:
            para = paragraphs_before[0]
            if hasattr(para, "_parent") and para._parent is not None:
                if hasattr(para._parent, "document"):
                    document = para._parent.document
                elif hasattr(para._parent, "part") and hasattr(
                    para._parent.part, "document"
                ):
                    document = para._parent.part.document

        if document is None and len(paragraphs_after) > 0:
            para = paragraphs_after[0]
            if hasattr(para, "_parent") and para._parent is not None:
                if hasattr(para._parent, "document"):
                    document = para._parent.document
                elif hasattr(para._parent, "part") and hasattr(
                    para._parent.part, "document"
                ):
                    document = para._parent.part.document

        if document is None or not hasattr(document, "styles"):
            return style_metadata

        def extract_style_xml(style):
            """提取样式的XML内容"""
            try:
                if hasattr(style, "_element"):
                    return style._element.xml
                elif hasattr(style, "element"):
                    return style.element.xml
            except:
                pass
            return ""

        def extract_based_on_from_xml(style_xml):
            """从XML中提取w:basedOn属性"""
            if not style_xml:
                return None
            match = re.search(r'w:basedOn[^=]*="([^"]*)"', style_xml, re.IGNORECASE)
            if match:
                return match.group(1)
            return None

        def get_based_on_chain(style, style_dict, visited=None):
            """递归获取样式继承链"""
            if visited is None:
                visited = set()

            style_id = style.style_id if hasattr(style, "style_id") else None
            if not style_id or style_id in visited:
                return []

            visited.add(style_id)
            chain = [style_id]

            based_on_id = None
            if hasattr(style, "based_on") and style.based_on is not None:
                based_on_id = (
                    style.based_on.style_id
                    if hasattr(style.based_on, "style_id")
                    else None
                )
            else:
                style_xml = extract_style_xml(style)
                based_on_id = extract_based_on_from_xml(style_xml)

            if based_on_id and based_on_id in style_dict:
                based_on_style = style_dict[based_on_id]
                based_on_chain = get_based_on_chain(based_on_style, style_dict, visited)
                chain.extend(based_on_chain)

            return chain

        def extract_style_info(style, all_styles_dict):
            """提取样式信息"""
            style_id = style.style_id if hasattr(style, "style_id") else None
            style_name = style.name if hasattr(style, "name") else None
            style_type = str(style.type) if hasattr(style, "type") else None
            style_xml = extract_style_xml(style)

            style_info = {
                "style_id": style_id,
                "name": style_name,
                "type": style_type,
                "xml": style_xml,
            }

            based_on_id = None
            if hasattr(style, "based_on") and style.based_on is not None:
                based_on_id = (
                    style.based_on.style_id
                    if hasattr(style.based_on, "style_id")
                    else None
                )
            else:
                based_on_id = extract_based_on_from_xml(style_xml)

            style_info["based_on"] = based_on_id
            style_info["inheritance_chain"] = (
                get_based_on_chain(style, all_styles_dict) if style_id else []
            )

            return style_info

        try:
            styles = document.styles
        except:
            return style_metadata

        all_styles_dict = {}
        for style in styles:
            try:
                style_id = style.style_id if hasattr(style, "style_id") else None
                if style_id:
                    all_styles_dict[style_id] = style
            except:
                continue

        table_styles_dict = {}
        for style in styles:
            try:
                if hasattr(style, "type") and style.type == WD_STYLE_TYPE.TABLE:
                    style_info = extract_style_info(style, all_styles_dict)
                    style_id = style_info["style_id"]
                    if style_id:
                        table_styles_dict[style_id] = style_info
            except:
                continue

        style_metadata["table_styles"] = table_styles_dict

        paragraph_styles_dict = {}
        all_paragraphs = paragraphs_before + paragraphs_after

        for para in all_paragraphs:
            try:
                if hasattr(para, "style") and para.style is not None:
                    style = para.style
                    style_id = style.style_id if hasattr(style, "style_id") else None

                    if style_id:
                        if style_id not in paragraph_styles_dict:
                            if style_id not in all_styles_dict:
                                all_styles_dict[style_id] = style
                            style_info = extract_style_info(style, all_styles_dict)
                            paragraph_styles_dict[style_id] = style_info
            except:
                continue

        style_metadata["paragraph_styles"] = paragraph_styles_dict

        inheritance_map = {}
        all_styles = list(table_styles_dict.values()) + list(
            paragraph_styles_dict.values()
        )

        for style_info in all_styles:
            style_id = style_info.get("style_id")
            if style_id:
                inheritance_map[style_id] = {
                    "based_on": style_info.get("based_on"),
                    "inheritance_chain": style_info.get("inheritance_chain", []),
                }

        style_metadata["style_inheritance"] = inheritance_map

        tbl_element = table._tbl
        tbl_xml = tbl_element.xml

        if tbl_xml:
            tbl_style_match = re.search(
                r'w:tblStyle[^=]*="([^"]*)"', tbl_xml, re.IGNORECASE
            )
            if tbl_style_match:
                tbl_style_id = tbl_style_match.group(1)
                style_metadata["table_applied_style"] = tbl_style_id
                if tbl_style_id in table_styles_dict:
                    style_metadata["table_applied_style_info"] = table_styles_dict[
                        tbl_style_id
                    ]

    except Exception as e:
        logger.error(f"处理样式继承失败: {e}", exc_info=True)

    return style_metadata
