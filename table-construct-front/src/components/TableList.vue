<template>
  <div class="table-list">
    <div class="table-list-header">
      <h3>表格列表</h3>
      <div class="header-actions">
        <el-input
          v-model="searchKeyword"
          placeholder="搜索表格ID"
          size="small"
          style="width: 200px; margin-right: 10px;"
          @keyup.enter.native="handleSearch"
          clearable
        ></el-input>
        <el-button type="primary" size="small" @click="handleSearch">搜索</el-button>
        <el-button size="small" @click="handleRefresh">刷新</el-button>
      </div>
    </div>

    <div class="table-list-content" v-loading="loading">
      <div v-if="tableList.length === 0 && !loading" class="empty-state">
        <p>暂无表格数据</p>
      </div>
      <div v-else class="table-items">
        <el-card
          v-for="(table, index) in filteredTableList"
          :key="table.id"
          class="table-item"
          shadow="hover"
        >
          <div slot="header" class="table-item-header">
            <div class="table-info">
              <span class="table-index">表格 {{ index + 1 }}</span>
              <span class="table-id">ID: {{ table.id }}</span>
              <span v-if="table.similarity !== undefined" class="table-similarity">
                相似度: {{ (table.similarity * 100).toFixed(2) }}%
              </span>
            </div>
            <div class="table-actions">
              <el-button
                type="text"
                size="small"
                @click="togglePreview(table.id)"
              >
                {{ expandedPreviews[table.id] ? '收起预览' : '展开预览' }}
              </el-button>
              <el-button
                type="text"
                size="small"
                @click="handleViewDetail(table)"
              >
                查看详情
              </el-button>
            </div>
          </div>

          <div class="table-item-body">
            <div v-if="expandedPreviews[table.id]" class="table-preview">
              <div class="preview-container">
                <iframe
                  v-if="table.html"
                  :srcdoc="table.html"
                  class="preview-iframe"
                ></iframe>
                <div v-else class="no-preview">
                  <p>暂无HTML预览</p>
                </div>
              </div>
            </div>
            <div v-else class="table-summary">
              <p>点击"展开预览"查看表格HTML预览</p>
            </div>
          </div>
        </el-card>
      </div>
    </div>

    <el-dialog
      title="表格详情"
      :visible.sync="detailDialogVisible"
      width="80%"
      :before-close="handleCloseDetail"
    >
      <div v-if="currentDetailTable" class="detail-content">
        <div class="detail-section">
          <h4>表格ID</h4>
          <p>{{ currentDetailTable.id }}</p>
        </div>
        <div class="detail-section" v-if="currentDetailTable.similarity !== undefined">
          <h4>相似度</h4>
          <p>{{ (currentDetailTable.similarity * 100).toFixed(2) }}%</p>
        </div>
        <div class="detail-section" v-if="currentDetailTable.metadata">
          <h4>元数据</h4>
          <pre>{{ JSON.stringify(currentDetailTable.metadata, null, 2) }}</pre>
        </div>
        <div class="detail-section">
          <h4>HTML预览</h4>
          <div class="detail-preview-container">
            <iframe
              v-if="currentDetailTable.html"
              :srcdoc="currentDetailTable.html"
              class="detail-preview-iframe"
            ></iframe>
            <div v-else class="no-preview">
              <p>暂无HTML预览</p>
            </div>
          </div>
        </div>
        <div class="detail-section" v-if="currentDetailTable.xml">
          <h4>XML源码</h4>
          <pre class="xml-code">{{ currentDetailTable.xml }}</pre>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script>
