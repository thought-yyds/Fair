// src/utils/validators.ts
/**
 * 数据验证工具
 * 提供前端表单验证、文件类型检查、数据格式验证等功能
 */

// 文件类型验证
export const validateFileType = (file: File, allowedTypes: string[] = ['docx', 'pdf']): boolean => {
  const fileExtension = file.name.split('.').pop()?.toLowerCase();
  return fileExtension ? allowedTypes.includes(fileExtension) : false;
};

// 文件大小验证
export const validateFileSize = (file: File, maxSizeMB: number = 10): boolean => {
  const fileSizeMB = file.size / (1024 * 1024);
  return fileSizeMB <= maxSizeMB;
};

// 文件名验证
export const validateFileName = (fileName: string): { valid: boolean; message?: string } => {
  if (!fileName || fileName.trim().length === 0) {
    return { valid: false, message: '文件名不能为空' };
  }

  if (fileName.length > 255) {
    return { valid: false, message: '文件名过长，请控制在255个字符以内' };
  }

  // 检查非法字符
  const invalidChars = /[<>:"/\\|?*]/;
  if (invalidChars.test(fileName)) {
    return { valid: false, message: '文件名包含非法字符，请移除 < > : " / \\ | ? * 等字符' };
  }

  return { valid: true };
};

// 搜索关键词验证
export const validateSearchKeyword = (keyword: string): { valid: boolean; message?: string } => {
  if (!keyword || keyword.trim().length === 0) {
    return { valid: true }; // 空关键词是允许的
  }

  if (keyword.length > 100) {
    return { valid: false, message: '搜索关键词过长，请控制在100个字符以内' };
  }

  // 检查SQL注入风险字符
  const sqlInjectionChars = /['";\-]/;
  if (sqlInjectionChars.test(keyword)) {
    return { valid: false, message: '搜索关键词包含非法字符' };
  }

  return { valid: true };
};

// 分页参数验证
export const validatePaginationParams = (page: number, pageSize: number): { valid: boolean; message?: string } => {
  if (page < 1) {
    return { valid: false, message: '页码必须大于0' };
  }

  if (pageSize < 1 || pageSize > 100) {
    return { valid: false, message: '每页条数必须在1-100之间' };
  }

  return { valid: true };
};

// 文件上传验证
export const validateFileUpload = (file: File): { valid: boolean; message?: string } => {
  // 1. 文件类型验证
  if (!validateFileType(file)) {
    return { 
      valid: false, 
      message: '不支持的文件格式，仅支持 .docx 和 .pdf 文件' 
    };
  }

  // 2. 文件大小验证
  if (!validateFileSize(file)) {
    const fileSizeMB = (file.size / (1024 * 1024)).toFixed(1);
    return { 
      valid: false, 
      message: `文件过大（${fileSizeMB}MB），请选择小于10MB的文件` 
    };
  }

  // 3. 文件名验证
  const fileNameValidation = validateFileName(file.name);
  if (!fileNameValidation.valid) {
    return fileNameValidation;
  }

  return { valid: true };
};

// 审查参数验证
export const validateReviewParams = (articleId: number): { valid: boolean; message?: string } => {
  if (!articleId || articleId <= 0) {
    return { valid: false, message: '无效的文件ID' };
  }

  if (!Number.isInteger(articleId)) {
    return { valid: false, message: '文件ID必须是整数' };
  }

  return { valid: true };
};

// 表单验证规则
export const formRules = {
  // 文件名规则
  fileName: [
    { required: true, message: '请输入文件名', trigger: 'blur' },
    { min: 1, max: 255, message: '文件名长度在1到255个字符', trigger: 'blur' },
    { pattern: /^[^<>:"/\\|?*]+$/, message: '文件名不能包含特殊字符', trigger: 'blur' }
  ],

  // 搜索关键词规则
  searchKeyword: [
    { max: 100, message: '搜索关键词不能超过100个字符', trigger: 'blur' },
    { pattern: /^[^'";\-]*$/, message: '搜索关键词包含非法字符', trigger: 'blur' }
  ],

  // 分页规则
  page: [
    { type: 'number', min: 1, message: '页码必须大于0', trigger: 'blur' }
  ],
  pageSize: [
    { type: 'number', min: 1, max: 100, message: '每页条数必须在1-100之间', trigger: 'blur' }
  ]
};

// 实时验证器
export const createRealtimeValidator = (validator: (value: any) => { valid: boolean; message?: string }) => {
  return (value: any) => {
    const result = validator(value);
    return result.valid ? true : result.message;
  };
};

// 文件上传实时验证
export const createFileUploadValidator = () => {
  return (file: File) => {
    const result = validateFileUpload(file);
    return result.valid ? true : result.message;
  };
};

// 搜索关键词实时验证
export const createSearchValidator = () => {
  return (keyword: string) => {
    const result = validateSearchKeyword(keyword);
    return result.valid ? true : result.message;
  };
};

// 分页参数实时验证
export const createPaginationValidator = () => {
  return (page: number, pageSize: number) => {
    const result = validatePaginationParams(page, pageSize);
    return result.valid ? true : result.message;
  };
};
