import requestWithType from '@/utils/request';
import type { CustomAxiosRequestConfig } from '@/utils/request';
import type { 
  ReviewProgress, 
  ReviewDetail, 
  StartReviewParams 
} from '@/types/review';
import { AxiosHeaders } from 'axios';

/**
 * 启动文件审查
 * @param params - 包含文件ID的参数
 * @returns 启动结果（提示信息）
 */
export const startReview = async (
  params: StartReviewParams
): Promise<{ success: boolean; msg: string; data: null }> => {
  const config: CustomAxiosRequestConfig = {
    url: `/api/reviews/start/${params.articleId}`, // 路径参数传递文件ID
    method: 'POST',
    showLoading: true,
    headers: new AxiosHeaders({
      'Content-Type': 'application/json'
    })
  };

  return requestWithType<{ success: boolean; msg: string; data: null }>(config);
};

/**
 * 查询审查进度（单次查询）
 * @param articleId - 文件ID
 * @returns 进度信息（进度百分比、状态、风险等级）
 */
export const getReviewProgress = async (
  articleId: number
): Promise<{ success: boolean; data: ReviewProgress }> => {
  const config: CustomAxiosRequestConfig = {
    url: `/api/reviews/progress/${articleId}`,
    method: 'GET',
    showLoading: false // 轮询场景下关闭全局加载，用局部动画
  };

  return requestWithType<{ success: boolean; data: ReviewProgress }>(config);
};

/**
 * 获取审查详情（包含违规句子、风险等级等）
 * @param articleId - 文件ID
 * @returns 完整的审查结果
 */
export const getReviewDetail = async (
  articleId: number
): Promise<ReviewDetail> => {
  const config: CustomAxiosRequestConfig = {
    url: `/api/reviews/detail/${articleId}`,
    method: 'GET',
    showLoading: true
  };

  return requestWithType<ReviewDetail>(config);
};

/**
 * 创建SSE连接监听审查进度
 * @param articleId - 文件ID
 * @param onProgress - 进度更新回调函数
 * @param onComplete - 完成回调函数
 * @param onError - 错误回调函数
 * @returns EventSource实例
 */
export const createReviewProgressSSE = (
  articleId: number,
  onProgress: (progress: number) => void,
  onComplete: () => void,
  onError: (error: Event) => void
): EventSource => {
  const eventSource = new EventSource(`/api/reviews/progress/sse/${articleId}`);
  
  eventSource.onmessage = (event) => {
    const data = event.data;
    if (data === 'complete') {
      onComplete();
      eventSource.close();
    } else {
      const progress = parseInt(data, 10);
      if (!isNaN(progress)) {
        onProgress(progress);
      }
    }
  };
  
  eventSource.onerror = (error) => {
    onError(error);
    eventSource.close();
  };
  
  return eventSource;
};
