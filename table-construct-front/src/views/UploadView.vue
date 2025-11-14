<template>
  <div class="upload-page">
    <el-card class="upload-card" shadow="hover">
      <div slot="header" class="card-header">
        <h2>
          <i class="el-icon-upload2"></i>
          文档上传
        </h2>
        <el-button type="primary" icon="el-icon-search" @click="goToDisplay">
          前往查询
        </el-button>
      </div>

      <div class="upload-content">
        <!-- 上传区域 -->
        <div class="upload-area-wrapper">
          <el-upload
            ref="upload"
            :auto-upload="false"
            :on-change="handleFileChange"
            :on-remove="handleFileRemove"
            :limit="1"
            accept=".docx"
            :file-list="fileList"
            drag
            class="upload-dragger"
          >
            <div class="upload-inner">
              <i class="el-icon-upload"></i>
              <div class="upload-text">
                <p class="upload-title">将文件拖到此处，或<em>点击上传</em></p>
                <p class="upload-tip">支持 .docx 格式，文件大小不超过 50MB</p>
              </div>
            </div>
          </el-upload>

          <!-- 文件信息 -->
          <div v-if="selectedFile" class="file-info">
            <el-card shadow="never" class="file-card">
              <div class="file-details">
                <div class="file-icon">
                  <i class="el-icon-document"></i>
                </div>
                <div class="file-meta">
                  <p class="file-name">{{ selectedFile.name }}</p>
                  <p class="file-size">{{ formatFileSize(selectedFile.size) }}</p>
                </div>
                <el-button
                  type="success"
                  icon="el-icon-upload2"
                  @click="uploadFile"
                  :loading="uploading"
                  size="medium"
                  class="upload-btn"
                >
                  {{ uploading ? '上传中...' : '开始上传' }}
                </el-button>
              </div>
            </el-card>
          </div>

          <!-- 上传提示 -->
          <div v-if="!selectedFile" class="upload-tips">
            <el-alert
              title="使用说明"
              type="info"
              :closable="false"
              show-icon
            >
              <ul class="tips-list">
                <li>上传包含表格的 Word 文档（.docx 格式）</li>
                <li>系统会自动提取文档中的所有表格</li>
                <li>提取的表格将用于智能搜索和查询</li>
                <li>上传成功后，您可以前往查询页面搜索表格</li>
              </ul>
            </el-alert>
          </div>
        </div>

        <!-- 上传进度 -->
        <div v-if="uploading" class="upload-progress">
          <el-progress
            :percentage="uploadProgress"
            :status="uploadStatus"
            :stroke-width="8"
          ></el-progress>
        </div>

        <!-- 上传结果 -->
        <div v-if="uploadResult" class="upload-result">
          <el-alert
            :title="uploadResult.title"
            :type="uploadResult.type"
            :description="uploadResult.message"
            show-icon
            :closable="true"
            @close="uploadResult = null"
          >
            <div v-if="uploadResult.data" slot="title" class="result-details">
              <p><strong>文件名：</strong>{{ uploadResult.data.filename }}</p>
              <p><strong>文件大小：</strong>{{ formatFileSize(uploadResult.data.file_size) }}</p>
              <p><strong>提取表格数：</strong>{{ uploadResult.data.tables_count }} 个</p>
            </div>
          </el-alert>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script>
import api from '../api'

