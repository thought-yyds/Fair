import axios, { 
  AxiosError,  
  AxiosHeaders  // 导入AxiosHeaders类
} from 'axios';

import type { AxiosResponse, InternalAxiosRequestConfig } from 'axios';
import type { AxiosInstance } from 'axios';
import { ElMessage, ElLoading } from 'element-plus';
import type { ApiResponse } from '@/types/common';
import { parseAxiosError, showError } from './errorHandler';

// 1. 精确定义自定义配置：headers使用Axios原生类型
export interface CustomAxiosRequestConfig extends Omit<InternalAxiosRequestConfig, 'headers'> {
  headers?: AxiosHeaders; // 明确使用AxiosHeaders类型（而非普通对象）
  showLoading?: boolean;
}

// 创建Axios实例
const createAxiosInstance = (): AxiosInstance => {
  const instance = axios.create({
    baseURL: import.meta.env.VITE_API_BASE_URL || '',
    timeout: 60000,
    headers: new AxiosHeaders({  // 用AxiosHeaders实例初始化默认headers
      'Content-Type': 'application/json;charset=utf-8'
    })
  });

  let loadingInstance: ReturnType<typeof ElLoading.service> | null = null;

  // 2. 请求拦截器：确保headers是AxiosHeaders实例
  instance.interceptors.request.use(
    (config: InternalAxiosRequestConfig) => {
      // 转换为自定义配置
      const customConfig = config as CustomAxiosRequestConfig;
      customConfig.showLoading = customConfig.showLoading ?? true;

      // 关键：如果headers不存在，用AxiosHeaders实例初始化（而非{}）
      if (!config.headers) {
        config.headers = new AxiosHeaders();
      }

      // 如果是FormData，移除Content-Type让浏览器自动设置boundary
      if ((config as any).data instanceof FormData) {
        try {
          config.headers.delete('Content-Type');
        } catch {}
      }

      // 显示加载动画
      if (customConfig.showLoading) {
        loadingInstance = ElLoading.service({
          text: '加载中...',
          lock: true
        });
      }

      // 添加Token（使用AxiosHeaders的set方法，符合类型要求）
      const token = localStorage.getItem('token');
      if (token) {
        config.headers.set('Authorization', `Bearer ${token}`);
      }

      return config;
    },
    (error: AxiosError) => {
      if (loadingInstance) loadingInstance.close();
      ElMessage.error(error.message || '请求发送失败');
      return Promise.reject(error);
    }
  );

  // 响应拦截器
  instance.interceptors.response.use(
    (response: AxiosResponse<ApiResponse<unknown>>) => {
      if (loadingInstance) loadingInstance.close();
      
      const res = response.data;
      if (!res.success && response.status !== 200) {
        ElMessage.error(res.msg || '请求失败，请重试');
        return Promise.reject(new Error(res.msg || 'Response Error'));
      }

      // 返回完整的响应结构，保持后端API的数据格式
      return response;
    },
    (error: AxiosError) => {
      if (loadingInstance) loadingInstance.close();
      
      // 使用统一的错误处理
      const errorInfo = parseAxiosError(error);
      showError(errorInfo, true); // 开发环境显示详细信息
      
      return Promise.reject(error);
    }
  );

  return instance;
};

const requestInstance = createAxiosInstance();

// 3. 请求函数：确保传入的headers是AxiosHeaders类型
const requestWithType = async <T>(config: CustomAxiosRequestConfig): Promise<T> => {
  // 合并配置时，用AxiosHeaders处理headers
  const requestConfig: InternalAxiosRequestConfig = {
    ...config,
    headers: config.headers ? new AxiosHeaders(config.headers) : new AxiosHeaders()
  };
  
  const response = await requestInstance(requestConfig) as AxiosResponse<unknown>;
  const payload = (response as AxiosResponse<any>).data;
  // 兼容两种返回：统一包装 { success,msg,data } 与 直接返回原始数据
  if (payload && typeof payload === 'object' && 'data' in payload && 'success' in payload) {
    return (payload as ApiResponse<T>).data;
  }
  return payload as T;
};

export default requestWithType;
