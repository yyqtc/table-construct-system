<template>
  <div class="display-page">
    <el-card class="search-card" shadow="hover">
      <div slot="header" class="search-header">
        <h2>
          <i class="el-icon-search"></i>
          智能表格搜索
        </h2>
        <el-button type="primary" icon="el-icon-upload2" @click="goToUpload">
          上传文档
        </el-button>
      </div>

      <!-- 搜索栏 -->
      <div class="search-bar">
        <el-input
          v-model="searchKeyword"
          placeholder="输入关键词搜索表格，例如：人员信息、销售数据、财务报表等..."
          size="large"
          @keyup.enter.native="handleSearch"
          class="search-input"
        >
          <el-button
            slot="append"
            icon="el-icon-search"
            @click="handleSearch"
            :loading="searching"
          >
            搜索
          </el-button>
        </el-input>
        
        <div class="search-options">
          <el-input-number
            v-model="topK"
            :min="1"
            :max="50"
            label="返回数量"
            size="small"
            class="option-input"
          ></el-input-number>
          <span class="option-label">返回结果数</span>
        </div>
      </div>

      <!-- 错误提示 -->
      <el-alert
        v-if="errorMessage"
        :title="errorMessage"
        type="error"
        :closable="true"
        @close="errorMessage = ''"
        show-icon
        class="error-alert"
      ></el-alert>
    </el-card>

    <!-- 搜索结果 -->
    <div v-if="hasResults" class="results-container">
      <!-- 主展示区 -->
      <el-card class="main-display-card" shadow="hover" v-loading="searching" element-loading-text="正在加载...">
        <div slot="header" class="display-header">
          <div class="header-left">
            <h3>
              <i class="el-icon-view"></i>
              表格详情
            </h3>
            <span v-if="currentTable" class="similarity-badge">
              相似度: {{ (currentTable.similarity * 100).toFixed(1) }}%
            </span>
          </div>
          <div class="header-actions">
            <el-button
              type="primary"
              icon="el-icon-plus"
              size="small"
              @click="addToSelected(currentTableId)"
              :disabled="!currentTableId"
            >
              添加到列表
            </el-button>
          </div>
        </div>
        
        <div class="table-display-wrapper">
          <div v-if="currentTablePdfUrl" class="table-container">
            <div class="table-wrapper">
              <iframe
                :src="currentTablePdfUrl"
                class="table-iframe"
              ></iframe>
            </div>
          </div>
          <div v-else class="empty-display">
            <i class="el-icon-document"></i>
            <p>请选择一个表格查看详情</p>
          </div>
        </div>
      </el-card>

      <!-- 结果列表 -->
      <el-card class="results-list-card" shadow="hover" v-loading="searching" element-loading-text="正在加载...">
        <div slot="header" class="list-header">
          <h3>
            <i class="el-icon-menu"></i>
            搜索结果 ({{ tableList.length }})
          </h3>
        </div>
        
        <div class="table-list">
          <div
            v-for="(table, index) in tableList"
            :key="table.id"
            class="table-item"
            :class="{ active: currentTableId === table.id }"
            @click="switchTable(table.id)"
          >
            <div class="table-item-header">
              <div class="table-info">
                <span class="table-number">表格 {{ index + 1 }}</span>
                <el-tag
                  :type="getSimilarityTagType(table.similarity)"
                  size="small"
                  class="similarity-tag"
                >
                  {{ (table.similarity * 100).toFixed(1) }}%
                </el-tag>
              </div>
              <el-button
                type="primary"
                icon="el-icon-plus"
                size="mini"
                circle
                @click.stop="addToSelected(table.id)"
              ></el-button>
            </div>
            
            <div class="table-preview">
              <iframe
                v-if="getTablePdfUrl(table)"
                :src="getTablePdfUrl(table)"
                class="preview-iframe"
              ></iframe>
              <div v-else class="preview-empty">无预览</div>
            </div>
          </div>
        </div>
      </el-card>

      <!-- 已选表格侧边栏 -->
      <el-card class="selected-sidebar" shadow="hover">
        <div slot="header" class="sidebar-header">
          <h3>
            <i class="el-icon-shopping-cart-full"></i>
            已选表格 ({{ selectedTables.length }})
          </h3>
          <el-button
            v-if="selectedTables.length > 0"
            type="text"
            size="small"
            @click="clearSelected"
          >
            清空
          </el-button>
        </div>

        <div v-if="selectedTables.length > 0" class="selected-content-wrapper">
          <div class="selected-list">
            <draggable
              v-model="selectedTables"
              :animation="200"
              handle=".drag-handle"
              @end="onDragEnd"
            >
              <div
                v-for="(tableItem, index) in selectedTables"
                :key="tableItem.uniqueId"
                class="selected-table-item"
                :class="{ active: currentTableId === tableItem.id }"
                @click="switchTable(tableItem.id)"
              >
                <div class="selected-table-header">
                  <div class="selected-table-info">
                    <i class="el-icon-rank drag-handle"></i>
                    <span class="selected-table-number">表格 {{ index + 1 }}</span>
                  </div>
                  <el-button
                    type="danger"
                    icon="el-icon-delete"
                    size="mini"
                    circle
                    @click.stop="removeSelectedByIndex(index)"
                  ></el-button>
                </div>
                
                <div class="selected-table-preview">
                  <iframe
                    v-if="getSelectedTablePdfUrl(tableItem)"
                    :src="getSelectedTablePdfUrl(tableItem)"
                    class="selected-preview-iframe"
                  ></iframe>
                  <div v-else class="selected-preview-empty">无预览</div>
                </div>
              </div>
            </draggable>
          </div>

          <div class="download-section">
            <el-button
              type="primary"
              icon="el-icon-download"
              size="medium"
              @click="handleDownload"
              :loading="downloading"
              class="download-btn"
            >
              {{ downloading ? '下载中...' : `下载文档 (${selectedTables.length})` }}
            </el-button>
          </div>
        </div>

        <div v-else class="empty-selected">
          <i class="el-icon-shopping-cart-2"></i>
          <p>暂无已选表格</p>
          <p class="empty-tip">点击表格上的 + 按钮添加到列表</p>
        </div>
      </el-card>
    </div>

    <!-- 空状态 -->
    <div v-else-if="!searching" class="empty-state">
      <el-card shadow="never" class="empty-card">
        <div class="empty-content">
          <i class="el-icon-search"></i>
          <h3>开始搜索表格</h3>
          <p>输入关键词搜索文档中的表格，系统会为您找到最相关的结果</p>
        </div>
      </el-card>
    </div>
  </div>
