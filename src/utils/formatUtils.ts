/**
 * 格式化工具函数
 */

/**
 * 格式化日期时间
 * @param date 日期字符串或Date对象
 * @param format 格式化模式，默认 'YYYY-MM-DD HH:mm:ss'
 * @returns 格式化后的日期字符串
 */
export const formatDateTime = (date: string | Date, format: string = 'YYYY-MM-DD HH:mm:ss'): string => {
  const d = new Date(date)
  
  if (isNaN(d.getTime())) {
    return '无效日期'
  }

  const year = d.getFullYear()
  const month = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  const hours = String(d.getHours()).padStart(2, '0')
  const minutes = String(d.getMinutes()).padStart(2, '0')
  const seconds = String(d.getSeconds()).padStart(2, '0')

  return format
    .replace('YYYY', String(year))
    .replace('MM', month)
    .replace('DD', day)
    .replace('HH', hours)
    .replace('mm', minutes)
    .replace('ss', seconds)
}

/**
 * 格式化相对时间
 * @param date 日期字符串或Date对象
 * @returns 相对时间字符串
 */
export const formatRelativeTime = (date: string | Date): string => {
  const now = new Date()
  const target = new Date(date)
  const diffInMs = now.getTime() - target.getTime()
  const diffInSeconds = Math.floor(diffInMs / 1000)
  const diffInMinutes = Math.floor(diffInSeconds / 60)
  const diffInHours = Math.floor(diffInMinutes / 60)
  const diffInDays = Math.floor(diffInHours / 24)

  if (diffInSeconds < 60) {
    return '刚刚'
  } else if (diffInMinutes < 60) {
    return `${diffInMinutes}分钟前`
  } else if (diffInHours < 24) {
    return `${diffInHours}小时前`
  } else if (diffInDays < 7) {
    return `${diffInDays}天前`
  } else {
    return formatDateTime(target, 'YYYY-MM-DD')
  }
}

/**
 * 格式化进度百分比
 * @param progress 进度值（0-100）
 * @returns 格式化后的进度字符串
 */
export const formatProgress = (progress: number): string => {
  return `${Math.round(progress)}%`
}

/**
 * 格式化风险等级
 * @param level 风险等级
 * @returns 格式化后的风险等级字符串
 */
export const formatRiskLevel = (level?: string): string => {
  if (!level) return '未评估'
  
  const levelMap: Record<string, string> = {
    '无风险': '无风险',
    '低风险': '低风险',
    '中风险': '中风险',
    '高风险': '高风险'
  }
  
  return levelMap[level] || level
}

/**
 * 格式化文件状态
 * @param status 文件状态
 * @returns 格式化后的状态字符串
 */
export const formatFileStatus = (status: string): string => {
  const statusMap: Record<string, string> = {
    '待审查': '待审查',
    '审查中': '审查中',
    '已审查': '已审查'
  }
  
  return statusMap[status] || status
}

/**
 * 截断文本
 * @param text 原始文本
 * @param maxLength 最大长度
 * @param suffix 后缀，默认为 '...'
 * @returns 截断后的文本
 */
export const truncateText = (text: string, maxLength: number, suffix: string = '...'): string => {
  if (text.length <= maxLength) {
    return text
  }
  return text.slice(0, maxLength) + suffix
}
