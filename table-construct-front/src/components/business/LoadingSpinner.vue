<template>
  <div v-loading="loading" :element-loading-text="loadingText" class="loading-spinner">
    <slot></slot>
  </div>
</template>

<script>
export default {
  name: 'LoadingSpinner',
  props: {
    loading: {
      type: Boolean,
      default: false
    },
    loadingText: {
      type: String,
      default: ''
    }
  }
}
</script>

<style scoped>
.loading-spinner {
  min-height: 100px;
}
</style>