</template>

<script>
import { queryTables, downloadTables } from '../api'
import { getTableOrder, updateTableOrder, clearTableIds, getAllTableIds, setStorage, getStorage, StorageType, TABLE_IDS_KEY } from '../utils/storage'
import draggable from 'vuedraggable'

// 查询结果缓存键名
const QUERY_RESULT_CACHE_KEY = 'query_result_cache'
// 已选表格完整信息存储键名
const SELECTED_TABLES_ITEMS_KEY = 'selected_tables_items'

export default {
  name: 'DisplayView',
  components: {
    draggable
  },
  data() {
    return {
      searchKeyword: '',
      tableList: [],
      currentTableId: null,
      selectedTableIds: [], // 保持向后兼容，用于存储逻辑
      selectedTables: [], // 新的数据结构，包含完整的表格信息
      currentSelectedIndex: -1,
      searching: false,
      downloading: false,
      errorMessage: '',
      topK: 10
    }
  },
  computed: {
    hasResults() {
      return this.tableList.length > 0 && !this.searching
    },
    currentTable() {
      if (!this.currentTableId) return null
      return this.tableList.find(t => t.id === this.currentTableId)
    },
    currentTableHtml() {
      return this.currentTable ? this.currentTable.html : null
    },
    currentTablePdfUrl() {
      if (!this.currentTable) return null
      return this.getTablePdfUrl(this.currentTable)
    }
  },
  watch: {
    // 监听返回结果数的变化，更新缓存
    topK(newVal) {
      if (newVal && this.tableList.length > 0) {
        // 如果有查询结果，更新缓存中的 topK
        const cached = getStorage(QUERY_RESULT_CACHE_KEY, null, StorageType.SESSION)
        if (cached) {
          this.cacheQueryResult({
            ...cached,
            topK: newVal
          })
        }
      }
    },
    // 监听搜索关键词的变化，更新缓存
    searchKeyword(newVal) {
      if (newVal && this.tableList.length > 0) {
        // 如果有查询结果，更新缓存中的 keyword
        const cached = getStorage(QUERY_RESULT_CACHE_KEY, null, StorageType.SESSION)
        if (cached) {
          this.cacheQueryResult({
            ...cached,
            keyword: newVal
          })
        }
      }
    }
  },
  mounted() {
    this.loadSelectedTables()
    // 从 sessionStorage 恢复查询结果
    this.loadCachedQueryResult()
  },
  methods: {
    async handleSearch() {
      if (!this.searchKeyword.trim()) {
        this.$message.warning('请输入搜索关键词')
        return
      }
      
      this.searching = true
      this.errorMessage = ''
      this.tableList = []
      this.currentTableId = null
      
      try {
        const response = await queryTables({
          query: this.searchKeyword,
          top_k: this.topK
        })
        
        this.tableList = response || []
        
        // 缓存查询结果到 sessionStorage
        this.cacheQueryResult({
          keyword: this.searchKeyword,
          topK: this.topK,
          results: this.tableList,
          timestamp: Date.now()
        })
        
        // 同步已选表格（从存储中加载完整的表格项信息）
        this.syncSelectedTableIds()
        
        if (this.tableList.length > 0) {
          this.currentTableId = this.tableList[0].id
          this.$message.success(`找到 ${this.tableList.length} 个相关表格`)
        } else {
          this.$message.info('未找到相关表格，请尝试其他关键词')
        }
      } catch (error) {
        this.errorMessage = '搜索失败: ' + (error.message || '未知错误')
        this.$message.error(this.errorMessage)
      } finally {
        this.searching = false
      }
    },
    switchTable(tableId) {
      this.currentTableId = tableId
    },
    addToSelected(tableId) {
      if (!tableId) return
      
      // 查找对应的表格对象
      const table = this.tableList.find(t => t.id === tableId)
      if (!table) {
        this.$message.warning('表格不存在')
        return
      }
      
      // 生成唯一标识符（允许同一个表格选择多次）
      const uniqueId = `${tableId}_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
      
      // 创建完整的表格项（包含所有信息）
      const tableItem = {
        uniqueId: uniqueId,
        id: table.id,
        html: table.html,
        xml: table.xml,
        similarity: table.similarity,
        metadata: table.metadata
      }
      
      this.selectedTables.push(tableItem)
      
      // 保存完整的表格项信息到存储
      const storedItems = getStorage(SELECTED_TABLES_ITEMS_KEY, [], StorageType.SESSION)
      storedItems.push(tableItem)
      setStorage(SELECTED_TABLES_ITEMS_KEY, storedItems, StorageType.SESSION)
      
      // 同时保持 table_id 的存储（用于向后兼容和下载功能）
      const ids = getAllTableIds()
      ids.push(tableId)
      setStorage(TABLE_IDS_KEY, ids, StorageType.SESSION)
      
      const order = getTableOrder()
      order.push(tableId)
      updateTableOrder(order)
      
      this.$message.success('已添加到列表')
    },
    removeSelectedByIndex(index) {
      if (index < 0 || index >= this.selectedTables.length) return
      
      const tableItem = this.selectedTables[index]
      
      // 从 selectedTables 中移除
      this.selectedTables.splice(index, 1)
      
      // 从存储中移除对应的表格项
      const storedItems = getStorage(SELECTED_TABLES_ITEMS_KEY, [], StorageType.SESSION)
      const itemIndex = storedItems.findIndex(item => item.uniqueId === tableItem.uniqueId)
      if (itemIndex !== -1) {
        storedItems.splice(itemIndex, 1)
        setStorage(SELECTED_TABLES_ITEMS_KEY, storedItems, StorageType.SESSION)
      }
      
      // 从存储中移除对应位置的 tableId（保持向后兼容）
      const order = getTableOrder()
      if (index < order.length) {
        order.splice(index, 1)
        updateTableOrder(order)
        
        // 同时更新 TABLE_IDS_KEY
        const ids = getAllTableIds()
        const tableIdIndex = ids.indexOf(tableItem.id)
        if (tableIdIndex !== -1) {
          ids.splice(tableIdIndex, 1)
          setStorage(TABLE_IDS_KEY, ids, StorageType.SESSION)
        }
      }
      
      if (this.currentSelectedIndex === index) {
        this.currentSelectedIndex = -1
      } else if (this.currentSelectedIndex > index) {
        this.currentSelectedIndex = this.currentSelectedIndex - 1
      }
      
      this.$message.success('已移除')
    },
    isSelected(tableId) {
      return this.selectedTables.some(item => item.id === tableId)
    },
    onDragEnd() {
      // 拖拽后更新存储顺序
      const tableIds = this.selectedTables.map(item => item.id)
      updateTableOrder(tableIds)
      
      // 更新存储中的表格项顺序
      setStorage(SELECTED_TABLES_ITEMS_KEY, this.selectedTables, StorageType.SESSION)
      
      this.$message.success('顺序已更新')
    },
    clearSelected() {
      this.$confirm('确定要清空已选表格列表吗？', '提示', {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }).then(() => {
        clearTableIds()
        // 清空表格项存储
        setStorage(SELECTED_TABLES_ITEMS_KEY, [], StorageType.SESSION)
        this.selectedTableIds = []
        this.selectedTables = []
        this.currentSelectedIndex = -1
        this.$message.success('已清空')
      }).catch(() => {})
    },
    syncSelectedTableIds() {
      // 从存储中加载完整的表格项信息
      const storedItems = getStorage(SELECTED_TABLES_ITEMS_KEY, [], StorageType.SESSION)
      const order = getTableOrder()
      this.selectedTableIds = order
      
      if (storedItems.length > 0 && storedItems.length === order.length) {
        // 如果存储中有完整的表格项且数量匹配，按照 order 的顺序重新排列
        const itemMap = new Map()
        storedItems.forEach(item => {
          if (!itemMap.has(item.id)) {
            itemMap.set(item.id, [])
          }
          itemMap.get(item.id).push(item)
        })
        
        // 按照 order 的顺序重建 selectedTables
        const orderedItems = []
        const usedUniqueIds = new Set()
        
        order.forEach(tableId => {
          const items = itemMap.get(tableId) || []
          // 找到第一个未使用的项
          const item = items.find(i => !usedUniqueIds.has(i.uniqueId))
          if (item) {
            usedUniqueIds.add(item.uniqueId)
            orderedItems.push(item)
          } else if (items.length > 0) {
            // 如果所有项都已使用，使用第一个（允许重复）
            usedUniqueIds.add(items[0].uniqueId)
            orderedItems.push(items[0])
          }
        })
        
        this.selectedTables = orderedItems
      } else if (storedItems.length > 0) {
        // 如果存储中有项但数量不匹配，使用存储的项
        this.selectedTables = storedItems
        // 更新 order 以匹配存储的项
        const newOrder = storedItems.map(item => item.id)
        updateTableOrder(newOrder)
        this.selectedTableIds = newOrder
      } else if (order.length > 0) {
        // 如果只有 order 没有存储的项，尝试从当前搜索结果中重建
        this.selectedTables = order.map((tableId) => {
          const table = this.tableList.find(t => t.id === tableId)
          if (table) {
            const uniqueId = `${tableId}_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
            return {
              uniqueId: uniqueId,
              id: table.id,
              html: table.html,
              xml: table.xml,
              similarity: table.similarity,
              metadata: table.metadata
            }
          }
          return null
        }).filter(item => item !== null)
        
        // 保存到存储
        if (this.selectedTables.length > 0) {
          setStorage(SELECTED_TABLES_ITEMS_KEY, this.selectedTables, StorageType.SESSION)
        }
      } else {
        this.selectedTables = []
      }
    },
    loadSelectedTables() {
      const order = getTableOrder()
      this.selectedTableIds = order
      // 从存储中加载完整的表格项信息
      this.syncSelectedTableIds()
    },
    async handleDownload() {
      this.selectedTableIds = this.selectedTables.map(item => item.id)
      if (this.selectedTableIds.length === 0) {
        this.$message.warning('请先选择要下载的表格')
        return
      }
      
      this.downloading = true
      this.errorMessage = ''
      
      try {
        const blob = await downloadTables(this.selectedTableIds)
        const url = window.URL.createObjectURL(blob)
        const link = document.createElement('a')
        link.href = url
        link.setAttribute('download', `tables_${new Date().getTime()}.docx`)
        document.body.appendChild(link)
        link.click()
        link.remove()
        window.URL.revokeObjectURL(url)
        
        this.$message.success('下载成功！')
        
        // 清空列表并返回上传页
        clearTableIds()
        this.selectedTableIds = []
        this.selectedTables = []
        this.currentSelectedIndex = -1
        
        setTimeout(() => {
          this.$router.push('/upload')
        }, 1500)
      } catch (error) {
        this.errorMessage = '下载失败: ' + (error.message || '未知错误')
        this.$message.error(this.errorMessage)
      } finally {
        this.downloading = false
      }
    },
    getTableShortId(tableId) {
      if (!tableId) return ''
      return tableId.substring(0, 8) + '...'
    },
    getSimilarityTagType(similarity) {
      if (similarity >= 0.8) return 'success'
      if (similarity >= 0.6) return 'warning'
      return 'info'
    },
    getTableHtmlWithStyle(html) {
      if (!html) return ''
      return `
        <!DOCTYPE html>
        <html>
        <head>
          <meta charset="UTF-8">
          <style>
            body {
              margin: 0;
              padding: 10px;
              font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            }
            table {
              border-collapse: collapse;
              width: 100%;
              font-size: 14px;
            }
            td, th {
              border: 1px solid #ddd;
              padding: 8px;
              text-align: left;
            }
            th {
              background-color: #f5f5f5;
              font-weight: 600;
            }
          </style>
        </head>
        <body>
          ${html}
        </body>
        </html>
      `
    },
    getTablePdfUrl(table) {
      if (!table || !table.metadata || !table.metadata.pdf_path) {
        return null
      }
      
      // 从完整路径中提取文件名
      // 例如: C:\Users\...\pdf\table_xxx.pdf -> table_xxx.pdf
      const pdfPath = table.metadata.pdf_path
      const fileName = pdfPath.split(/[/\\]/).pop() // 支持 Windows 和 Linux 路径分隔符
      
      if (!fileName) {
        return null
      }
      
      // 拼接 PDF 访问 URL
      return `http://localhost/table-pdf/${fileName}`
    },
    getSelectedTablePdfUrl(tableItem) {
      if (!tableItem || !tableItem.metadata || !tableItem.metadata.pdf_path) {
        return null
      }
      
      // 从完整路径中提取文件名
      const pdfPath = tableItem.metadata.pdf_path
      const fileName = pdfPath.split(/[/\\]/).pop()
      
      if (!fileName) {
        return null
      }
      
      // 拼接 PDF 访问 URL
      return `http://localhost/table-pdf/${fileName}`
    },
    goToUpload() {
      this.$router.push('/upload')
    },
    cacheQueryResult(cacheData) {
      // 缓存查询结果到 sessionStorage
      setStorage(QUERY_RESULT_CACHE_KEY, cacheData, StorageType.SESSION)
    },
    loadCachedQueryResult() {
      // 从 sessionStorage 加载缓存的查询结果
      const cached = getStorage(QUERY_RESULT_CACHE_KEY, null, StorageType.SESSION)
      if (cached && cached.results && cached.results.length > 0) {
        this.searchKeyword = cached.keyword || ''
        this.topK = cached.topK || 10
        this.tableList = cached.results || []
        
        // 恢复当前选中的表格
        if (this.tableList.length > 0) {
          this.currentTableId = this.tableList[0].id
        }
        
        // 同步已选表格
        this.syncSelectedTableIds()
      }
    }
  }
}
</script>

