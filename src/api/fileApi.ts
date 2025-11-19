import requestWithType from '@/utils/request';
import { AxiosHeaders } from 'axios';
import type { 
  UploadFileParams, 
  UploadFileResponse, 
  ArticleListParams, 
  ArticleListResponse, 
  Article 
} from '@/types/article';
import type { CustomAxiosRequestConfig } from '@/utils/request'; // 导入自定义请求配置类型

/**
 * 上传文件（支持docx、pdf）
 * @param params - 包含File对象的参数
 * @returns 上传成功后的文件信息（Article类型）
 */
export const uploadFile = async (params: UploadFileParams): Promise<Article> => {
  // 创建FormData（文件上传必须用FormData格式）
  const formData = new FormData();
  formData.append('file', params.file); // 键名'file'需与后端接口参数一致

  // 配置请求（覆盖默认Content-Type，FormData会自动设置正确的类型）
  const config: CustomAxiosRequestConfig = {
    url: '/api/files/upload',
    method: 'POST',
    data: formData,
    headers: new AxiosHeaders({  // 用AxiosHeaders设置multipart类型
      'Content-Type': 'multipart/form-data'
    }),
    showLoading: true // 显示加载动画（默认true，可省略）
  };

  return requestWithType<Article>(config);
};

/**
 * 获取文件列表（支持分页和搜索）
 * @param params - 分页参数和搜索关键词
 * @returns 分页的文件列表
 */
export const getFileList = async (
  params: ArticleListParams = { page: 1, pageSize: 10 }
): Promise<{ list: Article[]; pagination: { page: number; page_size: number; total: number; total_pages: number } }> => {
  const config: CustomAxiosRequestConfig = {
    url: '/api/files/list',
    method: 'GET',
    params: { page: params.page, page_size: params.pageSize, keyword: params.keyword }, // 转换参数名以匹配后端
    showLoading: false // 列表页可关闭全局加载，用局部加载动画
  };

  return requestWithType<{ list: Article[]; pagination: { page: number; page_size: number; total: number; total_pages: number } }>(config);
};

/**
 * 删除文件
 * @param articleId - 要删除的文件ID
 * @returns 删除结果（成功信息）
 */
export const deleteFile = async (articleId: number): Promise<null> => {
  const config: CustomAxiosRequestConfig = {
    url: `/api/files/delete/${articleId}`, // 路径参数传递文件ID
    method: 'DELETE',
    showLoading: true
  };

  return requestWithType<null>(config);
};

/**
 * 获取单个文件详情
 * @param articleId - 文件ID
 * @returns 单个文件的完整信息
 */
export const getFileDetail = async (articleId: number): Promise<ApiResponse<Article>> => {
  const config: CustomAxiosRequestConfig = {
    url: `/api/files/detail/${articleId}`,
    method: 'GET',
    showLoading: true
  };

  return requestWithType<ApiResponse<Article>>(config);
};

/**
 * 获取完整文档内容（用于详情页面显示和高亮）
 * @param articleId - 文件ID
 * @returns 完整文档内容和句子信息
 */
export const getFullContent = async (articleId: number): Promise<{
  article_id: number;
  article_name: string;
  full_content: string;
  sentences: Array<{
    content: string;
    start_pos: number;
    end_pos: number;
    id: number | null;
    has_problem: boolean | null;
    annotation_id: number | null;
    annotation_content: string;
  }>;
}> => {
  const config: CustomAxiosRequestConfig = {
    url: `/api/files/full-content/${articleId}`,
    method: 'GET',
    showLoading: true
  };

  return requestWithType<{
    article_id: number;
    article_name: string;
    full_content: string;
    sentences: Array<{
      content: string;
      start_pos: number;
      end_pos: number;
      id: number | null;
      has_problem: boolean | null;
      annotation_id: number | null;
      annotation_content: string;
    }>;
  }>(config);
};