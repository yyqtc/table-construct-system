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


def extract_style_ids_from_xml(xml_content: str) -> Dict[str, Optional[str]]:
    """
    从document.xml的XML片段中提取样式ID
    
    Args:
        xml_content: document.xml中的XML字符串片段
        
    Returns:
        包含各种样式ID的字典:
        - paragraph_style: 段落样式ID (w:pStyle)
        - table_style: 表格样式ID (w:tblStyle)
        - run_style: 文本运行样式ID (w:rStyle)
        - cell_style: 单元格样式ID (w:tcStyle)
    """
    style_ids = {
        "paragraph_style": None,
        "table_style": None,
        "run_style": None,
        "cell_style": None,
    }
    
    if not xml_content:
        return style_ids
    
    # 提取段落样式 w:pStyle w:val="样式ID"
    p_style_match = re.search(r'w:pStyle[^=]*w:val="([^"]*)"', xml_content, re.IGNORECASE)
    if p_style_match:
        style_ids["paragraph_style"] = p_style_match.group(1)
    
    # 提取表格样式 w:tblStyle w:val="样式ID"
    tbl_style_match = re.search(r'w:tblStyle[^=]*w:val="([^"]*)"', xml_content, re.IGNORECASE)
    if tbl_style_match:
        style_ids["table_style"] = tbl_style_match.group(1)
    
    # 提取文本运行样式 w:rStyle w:val="样式ID"
    r_style_match = re.search(r'w:rStyle[^=]*w:val="([^"]*)"', xml_content, re.IGNORECASE)
    if r_style_match:
        style_ids["run_style"] = r_style_match.group(1)
    
    # 提取单元格样式 w:tcStyle w:val="样式ID"
    tc_style_match = re.search(r'w:tcStyle[^=]*w:val="([^"]*)"', xml_content, re.IGNORECASE)
    if tc_style_match:
        style_ids["cell_style"] = tc_style_match.group(1)
    
    return style_ids


def extract_style_from_styles_xml(
    styles_xml: str, style_id: str, style_type: str = None
) -> Optional[Dict[str, Any]]:
    """
    从styles.xml中提取指定样式ID的样式定义
    
    Args:
        styles_xml: styles.xml的完整XML内容
        style_id: 要查找的样式ID
        style_type: 样式类型 (可选): "paragraph", "table", "character", "numbering"
        
    Returns:
        样式信息字典，包含:
        - style_id: 样式ID
        - style_type: 样式类型
        - name: 样式名称
        - based_on: 继承的基础样式ID
        - xml: 完整的样式XML定义
        如果未找到则返回None
    """
    if not styles_xml or not style_id:
        return None
    
    try:
        from lxml import etree
        
        # 解析styles.xml
        namespaces = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
        styles_tree = etree.fromstring(styles_xml.encode('utf-8') if isinstance(styles_xml, str) else styles_xml)
        
        # 构建XPath查询
        if style_type:
            xpath_query = f'//w:style[@w:styleId="{style_id}" and @w:type="{style_type}"]'
        else:
            xpath_query = f'//w:style[@w:styleId="{style_id}"]'
        
        # 查找样式
        style_elements = styles_tree.xpath(xpath_query, namespaces=namespaces)
        
        if not style_elements:
            return None
        
        style_element = style_elements[0]
        
        # 提取样式信息
        style_info = {
            "style_id": style_id,
            "style_type": style_element.get(f'{{{namespaces["w"]}}}type'),
            "name": None,
            "based_on": None,
            "xml": etree.tostring(style_element, encoding='unicode', pretty_print=True),
        }
        
        # 提取样式名称 w:name w:val="样式名称"
        name_elem = style_element.xpath('.//w:name/@w:val', namespaces=namespaces)
        if name_elem:
            style_info["name"] = name_elem[0]
        
        # 提取基础样式 w:basedOn w:val="基础样式ID"
        based_on_elem = style_element.xpath('.//w:basedOn/@w:val', namespaces=namespaces)
        if based_on_elem:
            style_info["based_on"] = based_on_elem[0]
        
        return style_info
        
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"从styles.xml提取样式失败: {e}", exc_info=True)
        return None