<style scoped>
.display-page {
  min-height: calc(100vh - 200px);
}

.search-card {
  margin-bottom: 20px;
  border-radius: 12px;
}

.search-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.search-header h2 {
  margin: 0;
  font-size: 20px;
  color: #303133;
  display: flex;
  align-items: center;
  gap: 10px;
}

.search-bar {
  display: flex;
  gap: 20px;
  align-items: center;
  flex-wrap: wrap;
}

.search-input {
  flex: 1;
  min-width: 300px;
}

.search-options {
  display: flex;
  align-items: center;
  gap: 10px;
}

.option-label {
  font-size: 14px;
  color: #606266;
  white-space: nowrap;
}

.option-input {
  width: 100px;
}

.error-alert {
  margin-top: 15px;
}

.results-container {
  display: grid;
  grid-template-columns: 1fr 1fr 350px;
  grid-template-rows: auto 1fr;
  gap: 20px;
  grid-template-areas:
    'main main sidebar'
    'list list sidebar';
}

.main-display-card {
  grid-area: main;
  border-radius: 12px;
}

.results-list-card {
  grid-area: list;
  border-radius: 12px;
}

.selected-sidebar {
  grid-area: sidebar;
  border-radius: 12px;
  position: sticky;
  top: 20px;
  height: fit-content;
  display: flex;
  flex-direction: column;
}

