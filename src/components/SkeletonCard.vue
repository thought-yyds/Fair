<!-- src/components/SkeletonCard.vue -->
<template>
  <div class="skeleton-card">
    <!-- 文件名骨架 -->
    <div class="skeleton-header">
      <div class="skeleton-title"></div>
      <div class="skeleton-tag"></div>
    </div>
    
    <!-- 进度条骨架 -->
    <div class="skeleton-progress">
      <div class="skeleton-progress-bar"></div>
    </div>
    
    <!-- 操作按钮骨架 -->
    <div class="skeleton-actions">
      <div class="skeleton-button"></div>
      <div class="skeleton-button"></div>
    </div>
  </div>
</template>

<script setup lang="ts">
// 骨架屏组件，用于文件列表加载时的占位
</script>

<style scoped>
.skeleton-card {
  width: 100%;
  min-width: 500px;
  padding: 16px;
  border: 1px solid #f0f0f0;
  border-radius: 8px;
  background: #fff;
}

.skeleton-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.skeleton-title {
  width: 60%;
  height: 20px;
  background: linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%);
  background-size: 200% 100%;
  animation: loading 1.5s infinite;
  border-radius: 4px;
}

.skeleton-tag {
  width: 80px;
  height: 24px;
  background: linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%);
  background-size: 200% 100%;
  animation: loading 1.5s infinite;
  border-radius: 12px;
}

.skeleton-progress {
  margin: 8px 0;
}

.skeleton-progress-bar {
  width: 100%;
  height: 8px;
  background: linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%);
  background-size: 200% 100%;
  animation: loading 1.5s infinite;
  border-radius: 4px;
}

.skeleton-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 8px;
}

.skeleton-button {
  width: 80px;
  height: 32px;
  background: linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%);
  background-size: 200% 100%;
  animation: loading 1.5s infinite;
  border-radius: 6px;
}

@keyframes loading {
  0% {
    background-position: 200% 0;
  }
  100% {
    background-position: -200% 0;
  }
}
</style>
