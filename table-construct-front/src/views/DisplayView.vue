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
      <el-card class="main-display-card" shadow="hover">
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
              :type="isSelected(currentTableId) ? 'success' : 'primary'"
              :icon="isSelected(currentTableId) ? 'el-icon-check' : 'el-icon-plus'"
              size="small"
              @click="toggleSelect(currentTableId)"
              :disabled="!currentTableId"
            >
              {{ isSelected(currentTableId) ? '已选择' : '添加到列表' }}
            </el-button>
          </div>
        </div>
        
        <div class="table-display-wrapper">
          <div v-if="currentTableHtml" class="table-container">
            <div class="table-wrapper">
              <iframe
                :srcdoc="getTableHtmlWithStyle(currentTableHtml)"
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
      <el-card class="results-list-card" shadow="hover">
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
            :class="{ active: currentTableId === table.id, selected: isSelected(table.id) }"
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
                :type="isSelected(table.id) ? 'success' : 'default'"
                :icon="isSelected(table.id) ? 'el-icon-check' : 'el-icon-plus'"
                size="mini"
                circle
                @click.stop="toggleSelect(table.id)"
              ></el-button>
            </div>
            
            <div class="table-preview">
              <iframe
                v-if="table.html"
                :srcdoc="getTableHtmlWithStyle(table.html)"
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
            已选表格 ({{ selectedTableIds.length }})
          </h3>
          <el-button
            v-if="selectedTableIds.length > 0"
            type="text"
            size="small"
            @click="clearSelected"
          >
            清空
          </el-button>
        </div>

        <div v-if="selectedTableIds.length > 0" class="selected-list">
          <draggable
            v-model="selectedTableIds"
            :animation="200"
            handle=".drag-handle"
            @end="onDragEnd"
          >
            <div
              v-for="(tableId, index) in selectedTableIds"
              :key="tableId"
              class="selected-item"
              :class="{ 'item-active': currentSelectedIndex === index }"
              @click="currentSelectedIndex = index"
            >
              <div class="item-content">
                <i class="el-icon-rank drag-handle"></i>
                <span class="item-number">{{ index + 1 }}</span>
                <span class="item-id">{{ getTableShortId(tableId) }}</span>
              </div>
              <el-button
                type="danger"
                icon="el-icon-delete"
                size="mini"
                circle
                @click.stop="removeSelected(tableId)"
              ></el-button>
            </div>
          </draggable>

          <div class="order-controls">
            <el-button
              size="small"
              icon="el-icon-arrow-up"
              @click="moveUp"
              :disabled="currentSelectedIndex <= 0"
            >
              上移
            </el-button>
            <el-button
              size="small"
              icon="el-icon-arrow-down"
              @click="moveDown"
              :disabled="currentSelectedIndex >= selectedTableIds.length - 1 || currentSelectedIndex < 0"
            >
              下移
            </el-button>
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
              {{ downloading ? '下载中...' : `下载文档 (${selectedTableIds.length})` }}
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

    <!-- 加载状态 -->
    <div v-if="searching" class="loading-state">
      <el-card shadow="never" class="loading-card">
        <div class="loading-content">
          <i class="el-icon-loading"></i>
          <p>正在搜索...</p>
        </div>
      </el-card>
    </div>
  </div>
</template>

<script>
import { queryTables, downloadTables } from '../api'
import { getTableOrder, addTableId, removeTableId, updateTableOrder, clearTableIds } from '../utils/storage'
import draggable from 'vuedraggable'

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
      selectedTableIds: [],
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
    }
  },
  mounted() {
    this.loadSelectedTables()
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
    toggleSelect(tableId) {
      if (!tableId) return
      
      const index = this.selectedTableIds.indexOf(tableId)
      if (index > -1) {
        removeTableId(tableId)
        this.$message.info('已从列表移除')
      } else {
        addTableId(tableId)
        this.$message.success('已添加到列表')
      }
      this.syncSelectedTableIds()
    },
    isSelected(tableId) {
      return this.selectedTableIds.includes(tableId)
    },
    removeSelected(tableId) {
      const index = this.selectedTableIds.indexOf(tableId)
      if (index > -1) {
        removeTableId(tableId)
        if (this.currentSelectedIndex === index) {
          this.currentSelectedIndex = -1
        } else if (this.currentSelectedIndex > index) {
          this.currentSelectedIndex = this.currentSelectedIndex - 1
        }
        this.syncSelectedTableIds()
        this.$message.success('已移除')
      }
    },
    moveUp() {
      if (this.currentSelectedIndex <= 0 || this.currentSelectedIndex >= this.selectedTableIds.length) {
        return
      }
      const newOrder = [...this.selectedTableIds]
      const temp = newOrder[this.currentSelectedIndex]
      newOrder[this.currentSelectedIndex] = newOrder[this.currentSelectedIndex - 1]
      newOrder[this.currentSelectedIndex - 1] = temp
      updateTableOrder(newOrder)
      this.currentSelectedIndex = this.currentSelectedIndex - 1
      this.syncSelectedTableIds()
      this.$message.success('已上移')
    },
    moveDown() {
      if (this.currentSelectedIndex < 0 || this.currentSelectedIndex >= this.selectedTableIds.length - 1) {
        return
      }
      const newOrder = [...this.selectedTableIds]
      const temp = newOrder[this.currentSelectedIndex]
      newOrder[this.currentSelectedIndex] = newOrder[this.currentSelectedIndex + 1]
      newOrder[this.currentSelectedIndex + 1] = temp
      updateTableOrder(newOrder)
      this.currentSelectedIndex = this.currentSelectedIndex + 1
      this.syncSelectedTableIds()
      this.$message.success('已下移')
    },
    onDragEnd() {
      updateTableOrder(this.selectedTableIds)
      this.$message.success('顺序已更新')
    },
    clearSelected() {
      this.$confirm('确定要清空已选表格列表吗？', '提示', {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }).then(() => {
        clearTableIds()
        this.selectedTableIds = []
        this.currentSelectedIndex = -1
        this.$message.success('已清空')
      }).catch(() => {})
    },
    syncSelectedTableIds() {
      const order = getTableOrder()
      this.selectedTableIds = order
    },
    loadSelectedTables() {
      const order = getTableOrder()
      this.selectedTableIds = order
    },
    async handleDownload() {
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
    goToUpload() {
      this.$router.push('/upload')
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
  max-height: calc(100vh - 100px);
  overflow-y: auto;
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

.selected-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin-bottom: 20px;
}

.selected-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px;
  background: #f5f7fa;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.3s;
  border: 2px solid transparent;
}

.selected-item:hover {
  background: #e4e7ed;
}

.selected-item.item-active {
  background: #ecf5ff;
  border-color: #409EFF;
}

.item-content {
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

.item-number {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  background: #409EFF;
  color: #fff;
  border-radius: 50%;
  font-size: 12px;
  font-weight: 600;
}

.item-id {
  font-size: 12px;
  color: #606266;
  font-family: monospace;
}

.order-controls {
  display: flex;
  gap: 10px;
  margin-bottom: 20px;
}

.order-controls .el-button {
  flex: 1;
}

.download-section {
  margin-top: 20px;
  padding-top: 20px;
  border-top: 1px solid #e4e7ed;
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
}
</style>
