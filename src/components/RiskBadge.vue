<!-- src/components/RiskBadge.vue -->
<template>
  <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium" :class="badgeClass">
    <i :class="badgeIcon" class="mr-1"></i>
    {{ riskLevel }}
  </span>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { Article } from '@/types/article'

// Props：明确接收风险等级（与Article类型对齐）
const props = defineProps<{
  riskLevel: Article['risk_level'] // 限定为 "无风险" | "低风险" | "中风险" | "高风险"
}>()

// 计算属性：根据风险等级匹配样式（统一设计规范）
const badgeClass = computed(() => {
  switch (props.riskLevel) {
    case '无风险':
      return 'bg-green-100 text-green-800'
    case '低风险':
      return 'bg-blue-100 text-blue-800'
    case '中风险':
      return 'bg-yellow-100 text-yellow-800'
    case '高风险':
      return 'bg-red-100 text-red-800'
    default:
      return 'bg-gray-100 text-gray-800'
  }
})

// 计算属性：匹配风险等级图标
const badgeIcon = computed(() => {
  switch (props.riskLevel) {
    case '无风险':
      return 'fa fa-check-circle'
    case '低风险':
      return 'fa fa-info-circle'
    case '中风险':
      return 'fa fa-exclamation-triangle'
    case '高风险':
      return 'fa fa-exclamation-circle'
    default:
      return 'fa fa-question-circle'
  }
})
</script>