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
    # 支持多种格式：<w:pStyle w:val="..."/> 或 <w:pStyle w:val='...'/> 或带命名空间的格式
    p_style_patterns = [
        r'<w:pStyle[^>]*w:val=["\']([^"\']*)["\']',  # 标准格式
        r'w:pStyle[^>]*w:val=["\']([^"\']*)["\']',   # 不带<的格式
        r'pStyle[^>]*val=["\']([^"\']*)["\']',        # 简化格式
    ]
    for pattern in p_style_patterns:
        p_style_match = re.search(pattern, xml_content, re.IGNORECASE | re.DOTALL)
        if p_style_match:
            style_ids["paragraph_style"] = p_style_match.group(1)
            break
    
    # 提取表格样式 w:tblStyle w:val="样式ID"
    tbl_style_patterns = [
        r'<w:tblStyle[^>]*w:val=["\']([^"\']*)["\']',
        r'w:tblStyle[^>]*w:val=["\']([^"\']*)["\']',
        r'tblStyle[^>]*val=["\']([^"\']*)["\']',
    ]
    for pattern in tbl_style_patterns:
        tbl_style_match = re.search(pattern, xml_content, re.IGNORECASE | re.DOTALL)
        if tbl_style_match:
            style_ids["table_style"] = tbl_style_match.group(1)
            break
    
    # 提取文本运行样式 w:rStyle w:val="样式ID"
    r_style_patterns = [
        r'<w:rStyle[^>]*w:val=["\']([^"\']*)["\']',
        r'w:rStyle[^>]*w:val=["\']([^"\']*)["\']',
        r'rStyle[^>]*val=["\']([^"\']*)["\']',
    ]
    for pattern in r_style_patterns:
        r_style_match = re.search(pattern, xml_content, re.IGNORECASE | re.DOTALL)
        if r_style_match:
            style_ids["run_style"] = r_style_match.group(1)
            break
    
    # 提取单元格样式 w:tcStyle w:val="样式ID"
    tc_style_patterns = [
        r'<w:tcStyle[^>]*w:val=["\']([^"\']*)["\']',
        r'w:tcStyle[^>]*w:val=["\']([^"\']*)["\']',
        r'tcStyle[^>]*val=["\']([^"\']*)["\']',
    ]
    for pattern in tc_style_patterns:
        tc_style_match = re.search(pattern, xml_content, re.IGNORECASE | re.DOTALL)
        if tc_style_match:
            style_ids["cell_style"] = tc_style_match.group(1)
            break
    
    return style_ids


def get_default_style_id(styles_xml: str, style_type: str) -> Optional[str]:
    """
    从styles.xml中获取默认样式ID
    
    Args:
        styles_xml: styles.xml的完整XML内容
        style_type: 样式类型: "paragraph", "table", "character", "numbering"
        
    Returns:
        默认样式ID，如果未找到则返回None
    """
    if not styles_xml or not style_type:
        return None
    
    try:
        from lxml import etree
        
        namespaces = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
        styles_tree = etree.fromstring(styles_xml.encode('utf-8') if isinstance(styles_xml, str) else styles_xml)
        
        # 查找默认样式：w:default="1" 或 w:styleId="1" (段落默认样式通常是 "1" 或 "Normal")
        xpath_query = f'//w:style[@w:type="{style_type}" and @w:default="1"]/@w:styleId'
        default_styles = styles_tree.xpath(xpath_query, namespaces=namespaces)
        
        if default_styles:
            return default_styles[0]
        
        # 如果没有找到 w:default="1"，尝试查找 styleId="1" 的样式（段落默认样式通常是 "1"）
        if style_type == "paragraph":
            xpath_query = '//w:style[@w:type="paragraph" and @w:styleId="1"]/@w:styleId'
            style_id_1 = styles_tree.xpath(xpath_query, namespaces=namespaces)
            if style_id_1:
                return "1"
        
        return None
        
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(f"查找默认样式失败: {e}")
        return None


