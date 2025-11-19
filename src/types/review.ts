// src/types/review.ts
/**
 * 审查进度响应类型
 */


export interface ReviewProgress {
  progress: number; // 进度（0-100）
  status: '待审查' | '审查中' | '已审查'; // 状态
  risk_level?: '无风险' | '低风险' | '中风险' | '高风险'; // 风险等级（完成后才有）
}

/**
 * 违规句子类型（审查详情中返回）
 * 匹配后端新的数据结构：annotation_content直接来自Annotation表的content字段
 */
export interface ViolationSentence {
  id: number; // 句子ID
  content: string; // 句子内容
  annotation_content: string; // 标注内容（为什么违规）- 来自Annotation表的content字段
}

/**
 * 审查详情响应类型
 * 匹配后端新的响应格式
 */
export interface ReviewDetail {
  article_name: string; // 文档名称
  review_time: string; // 审查完成时间
  risk_level: string; // 风险等级
  total_violation: number; // 总违规数量
  violation_sentences: ViolationSentence[]; // 违规句子列表
  document_content: string; // 原始文档内容
}

/**
 * 启动审查请求参数
 */
export interface StartReviewParams {
  articleId: number; // 文件ID
}