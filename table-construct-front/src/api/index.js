import axios from 'axios'
import { xml2html } from '../utils/xml2html.js'

const instance = axios.create({
  baseURL: process.env.VUE_APP_API_BASE_URL || '',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json'
  }
})

instance.interceptors.request.use(
  config => {
    // 如果是 FormData，删除 Content-Type 让浏览器自动设置（包括 boundary）
    if (config.data instanceof FormData) {
      delete config.headers['Content-Type']
    }
    return config
  },
  error => {
    console.error('Request error:', error)
    return Promise.reject(error)
  }
)

instance.interceptors.response.use(
  response => {
    return response.data
  },
  error => {
    if (error.response) {
      console.error('Response error:', error.response.status, error.response.statusText)
    } else if (error.request) {
      console.error('Request error: No response received')
    } else {
      console.error('Error:', error.message)
    }
    return Promise.reject(error)
  }
)

export const request = (config) => {
  return instance(config)
}

export const get = (url, params) => {
  return instance.get(url, { params })
}

export const post = (url, data) => {
  return instance.post(url, data)
}

export const put = (url, data) => {
  return instance.put(url, data)
}

export const del = (url, params) => {
  return instance.delete(url, { params })
}

/**
 * 上传文件到服务器
 * @param {File} file - 要上传的.docx文件
 * @returns {Promise<Object>} 上传结果
 */
export const uploadFile = async (file) => {
  if (!file) {
    throw new Error('文件不能为空')
  }

  if (!file.name || !file.name.toLowerCase().endsWith('.docx')) {
    throw new Error('只支持.docx格式的文件')
  }

  const MAX_FILE_SIZE = 10 * 1024 * 1024
  if (file.size > MAX_FILE_SIZE) {
    throw new Error(`文件大小超过限制（最大10MB），当前文件大小：${(file.size / (1024 * 1024)).toFixed(2)}MB`)
  }

  try {
    const formData = new FormData()
    formData.append('file', file)

    // 不手动设置 Content-Type，让浏览器自动设置（包括 boundary）
    const response = await instance.post('/api/upload', formData, {
      timeout: 60000
    })

    if (response.success) {
      return response
    } else {
      throw new Error(response.message || '上传失败')
    }
  } catch (error) {
    if (error.response) {
      const errorMessage = error.response.data?.message || error.response.data?.detail || '上传失败'
      throw new Error(errorMessage)
    } else if (error.request) {
      throw new Error('网络错误，请检查网络连接')
    } else {
      throw new Error(error.message || '上传失败')
    }
  }
}

/**
 * 查询表格
 * @param {Object} params - 查询参数
 * @param {string} params.query - 查询关键词
 * @param {number} params.top_k - 返回数量，默认10
 * @param {number} params.threshold - 相似度阈值（可选）
 * @returns {Promise<Array>} 查询结果列表
 */
export const queryTables = async ({ query = '', top_k = 10, threshold = null }) => {
  if (!query || !query.trim()) {
    throw new Error('查询关键词不能为空')
  }

  if (top_k < 1) {
    throw new Error('返回数量必须大于0')
  }

  try {
    const requestBody = {
      query: query.trim(),
      top_k: top_k
    }
    
    // 只有当threshold不为null时才添加到请求中
    if (threshold !== null && threshold !== undefined) {
      requestBody.threshold = threshold
    }
    
    const response = await instance.post('/api/query', requestBody)

    if (response.success) {
      const data = response.data || []
      return data.map(item => {
        const tableId = item.table_id || item.id || ''
        const tableXml = item.table_xml || item.document || ''
        const metadata = item.metadata || {}

        let tableHtml = ''
        if (tableXml) {
          tableHtml = xml2html(tableXml)
        }

        return {
          id: tableId,
          html: tableHtml,
          xml: tableXml,
          similarity: item.similarity || 0,
          metadata: metadata
        }
      })
    } else {
      throw new Error(response.message || '查询失败')
    }
  } catch (error) {
    if (error.response) {
      const errorMessage = error.response.data?.message || error.response.data?.detail || '查询失败'
      throw new Error(errorMessage)
    } else if (error.request) {
      throw new Error('网络错误，请检查网络连接')
    } else {
      throw new Error(error.message || '查询失败')
    }
  }
}

/**
 * 下载表格
 * @param {Array<string>} tableIds - 表格ID数组
 * @returns {Promise<Blob>} 下载的文件blob
 */
export const downloadTables = async (tableIds) => {
  if (!tableIds || !Array.isArray(tableIds) || tableIds.length === 0) {
    throw new Error('表格ID数组不能为空')
  }

  try {
    const response = await instance.post('/api/download', {
      table_ids: tableIds
    }, {
      responseType: 'blob',
      timeout: 60000
    })

    if (response instanceof Blob) {
      return response
    } else {
      throw new Error('下载失败：返回数据格式错误')
    }
  } catch (error) {
    if (error.response) {
      if (error.response.data instanceof Blob) {
        try {
          const errorText = await new Promise((resolve, reject) => {
            const reader = new FileReader()
            reader.onload = () => resolve(reader.result)
            reader.onerror = () => reject(new Error('读取错误信息失败'))
            reader.readAsText(error.response.data)
          })
          const errorJson = JSON.parse(errorText)
          throw new Error(errorJson.message || errorJson.detail || '下载失败')
        } catch (parseError) {
          if (parseError instanceof Error && parseError.message !== '下载失败' && parseError.message !== '读取错误信息失败') {
            throw parseError
          }
          throw new Error('下载失败')
        }
      } else {
        const errorMessage = error.response.data?.message || error.response.data?.detail || '下载失败'
        throw new Error(errorMessage)
      }
    } else if (error.request) {
      throw new Error('网络错误，请检查网络连接')
    } else {
      throw new Error(error.message || '下载失败')
    }
  }
}

/**
 * HTML转XML（TODO: 完整实现）
 * @param {string} htmlContent - HTML内容
 * @returns {string} XML内容
 */
// const htmlToXml = (htmlContent) => {
//   if (!htmlContent) {
//     return ''
//   }
//   return htmlContent
// }

export default {
  request,
  get,
  post,
  put,
  delete: del,
  uploadFile,
  queryTables,
  downloadTables
}
