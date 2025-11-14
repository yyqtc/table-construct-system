<template>
  <div class="error-message" v-if="message">
    <el-alert
      :title="message"
      :type="type"
      :closable="closable"
      show-icon
      @close="handleClose"
    />
  </div>
</template>

<script>
export default {
  name: 'ErrorMessage',
  props: {
    message: {
      type: String,
      default: ''
    },
    type: {
      type: String,
      default: 'error'
    },
    closable: {
      type: Boolean,
      default: true
    }
  },
  methods: {
    handleClose() {
      this.$emit('close');
    }
  }
}
</script>

<style scoped>
.error-message {
  margin: 12px 0;
}
</style>
