/**
 * 文件工具函数
 */

/**
 * 格式化文件大小
 * @param bytes 字节数
 * @returns 格式化后的文件大小字符串
 */
export const formatFileSize = (bytes: number): string => {
  if (bytes === 0) return '0 B'
  
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

/**
 * 获取文件扩展名
 * @param filename 文件名
 * @returns 文件扩展名（小写）
 */
export const getFileExtension = (filename: string): string => {
  return filename.slice((filename.lastIndexOf('.') - 1 >>> 0) + 2).toLowerCase()
}

/**
 * 检查文件类型是否支持
 * @param filename 文件名
 * @param allowedTypes 允许的文件类型数组
 * @returns 是否支持
 */
export const isFileTypeAllowed = (filename: string, allowedTypes: string[] = ['docx', 'pdf']): boolean => {
  const extension = getFileExtension(filename)
  return allowedTypes.includes(extension)
}

/**
 * 验证文件大小
 * @param file 文件对象
 * @param maxSizeInMB 最大文件大小（MB）
 * @returns 是否通过验证
 */
export const validateFileSize = (file: File, maxSizeInMB: number = 100): boolean => {
  const maxSizeInBytes = maxSizeInMB * 1024 * 1024
  return file.size <= maxSizeInBytes
}

/**
 * 验证文件
 * @param file 文件对象
 * @param allowedTypes 允许的文件类型
 * @param maxSizeInMB 最大文件大小（MB）
 * @returns 验证结果
 */
export const validateFile = (
  file: File, 
  allowedTypes: string[] = ['docx', 'pdf'], 
  maxSizeInMB: number = 100
): { valid: boolean; error?: string } => {
  if (!isFileTypeAllowed(file.name, allowedTypes)) {
    return {
      valid: false,
      error: `不支持的文件类型，仅支持：${allowedTypes.join(', ')}`
    }
  }

  if (!validateFileSize(file, maxSizeInMB)) {
    return {
      valid: false,
      error: `文件大小不能超过 ${maxSizeInMB}MB`
    }
  }

  return { valid: true }
}