def extract_style_from_styles_xml(
    styles_xml: str, style_id: str, style_type: str = None
) -> Optional[str]:
    """
    从styles.xml中提取指定样式ID的样式XML定义
    
    Args:
        styles_xml: styles.xml的完整XML内容
        style_id: 要查找的样式ID
        style_type: 样式类型 (可选): "paragraph", "table", "character", "numbering"
        
    Returns:
        样式的完整XML字符串，如果未找到则返回None
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
        
        # 返回样式的完整XML字符串
        return etree.tostring(style_element, encoding='unicode', pretty_print=True)
        
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"从styles.xml提取样式失败: {e}", exc_info=True)
        return None


def extract_styles_from_document_xml_fragment(
    document_xml_fragment: str, styles_xml: str
) -> Dict[str, Optional[str]]:
    """
    根据document.xml的XML片段提取对应的styles.xml中的样式XML
    
    Args:
        document_xml_fragment: document.xml中的XML片段（如段落、表格、文本运行等）
        styles_xml: styles.xml的完整XML内容
        
    Returns:
        包含提取到的样式XML的字典:
        - paragraph_style: 段落样式XML字符串（如果有）
        - table_style: 表格样式XML字符串（如果有）
        - run_style: 文本运行样式XML字符串（如果有）
        - cell_style: 单元格样式XML字符串（如果有）
    """
    result = {
        "paragraph_style": None,
        "table_style": None,
        "run_style": None,
        "cell_style": None,
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
        
        # 提取每个样式的XML
        for style_key, style_id in style_ids.items():
            if style_id:
                try:
                    style_type = style_type_map.get(style_key)
                    style_xml = extract_style_from_styles_xml(styles_xml, style_id, style_type)
                    
                    if style_xml:
                        result[style_key] = style_xml
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


def create_docx_with_table_and_styles(
    table_xml: str, styles_dict: Dict[str, Optional[str]], output_path: str
) -> bool:
    """
    创建包含表格和样式的临时DOCX文件
    支持表格前后包含段落（标题、注释等）
    
    Args:
        table_xml: 表格的XML字符串，可以是：
                   - 单独的<w:tbl>元素
                   - 包含段落和表格的XML片段（多个<w:p>和<w:tbl>元素）
        styles_dict: 样式字典，包含 paragraph_style, table_style, run_style, cell_style 的XML字符串
        output_path: 输出文件路径
        
    Returns:
        成功返回True，失败返回False
    """
    try:
        from zipfile import ZipFile, ZIP_DEFLATED
        from lxml import etree
        from io import BytesIO
        
        # 创建一个新的空DOCX文档作为模板
        doc = Document()
        template_buffer = BytesIO()
        doc.save(template_buffer)
        template_buffer.seek(0)
        
        # 读取模板DOCX并修改
        with ZipFile(template_buffer, 'r') as template_zip:
            # 创建新的ZIP文件
            output_buffer = BytesIO()
            with ZipFile(output_buffer, 'w', ZIP_DEFLATED) as new_zip:
                # 复制模板中的所有文件（跳过document.xml和styles.xml，后面会写入）
                files_to_skip = {'word/document.xml', 'word/styles.xml'}
                for item in template_zip.infolist():
                    if item.filename not in files_to_skip:
                        data = template_zip.read(item.filename)
                        # 使用文件名而不是ZipInfo对象，避免重复警告
                        new_zip.writestr(item.filename, data)
                
                # 修改 document.xml，添加表格和段落
                namespaces = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
                doc_xml = template_zip.read('word/document.xml')
                doc_tree = etree.fromstring(doc_xml)
                
                # 解析XML内容（可能包含段落和表格）
                # 使用XMLParser保留空格属性
                parser = etree.XMLParser(remove_blank_text=False)
                try:
                    # 尝试解析为单个XML文档
                    content_tree = etree.fromstring(table_xml.encode('utf-8'), parser=parser)
                    elements_to_add = [content_tree]
                except etree.XMLSyntaxError:
                    # 如果包含多个根元素，尝试包装在临时根元素中
                    try:
                        wrapped_xml = f"<root xmlns:w=\"{namespaces['w']}\">{table_xml}</root>"
                        wrapped_tree = etree.fromstring(wrapped_xml.encode('utf-8'), parser=parser)
                        elements_to_add = list(wrapped_tree)
                    except Exception:
                        # 如果还是失败，尝试使用正则表达式提取段落和表格
                        import re
                        elements_to_add = []
                        # 提取所有段落
                        para_matches = re.findall(r'<w:p[^>]*>.*?</w:p>', table_xml, re.DOTALL)
                        for para_xml in para_matches:
                            try:
                                para_tree = etree.fromstring(para_xml.encode('utf-8'), parser=parser)
                                elements_to_add.append(para_tree)
                            except:
                                pass
                        # 提取表格
                        tbl_matches = re.findall(r'<w:tbl[^>]*>.*?</w:tbl>', table_xml, re.DOTALL)
                        for tbl_xml in tbl_matches:
                            try:
                                tbl_tree = etree.fromstring(tbl_xml.encode('utf-8'), parser=parser)
                                elements_to_add.append(tbl_tree)
                            except:
                                pass
                
                # 递归复制元素，保留所有属性（包括xml:space）
                def deep_copy_element(source_elem, target_parent, target_ns):
                    """递归复制元素，保留所有属性和命名空间"""
                    if source_elem.tag.startswith('{'):
                        # 提取命名空间和标签名
                        ns, tag = source_elem.tag[1:].split('}', 1)
                        if ns == namespaces['w']:
                            new_elem = etree.SubElement(target_parent, source_elem.tag)
                        else:
                            # 保持原始命名空间
                            new_elem = etree.SubElement(target_parent, source_elem.tag)
                    else:
                        # 没有命名空间，添加默认命名空间
                        new_elem = etree.SubElement(target_parent, f"{{{target_ns}}}{source_elem.tag}")
                    
                    # 复制所有属性（包括xml:space）
                    for attr, value in source_elem.attrib.items():
                        new_elem.set(attr, value)
                    
                    # 复制文本内容
                    if source_elem.text is not None:
                        new_elem.text = source_elem.text
                    
                    # 递归复制子元素
                    for child in source_elem:
                        deep_copy_element(child, new_elem, target_ns)
                    
                    # 复制tail文本
                    if source_elem.tail is not None:
                        new_elem.tail = source_elem.tail
                    
                    return new_elem
                
                # 清空body并添加所有元素（段落和表格）
                body = doc_tree.xpath('//w:body', namespaces=namespaces)[0]
                # 移除body中的所有子元素
                for child in list(body):
                    body.remove(child)
                
                # 按顺序添加所有元素（保持段落和表格的原始顺序）
                for element in elements_to_add:
                    deep_copy_element(element, body, namespaces['w'])
                
                # 保存修改后的document.xml，使用method='xml'确保保留所有属性
                new_doc_xml = etree.tostring(
                    doc_tree, 
                    encoding='utf-8', 
                    xml_declaration=True,
                    method='xml',
                    pretty_print=False  # 不格式化，保持原始格式
                )
                new_zip.writestr('word/document.xml', new_doc_xml)
                
                # 从 styles_dict 构建完整的 styles.xml，完全覆盖原来的
                styles_xml_content = build_styles_xml_from_dict(styles_dict)
                if styles_xml_content:
                    new_zip.writestr('word/styles.xml', styles_xml_content.encode('utf-8'))
            
            # 将新ZIP文件写入磁盘
            output_buffer.seek(0)
            with open(output_path, 'wb') as f:
                f.write(output_buffer.getvalue())
        
        return True
        
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"创建DOCX文件失败: {e}", exc_info=True)
        return False


def build_styles_xml_from_dict(styles_dict: Dict[str, Optional[str]]) -> Optional[str]:
    """
    从样式字典构建完整的 styles.xml，完全覆盖原来的内容
    
    Args:
        styles_dict: 样式字典，包含 paragraph_style, table_style, run_style, cell_style 的XML字符串
        
    Returns:
        完整的 styles.xml 的 XML 字符串
    """
    try:
        from lxml import etree
        import logging
        logger = logging.getLogger(__name__)
        
        namespaces = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
        
        # 创建新的 styles 根元素
        styles_root = etree.Element(
            '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}styles',
            nsmap=namespaces
        )
        
        # 添加样式字典中的所有样式
        for style_key, style_xml in styles_dict.items():
            if style_xml:
                try:
                    # 解析样式XML
                    style_element = etree.fromstring(style_xml.encode('utf-8'))
                    # 添加到根元素
                    styles_root.append(style_element)
                except Exception as e:
                    logger.warning(f"解析样式XML失败 ({style_key}): {e}")
                    continue
        
        # 如果没有样式，至少创建一个基本的styles.xml结构
        if len(styles_root) == 0:
            # 创建一个默认段落样式
            default_style = etree.SubElement(
                styles_root,
                '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}style',
                attrib={
                    '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}type': 'paragraph',
                    '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}styleId': 'Normal',
                    '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}default': '1'
                }
            )
            name_elem = etree.SubElement(
                default_style,
                '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}name',
                attrib={
                    '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}val': 'Normal'
                }
            )
        
        # 转换为字符串
        styles_xml_str = etree.tostring(
            styles_root,
            encoding='utf-8',
            xml_declaration=True,
            pretty_print=True
        ).decode('utf-8')
        
        return styles_xml_str
        
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"构建styles.xml失败: {e}", exc_info=True)
        return None


