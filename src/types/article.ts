import type{ PageParams} from "./common";
/**
 * 文件（Article）模型类型（对应后端的 Article 表）
 */

export interface Article {
  id: number;
  name: string;
  type?: string;
  description?: string;
  upload_time: string; //上传时间（UTC）
  status: '待审查' | '审查中' | '已审查';//枚举
  review_progress: number;//审查进度
  risk_level?: '无风险' | '低风险' | '中风险' | '高风险'; // 风险等级
  review_time?: string; //审查完成时间（UTC）
}

/**
 * 文件列表查询参数（继承分页参数，可扩展）
 */
export interface ArticleListParams extends PageParams {
  keyword?: string; // 可选：按文件名搜索
}

/**
 * 文件列表响应（分页）
 */
export interface ArticleListResponse {
  list: Article[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

/**
 * 文件上传请求参数（FormData 类型）
 */
export interface UploadFileParams {
  file: File; // 上传的文件对象
}

/**
 * 文件上传响应（返回单个文件信息）
 */
export type UploadFileResponse = Article;