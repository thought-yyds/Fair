// src/utils/errorHandler.ts
/**
 * 统一错误处理工具
 * 提供网络异常、业务异常、用户友好的错误提示等功能
 */

import { ElMessage, ElMessageBox } from 'element-plus';
import type { AxiosError } from 'axios';

// 错误类型枚举
export enum ErrorType {
  NETWORK = 'NETWORK',
  TIMEOUT = 'TIMEOUT',
  SERVER = 'SERVER',
  CLIENT = 'CLIENT',
  VALIDATION = 'VALIDATION',
  UNKNOWN = 'UNKNOWN'
}

// 错误信息接口
export interface ErrorInfo {
  type: ErrorType;
  message: string;
  code?: string | number;
  details?: any;
}

/**
 * 解析Axios错误
 */
export function parseAxiosError(error: AxiosError): ErrorInfo {
  if (error.code === 'ECONNABORTED' || error.message.includes('timeout')) {
    return {
      type: ErrorType.TIMEOUT,
      message: '请求超时，请检查网络连接后重试',
      code: error.code
    };
  }

  if (error.response) {
    // 服务器响应了错误状态码
    const status = error.response.status;
    const data = error.response.data as any;
    
    if (status >= 500) {
      return {
        type: ErrorType.SERVER,
        message: data?.msg || `服务器错误 (${status})，请稍后重试`,
        code: status,
        details: data
      };
    } else if (status >= 400) {
      return {
        type: ErrorType.CLIENT,
        message: data?.msg || `请求错误 (${status})，请检查输入`,
        code: status,
        details: data
      };
    }
  } else if (error.request) {
    // 网络错误
    return {
      type: ErrorType.NETWORK,
      message: '网络连接失败，请检查网络设置',
      code: 'NETWORK_ERROR'
    };
  }

  // 未知错误
  return {
    type: ErrorType.UNKNOWN,
    message: error.message || '未知错误，请重试',
    code: 'UNKNOWN_ERROR'
  };
}

/**
 * 显示错误提示
 */
export function showError(error: ErrorInfo, showDetails = false): void {
  const { type, message, code, details } = error;
  
  let errorMessage = message;
  
  // 根据错误类型添加额外信息
  switch (type) {
    case ErrorType.NETWORK:
      errorMessage += '\n请检查网络连接或联系管理员';
      break;
    case ErrorType.TIMEOUT:
      errorMessage += '\n如果问题持续存在，请联系技术支持';
      break;
    case ErrorType.SERVER:
      errorMessage += '\n服务器可能正在维护，请稍后重试';
      break;
    case ErrorType.CLIENT:
      errorMessage += '\n请检查输入内容是否正确';
      break;
  }
  
  // 显示错误消息
  ElMessage.error({
    message: errorMessage,
    duration: 5000,
    showClose: true
  });
  
  // 如果需要显示详细信息（开发环境）
  if (showDetails && import.meta.env.DEV && details) {
    console.error('错误详情:', {
      type,
      code,
      message,
      details
    });
  }
}

/**
 * 显示确认对话框
 */
export function showConfirm(
  title: string,
  message: string,
  confirmText = '确定',
  cancelText = '取消'
): Promise<boolean> {
  return ElMessageBox.confirm(message, title, {
    confirmButtonText: confirmText,
    cancelButtonText: cancelText,
    type: 'warning',
    showClose: true
  }).then(() => true).catch(() => false);
}

/**
 * 显示重试确认
 */
export function showRetryConfirm(
  error: ErrorInfo,
  retryAction: () => Promise<void>
): void {
  const { type, message } = error;
  
  let retryMessage = `操作失败：${message}\n\n是否重试？`;
  
  if (type === ErrorType.NETWORK || type === ErrorType.TIMEOUT) {
    retryMessage = `网络连接异常：${message}\n\n是否重试？`;
  }
  
  showConfirm('操作失败', retryMessage, '重试', '取消').then((confirmed) => {
    if (confirmed) {
      retryAction();
    }
  });
}

/**
 * 处理异步操作的错误
 */
export async function handleAsyncError<T>(
  asyncFn: () => Promise<T>,
  errorHandler?: (error: ErrorInfo) => void
): Promise<T | null> {
  try {
    return await asyncFn();
  } catch (error) {
    const errorInfo = parseAxiosError(error as AxiosError);
    
    if (errorHandler) {
      errorHandler(errorInfo);
    } else {
      showError(errorInfo);
    }
    
    return null;
  }
}

/**
 * 处理文件上传错误
 */
export function handleUploadError(error: any): void {
  const errorInfo = parseAxiosError(error as AxiosError);
  
  // 文件上传特有的错误处理
  if (errorInfo.type === ErrorType.CLIENT) {
    if (errorInfo.message.includes('文件类型')) {
      errorInfo.message = '不支持的文件格式，请上传 .docx 或 .pdf 文件';
    } else if (errorInfo.message.includes('文件大小')) {
      errorInfo.message = '文件过大，请选择小于 10MB 的文件';
    }
  }
  
  showError(errorInfo);
}

/**
 * 处理审查操作错误
 */
export function handleReviewError(error: any): void {
  const errorInfo = parseAxiosError(error as AxiosError);
  
  // 审查操作特有的错误处理
  if (errorInfo.type === ErrorType.CLIENT) {
    if (errorInfo.message.includes('状态')) {
      errorInfo.message = '文件状态不允许此操作，请刷新页面后重试';
    }
  }
  
  showError(errorInfo);
}
