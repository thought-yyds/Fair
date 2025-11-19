<template>
  <div class="empty-state">
    <el-empty
      :image="image"
      :description="description"
    >
      <slot name="action"></slot>
    </el-empty>
  </div>
</template>

<script setup lang="ts">
import { ElEmpty } from 'element-plus';

// 直接解构 props，避免单独声明 props 变量
const { image, description } = defineProps<{
  image?: string; // 自定义图片（默认用element的）
  description?: string; // 描述文字
}>();
</script>

<style scoped>
.empty-state {
  width: 100%;
  padding: 48px 24px;
  text-align: center;
}
</style>