.selected-sidebar >>> .el-card__body {
  display: flex;
  flex-direction: column;
  padding: 20px;
  height: 100%;
}

.display-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 15px;
}

.header-left h3 {
  margin: 0;
  font-size: 18px;
  color: #303133;
  display: flex;
  align-items: center;
  gap: 8px;
}

.similarity-badge {
  padding: 4px 12px;
  background: #ecf5ff;
  color: #409EFF;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 500;
}

.table-display-wrapper {
  min-height: 500px;
}

.table-container {
  width: 100%;
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  overflow: hidden;
  background: #fff;
}

.table-wrapper {
  width: 100%;
  height: 600px;
  overflow: auto;
}

.table-iframe {
  width: 100%;
  height: 100%;
  border: none;
}

.empty-display {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 500px;
  color: #909399;
}

.empty-display i {
  font-size: 64px;
  margin-bottom: 20px;
}

.list-header h3 {
  margin: 0;
  font-size: 18px;
  color: #303133;
  display: flex;
  align-items: center;
  gap: 8px;
}

.table-list {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 15px;
  max-height: 600px;
  overflow-y: auto;
  padding: 5px;
}

.table-item {
  border: 2px solid #e4e7ed;
  border-radius: 8px;
  padding: 12px;
  cursor: pointer;
  transition: all 0.3s;
  background: #fff;
}

