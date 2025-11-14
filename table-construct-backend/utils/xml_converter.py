"""
XML 和 HTML 转换工具
"""

import re
from typing import Optional
from utils.coze import xml_to_html_chain


async def xml_to_html(xml_content: str) -> str:
    """
    将Word XML表格转换为HTML格式
    使用正则表达式替换标签名，保持表格结构和样式信息

    Args:
        xml_content: Word XML表格内容字符串

    Returns:
        转换后的HTML字符串
    """
    if not xml_content:
        return ""

    html = xml_content

    # 移除XML命名空间声明
    html = re.sub(r'\s*xmlns[^=]*="[^"]*"', "", html)

    response = await xml_to_html_chain.ainvoke({"raw_xml": html})
    return response.content


def html_to_xml(html_content: str) -> str:
    """
    将HTML格式的表格转换回Word XML格式
    使用正则表达式进行标签名替换，参考xml_to_html函数的实现方式

    Args:
        html_content: HTML表格内容字符串

    Returns:
        转换后的Word XML字符串
    """
    if not html_content:
        return ""

    xml = html_content

    # 转换CSS样式属性为Word XML属性
    def convert_style_attr(match):
        tag_start = match.group(1)
        style_content = match.group(2)
        tag_end = match.group(3)

        xml_attrs = []

        # text-align -> w:jc
        align_match = re.search(
            r"text-align\s*:\s*([^;]+)", style_content, re.IGNORECASE
        )
        if align_match:
            align_val = align_match.group(1).strip().lower()
            align_map = {
                "left": "left",
                "center": "center",
                "right": "right",
                "justify": "both",
            }
            jc_val = align_map.get(align_val, "left")
            xml_attrs.append(f'w:jc="{jc_val}"')

        # vertical-align -> w:valign
        valign_match = re.search(
            r"vertical-align\s*:\s*([^;]+)", style_content, re.IGNORECASE
        )
        if valign_match:
            valign_val = valign_match.group(1).strip().lower()
            valign_map = {"top": "top", "middle": "center", "bottom": "bottom"}
            w_valign = valign_map.get(valign_val, "top")
            xml_attrs.append(f'w:valign="{w_valign}"')

        # background-color -> w:shd w:fill
        bg_match = re.search(
            r"background-color\s*:\s*#?([^;]+)", style_content, re.IGNORECASE
        )
        if bg_match:
            bg_val = bg_match.group(1).strip()
            if bg_val and bg_val.upper() != "FFFFFF":
                xml_attrs.append(f'w:shd w:fill="{bg_val}"')

        # color -> w:color
        color_match = re.search(r"color\s*:\s*#?([^;]+)", style_content, re.IGNORECASE)
        if color_match:
            color_val = color_match.group(1).strip()
            if color_val and color_val.upper() != "000000":
                xml_attrs.append(f'w:color="{color_val}"')

        # font-size -> w:sz (pt转回sz值，sz值=pt*2)
        size_match = re.search(
            r"font-size\s*:\s*([0-9.]+)pt", style_content, re.IGNORECASE
        )
        if size_match:
            pt_val = float(size_match.group(1))
            sz_val = int(pt_val * 2)
            xml_attrs.append(f'w:sz="{sz_val}"')

        # width -> w:w
        width_match = re.search(
            r"width\s*:\s*([0-9.]+)(pt|%)", style_content, re.IGNORECASE
        )
        if width_match:
            width_val = width_match.group(1)
            width_unit = width_match.group(2).lower()
            if width_unit == "pt":
                twips = int(float(width_val) * 20)
                xml_attrs.append(f'w:w="{twips}" w:type="dxa"')
            elif width_unit == "%":
                xml_attrs.append(f'w:w="{width_val}" w:type="pct"')

        # 构建新的标签
        if xml_attrs:
            attrs_str = " " + " ".join(xml_attrs)
            return f"{tag_start}{attrs_str}{tag_end}"
        else:
            return f"{tag_start}{tag_end}"

    # 处理所有包含style属性的标签
    xml = re.sub(
        r'(<[^>]*?)\s+style\s*=\s*"([^"]*)"([^>]*>)',
        convert_style_attr,
        xml,
        flags=re.IGNORECASE,
    )

    # 转换表格相关标签
    # table -> w:tbl
    xml = re.sub(r"<table\b", "<w:tbl", xml, flags=re.IGNORECASE)
    xml = re.sub(r"</table>", "</w:tbl>", xml, flags=re.IGNORECASE)

    # tr -> w:tr
    xml = re.sub(r"<tr\b", "<w:tr", xml, flags=re.IGNORECASE)
    xml = re.sub(r"</tr>", "</w:tr>", xml, flags=re.IGNORECASE)

    # td/th -> w:tc
    xml = re.sub(r"<td\b", "<w:tc", xml, flags=re.IGNORECASE)
    xml = re.sub(r"</td>", "</w:tc>", xml, flags=re.IGNORECASE)
    xml = re.sub(r"<th\b", "<w:tc", xml, flags=re.IGNORECASE)
    xml = re.sub(r"</th>", "</w:tc>", xml, flags=re.IGNORECASE)

    # p -> w:p
    xml = re.sub(r"<p\b", "<w:p", xml, flags=re.IGNORECASE)
    xml = re.sub(r"</p>", "</w:p>", xml, flags=re.IGNORECASE)

    # span -> w:r
    xml = re.sub(r"<span\b", "<w:r", xml, flags=re.IGNORECASE)
    xml = re.sub(r"</span>", "</w:r>", xml, flags=re.IGNORECASE)

    # 将文本内容包装在w:t标签中
    # 处理w:r标签内的直接文本
    def wrap_text_in_r(match):
        tag_start = match.group(1)
        text_content = match.group(2)
        tag_end = match.group(3)
        if text_content.strip():
            return f"{tag_start}<w:t>{text_content}</w:t>{tag_end}"
        return f"{tag_start}{tag_end}"

    xml = re.sub(
        r"(<w:r[^>]*>)([^<]+)(</w:r>)", wrap_text_in_r, xml, flags=re.IGNORECASE
    )

    # 处理w:p标签内的直接文本（如果没有w:r包装）
    def wrap_text_in_p(match):
        tag_start = match.group(1)
        text_content = match.group(2)
        tag_end = match.group(3)
        if text_content.strip():
            return f"{tag_start}<w:r><w:t>{text_content}</w:t></w:r>{tag_end}"
        return f"{tag_start}{tag_end}"

    xml = re.sub(
        r"(<w:p[^>]*>)([^<]+)(</w:p>)", wrap_text_in_p, xml, flags=re.IGNORECASE
    )

    # 处理w:tc标签内的直接文本（如果没有w:p包装）
    def wrap_text_in_tc(match):
        tag_start = match.group(1)
        text_content = match.group(2)
        tag_end = match.group(3)
        if text_content.strip():
            return (
                f"{tag_start}<w:p><w:r><w:t>{text_content}</w:t></w:r></w:p>{tag_end}"
            )
        return f"{tag_start}{tag_end}"

    xml = re.sub(
        r"(<w:tc[^>]*>)([^<]+)(</w:tc>)", wrap_text_in_tc, xml, flags=re.IGNORECASE
    )

    # 添加XML命名空间声明（如果需要）
    if "<w:tbl" in xml and "xmlns:w=" not in xml:
        xml = xml.replace(
            "<w:tbl",
            '<w:tbl xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"',
            1,
        )

    # 清理多余的空白
    xml = re.sub(r"\s+", " ", xml)
    xml = re.sub(r">\s+<", "><", xml)
    xml = xml.strip()

    return xml
