<template>
  <div class="loading-spinner" :class="{ fullscreen }">
    <el-loading
      :visible="visible"
      :text="text"
      :fullscreen="fullscreen"
      :background="background"
    ></el-loading>
  </div>
</template>

<script setup lang="ts">
import { ElLoading } from 'element-plus';

// 直接解构 props 属性，避免单独声明 props 变量
const { visible, text, fullscreen, background } = defineProps<{
  visible: boolean; // 是否显示
  text?: string; // 提示文字
  fullscreen?: boolean; // 是否全屏
  background?: string; // 背景色（默认半透明）
}>();
</script>

<style scoped>
.loading-spinner {
  position: relative;
}

.fullscreen {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  z-index: 9999;
}
</style>