.table-item:hover {
  border-color: #409EFF;
  box-shadow: 0 2px 12px rgba(64, 158, 255, 0.2);
}

.table-item.active {
  border-color: #409EFF;
  background: #ecf5ff;
}

.table-item.selected {
  border-color: #67c23a;
  background: #f0f9ff;
}

.table-item-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.table-info {
  display: flex;
  align-items: center;
  gap: 10px;
}

.table-number {
  font-weight: 600;
  color: #303133;
}

.similarity-tag {
  font-size: 11px;
}

.table-preview {
  width: 100%;
  height: 150px;
  border: 1px solid #e4e7ed;
  border-radius: 4px;
  overflow: hidden;
  background: #fafafa;
}

.preview-iframe {
  width: 100%;
  height: 100%;
  border: none;
  transform: scale(0.5);
  transform-origin: top left;
  width: 200%;
  height: 200%;
}

.preview-empty {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: #c0c4cc;
  font-size: 12px;
}

.sidebar-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.sidebar-header h3 {
  margin: 0;
  font-size: 16px;
  color: #303133;
  display: flex;
  align-items: center;
  gap: 8px;
}

.selected-content-wrapper {
  display: flex;
  flex-direction: column;
  height: 600px;
  max-height: 600px;
}

.selected-list {
  display: flex;
  flex-direction: column;
  gap: 15px;
  flex: 1;
  overflow-y: auto;
  padding: 5px;
  margin-bottom: 0;
}