export default {
  name: 'UploadView',
  data() {
    return {
      selectedFile: null,
      uploading: false,
      fileList: [],
      uploadProgress: 0,
      uploadStatus: null,
      uploadResult: null
    }
  },
  methods: {
    handleFileChange(file, fileList) {
      if (file.raw) {
        if (!file.raw.name.toLowerCase().endsWith('.docx')) {
          this.$message.error('只能上传 .docx 格式的文件')
          this.$refs.upload.clearFiles()
          this.selectedFile = null
          this.fileList = []
          return
        }
        
        const MAX_FILE_SIZE = 50 * 1024 * 1024 // 50MB
        if (file.raw.size > MAX_FILE_SIZE) {
          this.$message.error(`文件大小超过限制（最大50MB），当前文件大小：${this.formatFileSize(file.raw.size)}`)
          this.$refs.upload.clearFiles()
          this.selectedFile = null
          this.fileList = []
          return
        }
        
        this.selectedFile = file.raw
        this.fileList = fileList
        this.uploadResult = null
      }
    },
    handleFileRemove() {
      this.selectedFile = null
      this.fileList = []
      this.uploadResult = null
    },
    async uploadFile() {
      if (!this.selectedFile) {
        return
      }
      
      this.uploading = true
      this.uploadProgress = 0
      this.uploadStatus = null
      this.uploadResult = null
      
      // 模拟上传进度
      const progressInterval = setInterval(() => {
        if (this.uploadProgress < 90) {
          this.uploadProgress += 10
        }
      }, 200)
      
      try {
        const response = await api.uploadFile(this.selectedFile)
        clearInterval(progressInterval)
        this.uploadProgress = 100
        this.uploadStatus = 'success'
        
        this.uploadResult = {
          type: 'success',
          title: '上传成功！',
          message: response.message || '文件上传成功',
          data: response.data
        }
        
        this.$message.success('文件上传成功！')
        
        // 3秒后清空文件列表
        setTimeout(() => {
          this.handleSuccess()
        }, 3000)
      } catch (error) {
        clearInterval(progressInterval)
        this.uploadProgress = 0
        this.uploadStatus = 'exception'
        
        this.uploadResult = {
          type: 'error',
          title: '上传失败',
          message: error.message || '上传失败，请重试'
        }
        
        this.$message.error(error.message || '上传失败')
      } finally {
        this.uploading = false
      }
    },
    handleSuccess() {
      this.selectedFile = null
      this.fileList = []
      this.uploadResult = null
      this.uploadProgress = 0
      this.uploadStatus = null
      this.$refs.upload.clearFiles()
    },
    formatFileSize(bytes) {
      if (bytes === 0) return '0 B'
      const k = 1024
      const sizes = ['B', 'KB', 'MB', 'GB']
      const i = Math.floor(Math.log(bytes) / Math.log(k))
      return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i]
    },
    goToDisplay() {
      this.$router.push('/display')
    }
  }
}
</script>

<style scoped>
.upload-page {
  min-height: calc(100vh - 200px);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
}

.upload-card {
  width: 100%;
  max-width: 800px;
  border-radius: 12px;
  overflow: hidden;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-header h2 {
  margin: 0;
  font-size: 24px;
  color: #303133;
  display: flex;
  align-items: center;
  gap: 10px;
}

.upload-content {
  padding: 20px 0;
}

.upload-area-wrapper {
  margin-bottom: 30px;
}

.upload-dragger {
  width: 100%;
}

.upload-dragger >>> .el-upload-dragger {
  width: 100%;
  height: 200px;
  border: 2px dashed #d9d9d9;
  border-radius: 8px;
  background: #fafafa;
  transition: all 0.3s;
}

.upload-dragger >>> .el-upload-dragger:hover {
  border-color: #409EFF;
  background: #f0f9ff;
}

.upload-inner {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  padding: 40px;
}

.upload-inner i {
  font-size: 67px;
  color: #c0c4cc;
  margin-bottom: 20px;
}

.upload-text {
  text-align: center;
}

.upload-title {
  font-size: 16px;
  color: #606266;
  margin-bottom: 10px;
}

.upload-title em {
  color: #409EFF;
  font-style: normal;
  font-weight: 600;
}

.upload-tip {
  font-size: 14px;
  color: #909399;
}

.file-info {
  margin-top: 20px;
}

.file-card {
  border: 1px solid #e4e7ed;
  border-radius: 8px;
}

.file-details {
  display: flex;
  align-items: center;
  gap: 20px;
  padding: 10px;
}

.file-icon {
  font-size: 48px;
  color: #409EFF;
}

.file-meta {
  flex: 1;
}

.file-name {
  font-size: 16px;
  font-weight: 500;
  color: #303133;
  margin-bottom: 5px;
  word-break: break-all;
}

.file-size {
  font-size: 14px;
  color: #909399;
  margin: 0;
}

.upload-btn {
  min-width: 120px;
}

.upload-tips {
  margin-top: 30px;
}

.tips-list {
  margin: 10px 0 0 20px;
  padding: 0;
  list-style: disc;
  color: #606266;
  line-height: 2;
}

.tips-list li {
  margin-bottom: 5px;
}

.upload-progress {
  margin: 20px 0;
}

.upload-result {
  margin-top: 20px;
}

.result-details {
  margin-top: 10px;
  font-size: 14px;
  line-height: 1.8;
}

.result-details p {
  margin: 5px 0;
  color: #606266;
}

.result-details strong {
  color: #303133;
}

@media (max-width: 768px) {
  .file-details {
    flex-direction: column;
    text-align: center;
  }

  .upload-btn {
    width: 100%;
  }
}
</style>
