<template>
  <div id="app">
    <el-container class="app-container">
      <!-- 顶部导航栏 -->
      <el-header class="app-header">
        <div class="header-content">
          <div class="logo">
            <h1>📊 表格构建系统</h1>
          </div>
          <el-menu
            :default-active="activeMenu"
            mode="horizontal"
            class="nav-menu"
            @select="handleMenuSelect"
            active-text-color="#409EFF"
          >
            <el-menu-item index="/upload">
              <i class="el-icon-upload2"></i>
              <span>文档上传</span>
            </el-menu-item>
            <el-menu-item index="/display">
              <i class="el-icon-search"></i>
              <span>表格查询</span>
            </el-menu-item>
          </el-menu>
        </div>
      </el-header>

      <!-- 主内容区 -->
      <el-main class="app-main">
        <router-view></router-view>
      </el-main>

      <!-- 底部 -->
      <el-footer class="app-footer">
        <p>© 表格构建系统 | Version 0.1.0</p>
      </el-footer>
    </el-container>
  </div>
</template>

<script>
export default {
  name: 'App',
  computed: {
    activeMenu() {
      return this.$route.path
    }
  },
  methods: {
    handleMenuSelect(index) {
      this.$router.push(index)
    }
  }
}
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

#app {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  color: #2c3e50;
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.app-container {
  min-height: 100vh;
  background: transparent;
}

.app-header {
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
  padding: 0;
  height: 70px !important;
  line-height: 70px;
}

.header-content {
  max-width: 1400px;
  margin: 0 auto;
  padding: 0 30px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.logo h1 {
  font-size: 24px;
  font-weight: 600;
  color: #409EFF;
  margin: 0;
}

.nav-menu {
  border-bottom: none;
  background: transparent;
}

.nav-menu .el-menu-item {
  font-size: 16px;
  font-weight: 500;
}

.app-main {
  padding: 30px;
  max-width: 1400px;
  margin: 0 auto;
  width: 100%;
}

.app-footer {
  background: rgba(255, 255, 255, 0.1);
  color: rgba(255, 255, 255, 0.8);
  text-align: center;
  height: 60px !important;
  line-height: 60px;
  margin-top: auto;
}

.app-footer p {
  margin: 0;
  font-size: 14px;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .header-content {
    flex-direction: column;
    padding: 10px 20px;
  }

  .logo h1 {
    font-size: 20px;
  }

  .app-main {
    padding: 20px;
  }
}
</style>