.selected-table-item {
  border: 2px solid #e4e7ed;
  border-radius: 8px;
  padding: 12px;
  cursor: pointer;
  transition: all 0.3s;
  background: #fff;
}

.selected-table-item:hover {
  border-color: #409EFF;
  box-shadow: 0 2px 12px rgba(64, 158, 255, 0.2);
}

.selected-table-item.active {
  border-color: #409EFF;
  background: #ecf5ff;
}

.selected-table-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.selected-table-info {
  display: flex;
  align-items: center;
  gap: 10px;
  flex: 1;
}

.drag-handle {
  color: #909399;
  cursor: move;
  font-size: 16px;
}

.drag-handle:hover {
  color: #409EFF;
}

.selected-table-number {
  font-weight: 600;
  color: #303133;
}

.selected-table-preview {
  width: 100%;
  height: 150px;
  border: 1px solid #e4e7ed;
  border-radius: 4px;
  overflow: hidden;
  background: #fafafa;
}

.selected-preview-iframe {
  width: 100%;
  height: 100%;
  border: none;
  transform: scale(0.5);
  transform-origin: top left;
  width: 200%;
  height: 200%;
}

.selected-preview-empty {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: #c0c4cc;
  font-size: 12px;
}

.download-section {
  margin-top: auto;
  padding-top: 15px;
  padding-bottom: 0;
  border-top: 1px solid #e4e7ed;
  background: #fff;
  flex-shrink: 0;
}

