# Table Construct System API 接口文档

## 概述

Table Construct System 是一个表格构建系统后端 API，提供文件上传、表格查询和导出功能。

- **基础路径**: `/api`
- **API 版本**: `0.1.0`
- **默认端口**: `3000`

---

## 目录

- [1. 文件上传接口](#1-文件上传接口)
- [2. 查询接口](#2-查询接口)
- [3. 导出接口](#3-导出接口)
- [4. 健康检查接口](#4-健康检查接口)
- [5. 根路径接口](#5-根路径接口)

---

## 1. 文件上传接口

### 1.1 上传文件

上传 `.docx` 文件，系统会解析文件中的表格并存入 ChromaDB 向量数据库。

**接口地址**: `POST /api/upload`

**请求头**:
```
Content-Type: multipart/form-data
```

**请求参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| file | File | 是 | 要上传的 .docx 文件，最大 50MB |

**请求示例**:

```bash
curl -X POST "http://localhost:3000/api/upload" \
  -F "file=@example.docx"
```

**响应模型**: `UploadResponse`

**响应字段**:

| 字段名 | 类型 | 说明 |
|--------|------|------|
| success | boolean | 请求是否成功 |
| message | string | 响应消息 |
| data | object | 响应数据（可选） |

**响应示例**:

```json
{
  "success": true,
  "message": "文件上传成功",
  "data": {
    "file_id": "xxx",
    "tables_count": 5
  }
}
```

**错误响应**:

```json
{
  "success": false,
  "message": "文件格式不支持",
  "data": null
}
```

---

## 2. 查询接口

### 2.1 GET 方式查询

使用 GET 方法进行表格查询，通过查询参数传递参数。

**接口地址**: `GET /api/query`

**请求参数**:

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|--------|------|
| query | string | 是 | - | 查询文本 |
| top_k | integer | 否 | 10 | 返回结果数量 |
| threshold | float | 否 | null | 相似度阈值（0-1之间） |

**请求示例**:

```bash
curl -X GET "http://localhost:3000/api/query?query=销售数据&top_k=5&threshold=0.7"
```

**响应模型**: `QueryResponse`

**响应字段**:

| 字段名 | 类型 | 说明 |
|--------|------|------|
| success | boolean | 请求是否成功 |
| message | string | 响应消息 |
| data | array | 查询结果列表（可选） |

**响应数据项结构**:

| 字段名 | 类型 | 说明 |
|--------|------|------|
| id | string | 表格ID |
| distance | float | 相似度距离 |
| metadata | object | 表格元数据 |
| document | object | 表格数据 |

**响应示例**:

```json
{
  "success": true,
  "message": "查询成功",
  "data": [
    {
      "id": "table_123",
      "distance": 0.85,
      "metadata": {
        "file_name": "example.docx",
        "table_index": 0
      },
      "document": {
        "table_data": "..."
      }
    }
  ]
}
```

### 2.2 POST 方式查询

使用 POST 方法进行表格查询，通过请求体传递参数。

**接口地址**: `POST /api/query`

**请求头**:
```
Content-Type: application/json
```

**请求体**: `QueryRequest`

| 字段名 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|--------|------|
| query | string | 是 | - | 查询文本 |
| top_k | integer | 否 | 10 | 返回结果数量 |
| threshold | float | 否 | null | 相似度阈值（0-1之间） |

**请求示例**:

```bash
curl -X POST "http://localhost:3000/api/query" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "销售数据",
    "top_k": 5,
    "threshold": 0.7
  }'
```

**响应格式**: 同 GET 方式查询

---

## 3. 导出接口

### 3.1 导出表格

根据表格ID数组，从 ChromaDB 查询对应的表格数据，组装成新的 `.docx` 文件并返回。

**接口地址**: `POST /api/download`

**请求头**:
```
Content-Type: application/json
```

**请求体**: `ExportRequest`

| 字段名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| table_ids | array[string] | 是 | 要导出的表格ID数组 |

**请求示例**:

```bash
curl -X POST "http://localhost:3000/api/download" \
  -H "Content-Type: application/json" \
  -d '{
    "table_ids": ["table_123", "table_456"]
  }' \
  --output result.docx
```

**响应类型**: `FileResponse`

**响应头**:
```
Content-Type: application/vnd.openxmlformats-officedocument.wordprocessingml.document
Content-Disposition: attachment; filename="exported_tables.docx"
```

**响应说明**: 直接返回 `.docx` 文件流，客户端需要保存为文件。

**错误响应**:

如果请求失败，会返回 JSON 格式的错误信息：

```json
{
  "detail": "表格ID不存在"
}
```

---

## 4. 健康检查接口

### 4.1 健康检查

检查 API 服务是否正常运行。

**接口地址**: `GET /health`

**请求示例**:

```bash
curl -X GET "http://localhost:3000/health"
```

**响应示例**:

```json
{
  "status": "healthy"
}
```

---

## 5. 根路径接口

### 5.1 获取 API 信息

获取 API 的基本信息。

**接口地址**: `GET /`

**请求示例**:

```bash
curl -X GET "http://localhost:3000/"
```

**响应示例**:

```json
{
  "message": "Table Construct System API",
  "version": "0.1.0",
  "status": "running"
}
```

---

## 数据模型

### QueryRequest

查询请求模型

```json
{
  "query": "string",
  "top_k": 10,
  "threshold": 0.7
}
```

### QueryResponse

查询响应模型

```json
{
  "success": true,
  "message": "string",
  "data": [
    {
      "id": "string",
      "distance": 0.85,
      "metadata": {},
      "document": {}
    }
  ]
}
```

### UploadResponse

上传响应模型

```json
{
  "success": true,
  "message": "string",
  "data": {
    "file_id": "string",
    "tables_count": 5
  }
}
```

### ExportRequest

导出请求模型

```json
{
  "table_ids": ["string"]
}
```

---

## 错误码说明

| HTTP 状态码 | 说明 |
|------------|------|
| 200 | 请求成功 |
| 400 | 请求参数错误 |
| 404 | 资源不存在 |
| 422 | 请求参数验证失败 |
| 500 | 服务器内部错误 |

---

## 注意事项

1. **文件上传限制**:
   - 仅支持 `.docx` 格式文件
   - 文件大小限制：50MB

2. **查询接口**:
   - 支持 GET 和 POST 两种方式
   - `threshold` 参数用于过滤相似度，值越小要求越严格
   - `top_k` 参数控制返回结果数量

3. **导出接口**:
   - 返回的是文件流，需要客户端正确处理
   - 如果表格ID不存在，会返回错误信息

4. **CORS 配置**:
   - API 已配置 CORS，允许跨域请求
   - 允许所有来源、方法和请求头

---

## 示例代码

### Python 示例

```python
import requests

# 上传文件
with open('example.docx', 'rb') as f:
    response = requests.post(
        'http://localhost:3000/api/upload',
        files={'file': f}
    )
    print(response.json())

# 查询表格
response = requests.get(
    'http://localhost:3000/api/query',
    params={'query': '销售数据', 'top_k': 5}
)
print(response.json())

# 导出表格
response = requests.post(
    'http://localhost:3000/api/download',
    json={'table_ids': ['table_123', 'table_456']}
)
with open('exported.docx', 'wb') as f:
    f.write(response.content)
```

### JavaScript 示例

```javascript
// 上传文件
const formData = new FormData();
formData.append('file', fileInput.files[0]);

fetch('http://localhost:3000/api/upload', {
  method: 'POST',
  body: formData
})
.then(response => response.json())
.then(data => console.log(data));

// 查询表格
fetch('http://localhost:3000/api/query?query=销售数据&top_k=5')
  .then(response => response.json())
  .then(data => console.log(data));

// 导出表格
fetch('http://localhost:3000/api/download', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    table_ids: ['table_123', 'table_456']
  })
})
.then(response => response.blob())
.then(blob => {
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = 'exported.docx';
  a.click();
});
```

---

## 更新日志

- **v0.1.0** (当前版本)
  - 初始版本
  - 支持文件上传、查询和导出功能



