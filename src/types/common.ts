// src/types/common.ts
/**
 * 后端 API 统一响应格式
 * @template T - 响应数据的类型（泛型，支持不同接口的不同数据结构）
 */
export interface ApiResponse<T> {
  success: boolean;
  msg: string;
  data: T;
}


/**
 * 分页查询参数
 */
export interface PageParams {
  page: number;
  pageSize: number;
}



/**
 * 分页响应格式
 * @template T - 列表项的类型
 */
export interface PageResponse<T> {
  list: T[];
  total: number;
  page: number;
  pageSize: number;
}
