<template>
  <div class="empty-state">
    <div class="empty-content">
      <div class="empty-icon"></div>
      <div class="empty-text">{{ message }}</div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'EmptyState',
  props: {
    message: {
      type: String,
      default: '暂无数据'
    }
  }
}
</script>

<style scoped>
.empty-state {
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 40px 20px;
  min-height: 200px;
}

.empty-content {
  text-align: center;
  color: #909399;
}

.empty-icon {
  width: 80px;
  height: 80px;
  margin: 0 auto 16px;
  background-color: #f5f7fa;
  border-radius: 50%;
  position: relative;
}

.empty-icon::before {
  content: '';
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 40px;
  height: 40px;
  border: 2px solid #c0c4cc;
  border-radius: 50%;
}

.empty-icon::after {
  content: '';
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%) rotate(45deg);
  width: 20px;
  height: 2px;
  background-color: #c0c4cc;
}

.empty-text {
  font-size: 14px;
  line-height: 1.5;
  color: #909399;
}
</style>