export default {
  name: 'TableList',
  props: {
    tables: {
      type: Array,
      default: () => []
    },
    loading: {
      type: Boolean,
      default: false
    }
  },
  data() {
    return {
      searchKeyword: '',
      expandedPreviews: {},
      detailDialogVisible: false,
      currentDetailTable: null
    }
  },
  computed: {
    tableList() {
      return this.tables || []
    },
    filteredTableList() {
      if (!this.searchKeyword.trim()) {
        return this.tableList
      }
      const keyword = this.searchKeyword.trim().toLowerCase()
      return this.tableList.filter(table => {
        return table.id && table.id.toString().toLowerCase().includes(keyword)
      })
    }
  },
  watch: {
    tables: {
      handler() {
        this.resetExpandedPreviews()
      },
      deep: true
    }
  },
  methods: {
    handleSearch() {
      this.$emit('search', this.searchKeyword)
    },
    handleRefresh() {
      this.searchKeyword = ''
      this.resetExpandedPreviews()
      this.$emit('refresh')
    },
    togglePreview(tableId) {
      this.$set(this.expandedPreviews, tableId, !this.expandedPreviews[tableId])
    },
    resetExpandedPreviews() {
      this.expandedPreviews = {}
    },
    handleViewDetail(table) {
      this.currentDetailTable = table
      this.detailDialogVisible = true
    },
    handleCloseDetail() {
      this.detailDialogVisible = false
      this.currentDetailTable = null
    }
  }
}
</script>

<style scoped>
.table-list {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
}

.table-list-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 15px 20px;
  border-bottom: 1px solid #e4e7ed;
  background-color: #fff;
}

.table-list-header h3 {
  margin: 0;
  font-size: 18px;
  font-weight: 500;
  color: #303133;
}

.header-actions {
  display: flex;
  align-items: center;
}

.table-list-content {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  background-color: #f5f7fa;
}

.empty-state {
  text-align: center;
  padding: 60px 20px;
  color: #909399;
}

.table-items {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.table-item {
  background-color: #fff;
  transition: all 0.3s;
}

.table-item:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.table-item-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.table-info {
  display: flex;
  align-items: center;
  gap: 15px;
  flex: 1;
}

.table-index {
  font-weight: 600;
  color: #303133;
  font-size: 14px;
}

.table-id {
  color: #606266;
  font-size: 13px;
  font-family: 'Courier New', monospace;
}

.table-similarity {
  color: #409eff;
  font-size: 13px;
}

.table-actions {
  display: flex;
  gap: 10px;
}

.table-item-body {
  margin-top: 10px;
}

.table-preview {
  margin-top: 10px;
}

.preview-container {
  width: 100%;
  border: 1px solid #e4e7ed;
  border-radius: 4px;
  overflow: hidden;
  background-color: #fff;
}

.preview-iframe {
  width: 100%;
  height: 300px;
  border: none;
  display: block;
}

.no-preview {
  padding: 40px;
  text-align: center;
  color: #909399;
}

.table-summary {
  padding: 20px;
  text-align: center;
  color: #909399;
  font-size: 13px;
}

.detail-content {
  max-height: 70vh;
  overflow-y: auto;
}

.detail-section {
  margin-bottom: 25px;
}

.detail-section h4 {
  margin: 0 0 10px 0;
  font-size: 16px;
  font-weight: 600;
  color: #303133;
  border-bottom: 2px solid #409eff;
  padding-bottom: 5px;
}

.detail-section p {
  margin: 5px 0;
  color: #606266;
  font-size: 14px;
  word-break: break-all;
}

.detail-section pre {
  background-color: #f5f7fa;
  border: 1px solid #e4e7ed;
  border-radius: 4px;
  padding: 15px;
  overflow-x: auto;
  font-size: 13px;
  line-height: 1.5;
  color: #303133;
  margin: 10px 0;
}

.xml-code {
  max-height: 300px;
  overflow-y: auto;
  font-family: 'Courier New', monospace;
}

.detail-preview-container {
  width: 100%;
  border: 1px solid #e4e7ed;
  border-radius: 4px;
  overflow: hidden;
  background-color: #fff;
}

.detail-preview-iframe {
  width: 100%;
  height: 400px;
  border: none;
  display: block;
}
</style>