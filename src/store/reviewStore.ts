import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { ReviewProgress, ViolationSentence } from '@/types/review'

export const useReviewStore = defineStore('review', () => {
  // 状态
  const reviewProgress = ref<Record<number, ReviewProgress>>({})
  const violationSentences = ref<Record<number, ViolationSentence[]>>({})
  const activeReviews = ref<Set<number>>(new Set())
  const sseConnections = ref<Record<number, EventSource | undefined>>({})

  // 操作
  const setReviewProgress = (articleId: number, progress: ReviewProgress) => {
    reviewProgress.value[articleId] = progress
  }

  const getReviewProgress = (articleId: number): ReviewProgress | undefined => {
    return reviewProgress.value[articleId]
  }

  const setViolationSentences = (articleId: number, sentences: ViolationSentence[]) => {
    violationSentences.value[articleId] = sentences
  }

  const getViolationSentences = (articleId: number): ViolationSentence[] => {
    return violationSentences.value[articleId] || []
  }

  const addActiveReview = (articleId: number) => {
    activeReviews.value.add(articleId)
  }

  const removeActiveReview = (articleId: number) => {
    activeReviews.value.delete(articleId)
  }

  const isReviewActive = (articleId: number): boolean => {
    return activeReviews.value.has(articleId)
  }

  const clearReviewData = (articleId: number) => {
    delete reviewProgress.value[articleId]
    delete violationSentences.value[articleId]
    activeReviews.value.delete(articleId)
    // 关闭SSE连接
    if (sseConnections.value[articleId]) {
      sseConnections.value[articleId].close()
      delete sseConnections.value[articleId]
    }
  }

  // SSE相关操作
  const setSSEConnection = (articleId: number, connection: EventSource) => {
    sseConnections.value[articleId] = connection
  }

  const getSSEConnection = (articleId: number): EventSource | undefined => {
    return sseConnections.value[articleId]
  }

  const closeSSEConnection = (articleId: number) => {
    if (sseConnections.value[articleId]) {
      sseConnections.value[articleId].close()
      delete sseConnections.value[articleId]
    }
  }

  const closeAllSSEConnections = () => {
    Object.values(sseConnections.value).forEach(connection => {
      if (connection) {
        connection.close()
      }
    })
    sseConnections.value = {}
  }

  return {
    // 状态
    reviewProgress,
    violationSentences,
    activeReviews,
    sseConnections,
    // 操作
    setReviewProgress,
    getReviewProgress,
    setViolationSentences,
    getViolationSentences,
    addActiveReview,
    removeActiveReview,
    isReviewActive,
    clearReviewData,
    // SSE操作
    setSSEConnection,
    getSSEConnection,
    closeSSEConnection,
    closeAllSSEConnections
  }
})
