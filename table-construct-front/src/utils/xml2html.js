/**
 * XML 转 HTML 工具函数
 * 提供将 XML 字符串转换为 HTML 字符串的功能
 */

/**
 * 转义 HTML 特殊字符
 * @param {string} text - 需要转义的文本
 * @returns {string} 转义后的文本
 */
function escapeHtml(text) {
  if (typeof text !== 'string') {
    return ''
  }
  const map = {
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    '"': '&quot;',
    "'": '&#39;'
  }
  return text.replace(/[&<>"']/g, (char) => map[char])
}

/**
 * 解析 XML 字符串为 DOM 节点
 * @param {string} xmlString - XML 字符串
 * @returns {Document|null} 解析后的 DOM 文档对象
 */
function parseXML(xmlString) {
  if (typeof xmlString !== 'string' || !xmlString.trim()) {
    return null
  }

  try {
    const parser = new DOMParser()
    const xmlDoc = parser.parseFromString(xmlString, 'text/xml')
    
    // 检查解析错误
    const parserError = xmlDoc.querySelector('parsererror')
    if (parserError) {
      const errorText = parserError.textContent || 'XML parsing error'
      console.error('XML parsing error:', errorText)
      return null
    }
    
    return xmlDoc
  } catch (error) {
    console.error('XML parsing error:', error)
    return null
  }
}

/**
 * 将 XML 节点转换为 HTML 字符串
 * @param {Node} node - XML 节点
 * @param {Object} options - 转换选项
 * @param {boolean} options.preserveAttributes - 是否保留所有属性，默认为 true
 * @param {boolean} options.preserveTextNodes - 是否保留文本节点，默认为 true
 * @param {Object} options.tagMapping - 标签映射对象，用于将 XML 标签映射为 HTML 标签
 * @returns {string} HTML 字符串
 */
function nodeToHtml(node, options = {}) {
  const {
    preserveAttributes = true,
    preserveTextNodes = true,
    tagMapping = {}
  } = options

  if (!node) {
    return ''
  }

  // 处理文本节点
  if (node.nodeType === Node.TEXT_NODE) {
    if (!preserveTextNodes) {
      return ''
    }
    const text = node.textContent || ''
    return escapeHtml(text.trim())
  }

  // 处理 CDATA 节点
  if (node.nodeType === Node.CDATA_SECTION_NODE) {
    return node.textContent || ''
  }

  // 处理元素节点
  if (node.nodeType === Node.ELEMENT_NODE) {
    const tagName = node.tagName ? node.tagName.toLowerCase() : ''
    const htmlTagName = tagMapping[tagName] || tagName || 'div'
    
    let html = `<${htmlTagName}`
    
    // 处理属性
    if (preserveAttributes && node.attributes) {
      for (let i = 0; i < node.attributes.length; i++) {
        const attr = node.attributes[i]
        const attrName = attr.name || attr.nodeName
        const attrValue = attr.value || attr.nodeValue || ''
        html += ` ${attrName}="${escapeHtml(attrValue)}"`
      }
    }
    
    // 处理子节点
    const children = node.childNodes || []
    let hasChildren = false
    let childrenHtml = ''
    
    for (let i = 0; i < children.length; i++) {
      const childHtml = nodeToHtml(children[i], options)
      if (childHtml) {
        childrenHtml += childHtml
        hasChildren = true
      }
    }
    
    // 自闭合标签处理
    const selfClosingTags = ['br', 'hr', 'img', 'input', 'meta', 'link', 'area', 'base', 'col', 'embed', 'source', 'track', 'wbr']
    if (selfClosingTags.includes(htmlTagName) && !hasChildren) {
      html += ' />'
      return html
    }
    
    html += '>'
    if (hasChildren) {
      html += childrenHtml
    }
    html += `</${htmlTagName}>`
    
    return html
  }

  // 处理注释节点
  if (node.nodeType === Node.COMMENT_NODE) {
    return `<!--${node.textContent || ''}-->`
  }

  // 处理文档节点
  if (node.nodeType === Node.DOCUMENT_NODE || node.nodeType === Node.DOCUMENT_FRAGMENT_NODE) {
    let html = ''
    const children = node.childNodes || []
    for (let i = 0; i < children.length; i++) {
      html += nodeToHtml(children[i], options)
    }
    return html
  }

  return ''
}

/**
 * 将 XML 字符串转换为 HTML 字符串
 * @param {string} xmlString - XML 字符串
 * @param {Object} options - 转换选项
 * @param {boolean} options.preserveAttributes - 是否保留所有属性，默认为 true
 * @param {boolean} options.preserveTextNodes - 是否保留文本节点，默认为 true
 * @param {Object} options.tagMapping - 标签映射对象，用于将 XML 标签映射为 HTML 标签
 * @param {string} options.wrapperTag - 包装标签，如果提供，会将结果包装在此标签中
 * @returns {string} HTML 字符串
 */
export function xml2html(xmlString, options = {}) {
  if (typeof xmlString !== 'string' || !xmlString.trim()) {
    return ''
  }

  const {
    preserveAttributes = true,
    preserveTextNodes = true,
    tagMapping = {},
    wrapperTag = ''
  } = options

  const xmlDoc = parseXML(xmlString)
  if (!xmlDoc) {
    return ''
  }

  const html = nodeToHtml(xmlDoc.documentElement || xmlDoc, {
    preserveAttributes,
    preserveTextNodes,
    tagMapping
  })

  if (wrapperTag) {
    return `<${wrapperTag}>${html}</${wrapperTag}>`
  }

  return html
}

/**
 * 将 XML 字符串转换为格式化的 HTML 字符串（带缩进）
 * @param {string} xmlString - XML 字符串
 * @param {Object} options - 转换选项
 * @param {number} options.indentSize - 缩进大小，默认为 2
 * @param {string} options.indentChar - 缩进字符，默认为空格
 * @returns {string} 格式化后的 HTML 字符串
 */
export function xml2htmlFormatted(xmlString, options = {}) {
  const html = xml2html(xmlString, options)
  if (!html) {
    return ''
  }

  const {
    indentSize = 2,
    indentChar = ' '
  } = options

  // 简单的格式化处理
  let formatted = ''
  let indentLevel = 0
  const indent = indentChar.repeat(indentSize)
  
  // 使用正则表达式添加换行和缩进
  formatted = html
    .replace(/></g, '>\n<')
    .split('\n')
    .map((line) => {
      const trimmed = line.trim()
      if (!trimmed) {
        return ''
      }
      
      if (trimmed.startsWith('</')) {
        indentLevel = Math.max(0, indentLevel - 1)
      }
      
      const indentedLine = indent.repeat(indentLevel) + trimmed
      
      if (trimmed.startsWith('<') && !trimmed.startsWith('</') && !trimmed.endsWith('/>')) {
        indentLevel++
      }
      
      return indentedLine
    })
    .filter((line) => line)
    .join('\n')

  return formatted
}

/**
 * 将 XML 字符串转换为 HTML 片段（不包含根标签）
 * @param {string} xmlString - XML 字符串
 * @param {Object} options - 转换选项
 * @returns {string} HTML 片段字符串
 */
export function xml2htmlFragment(xmlString, options = {}) {
  if (typeof xmlString !== 'string' || !xmlString.trim()) {
    return ''
  }

  const xmlDoc = parseXML(xmlString)
  if (!xmlDoc) {
    return ''
  }

  const {
    preserveAttributes = true,
    preserveTextNodes = true,
    tagMapping = {}
  } = options

  let html = ''
  const rootElement = xmlDoc.documentElement || xmlDoc
  const children = rootElement.childNodes || []
  
  for (let i = 0; i < children.length; i++) {
    html += nodeToHtml(children[i], {
      preserveAttributes,
      preserveTextNodes,
      tagMapping
    })
  }

  return html
}