def extract_styles_from_document_xml_fragment(
    document_xml_fragment: str, styles_xml: str
) -> Dict[str, Any]:
    """
    根据document.xml的XML片段提取对应的styles.xml中的样式
    
    Args:
        document_xml_fragment: document.xml中的XML片段（如段落、表格、文本运行等）
        styles_xml: styles.xml的完整XML内容
        
    Returns:
        包含提取到的样式信息的字典:
        - paragraph_style: 段落样式信息（如果有）
        - table_style: 表格样式信息（如果有）
        - run_style: 文本运行样式信息（如果有）
        - cell_style: 单元格样式信息（如果有）
        - all_styles: 所有找到的样式列表
    """
    result = {
        "paragraph_style": None,
        "table_style": None,
        "run_style": None,
        "cell_style": None,
        "all_styles": [],
    }
    
    if not document_xml_fragment or not styles_xml:
        return result
    
    try:
        # 从document.xml片段中提取样式ID（使用正则表达式，不要求完整XML）
        style_ids = extract_style_ids_from_xml(document_xml_fragment)
        
        # 根据样式类型映射
        style_type_map = {
            "paragraph_style": "paragraph",
            "table_style": "table",
            "run_style": "character",
            "cell_style": "table",
        }
        
        # 提取每个样式
        for style_key, style_id in style_ids.items():
            if style_id:
                try:
                    style_type = style_type_map.get(style_key)
                    style_info = extract_style_from_styles_xml(styles_xml, style_id, style_type)
                    
                    if style_info:
                        result[style_key] = style_info
                        result["all_styles"].append(style_info)
                        
                        # 如果样式有继承关系，递归提取基础样式
                        if style_info.get("based_on"):
                            based_on_id = style_info["based_on"]
                            try:
                                based_on_info = extract_style_from_styles_xml(
                                    styles_xml, based_on_id, style_type
                                )
                                if based_on_info:
                                    style_info["based_on_style"] = based_on_info
                                    result["all_styles"].append(based_on_info)
                            except Exception as e:
                                import logging
                                logger = logging.getLogger(__name__)
                                logger.warning(f"提取基础样式失败 (style_id={based_on_id}): {e}")
                except Exception as e:
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.warning(f"提取样式失败 (style_key={style_key}, style_id={style_id}): {e}")
                    continue
        
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"extract_styles_from_document_xml_fragment 执行失败: {e}", exc_info=True)
    
    return result


def get_styles_xml_from_docx_file(file_content: bytes) -> Optional[str]:
    """
    从docx文件内容（bytes）中提取styles.xml
    
    Args:
        file_content: docx文件的二进制内容
        
    Returns:
        styles.xml的字符串内容，如果未找到则返回None
    """
    try:
        from zipfile import ZipFile
        from io import BytesIO
        
        # 将文件内容转换为BytesIO对象
        file_stream = BytesIO(file_content)
        
        with ZipFile(file_stream, 'r') as docx:
            # 检查styles.xml是否存在
            if 'word/styles.xml' in docx.namelist():
                styles_xml = docx.read('word/styles.xml').decode('utf-8')
                return styles_xml
            else:
                return None
                
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"从docx文件提取styles.xml失败: {e}", exc_info=True)
        return None


def get_styles_xml_from_docx_stream(file_stream) -> Optional[str]:
    """
    从docx文件流（BytesIO）中提取styles.xml
    
    Args:
        file_stream: BytesIO对象或类似文件对象
        
    Returns:
        styles.xml的字符串内容，如果未找到则返回None
    """
    try:
        from zipfile import ZipFile
        
        # 确保文件指针在开头
        if hasattr(file_stream, 'seek'):
            file_stream.seek(0)
        
        with ZipFile(file_stream, 'r') as docx:
            # 检查styles.xml是否存在
            if 'word/styles.xml' in docx.namelist():
                styles_xml = docx.read('word/styles.xml').decode('utf-8')
                return styles_xml
            else:
                return None
                
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"从docx流提取styles.xml失败: {e}", exc_info=True)
        return None