.download-btn {
  width: 100%;
}

.empty-selected {
  text-align: center;
  padding: 40px 20px;
  color: #909399;
}

.empty-selected i {
  font-size: 48px;
  margin-bottom: 15px;
  color: #c0c4cc;
}

.empty-selected p {
  margin: 10px 0;
  font-size: 14px;
}

.empty-tip {
  font-size: 12px;
  color: #c0c4cc;
}

.empty-state,
.loading-state {
  margin-top: 40px;
}

.empty-card,
.loading-card {
  border-radius: 12px;
  text-align: center;
}

.empty-content,
.loading-content {
  padding: 60px 20px;
}

.empty-content i,
.loading-content i {
  font-size: 64px;
  color: #c0c4cc;
  margin-bottom: 20px;
}

.empty-content h3 {
  font-size: 20px;
  color: #303133;
  margin-bottom: 10px;
}

.empty-content p {
  color: #909399;
  font-size: 14px;
  line-height: 1.6;
}

.loading-content i {
  animation: rotating 2s linear infinite;
}

@keyframes rotating {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

/* 响应式设计 */
@media (max-width: 1200px) {
  .results-container {
    grid-template-columns: 1fr;
    grid-template-areas:
      'main'
      'list'
      'sidebar';
  }

  .selected-sidebar {
    position: static;
    max-height: none;
  }

  .selected-content-wrapper {
    height: auto;
    max-height: none;
  }
}

@media (max-width: 768px) {
  .search-bar {
    flex-direction: column;
    align-items: stretch;
  }

  .search-input {
    min-width: 100%;
  }

  .table-list {
    grid-template-columns: 1fr;
  }

  .table-wrapper {
    height: 400px;
  }

  .selected-content-wrapper {
    height: 400px;
    max-height: 400px;
  }
}
</style>
