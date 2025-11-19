// src/utils/feedbackManager.ts
/**
 * 用户反馈管理工具
 * 统一管理操作确认、成功提示、错误提示、进度反馈等
 */

import { ElMessage, ElMessageBox, ElNotification } from 'element-plus';
import type { ElMessageBoxOptions } from 'element-plus';

// 消息类型
export type MessageType = 'success' | 'warning' | 'info' | 'error';

// 通知类型
export type NotificationType = 'success' | 'warning' | 'info' | 'error';

// 确认对话框类型
export type ConfirmType = 'warning' | 'info' | 'success' | 'error';

/**
 * 消息提示管理
 */
export class MessageManager {
  private static messageQueue: string[] = [];
  

  // 显示消息
  static show(
    message: string, 
    type: MessageType = 'info', 
    duration = 3000,
    showClose = true
  ) {
    // 避免重复显示相同消息
    if (this.messageQueue.includes(message)) {
      return;
    }

    this.messageQueue.push(message);
    
    ElMessage({
      message,
      type,
      duration,
      showClose,
      onClose: () => {
        const index = this.messageQueue.indexOf(message);
        if (index > -1) {
          this.messageQueue.splice(index, 1);
        }
      }
    });
  }

  // 成功消息
  static success(message: string, duration = 3000) {
    this.show(message, 'success', duration);
  }

  // 错误消息
  static error(message: string, duration = 5000) {
    this.show(message, 'error', duration);
  }

  // 警告消息
  static warning(message: string, duration = 4000) {
    this.show(message, 'warning', duration);
  }

  // 信息消息
  static info(message: string, duration = 3000) {
    this.show(message, 'info', duration);
  }

  // 清除所有消息
  static clear() {
    ElMessage.closeAll();
    this.messageQueue = [];
  }
}

/**
 * 通知管理
 */
export class NotificationManager {
  // 显示通知
  static show(
    title: string,
    message: string,
    type: NotificationType = 'info',
    duration = 4500,
    position: 'top-right' | 'top-left' | 'bottom-right' | 'bottom-left' = 'top-right'
  ) {
    ElNotification({
      title,
      message,
      type,
      duration,
      position,
      showClose: true
    });
  }

  // 成功通知
  static success(title: string, message: string, duration = 3000) {
    this.show(title, message, 'success', duration);
  }

  // 错误通知
  static error(title: string, message: string, duration = 6000) {
    this.show(title, message, 'error', duration);
  }

  // 警告通知
  static warning(title: string, message: string, duration = 5000) {
    this.show(title, message, 'warning', duration);
  }

  // 信息通知
  static info(title: string, message: string, duration = 4000) {
    this.show(title, message, 'info', duration);
  }
}

/**
 * 确认对话框管理
 */
export class ConfirmManager {
  // 显示确认对话框
  static async show(
    title: string,
    message: string,
    type: ConfirmType = 'warning',
    options: Partial<ElMessageBoxOptions> = {}
  ): Promise<boolean> {
    try {
      await ElMessageBox.confirm(message, title, {
        type,
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        showClose: true,
        ...options
      });
      return true;
    } catch {
      return false;
    }
  }

  // 删除确认
  static async confirmDelete(itemName: string, itemType = '项目'): Promise<boolean> {
    return this.show(
      '确认删除',
      `确定要删除${itemType} "${itemName}" 吗？\n\n删除后无法恢复！`,
      'warning',
      {
        confirmButtonText: '删除',
        cancelButtonText: '取消',
        confirmButtonClass: 'el-button--danger'
      }
    );
  }

  // 批量操作确认
  static async confirmBatchOperation(
    operation: string,
    count: number,
    itemType = '项目'
  ): Promise<boolean> {
    return this.show(
      '确认批量操作',
      `确定要${operation} ${count} 个${itemType}吗？\n\n此操作不可撤销！`,
      'warning',
      {
        confirmButtonText: operation,
        cancelButtonText: '取消'
      }
    );
  }

  // 保存确认
  static async confirmSave(hasUnsavedChanges = true): Promise<boolean> {
    if (!hasUnsavedChanges) return true;
    
    return this.show(
      '确认保存',
      '当前有未保存的更改，确定要保存吗？',
      'info',
      {
        confirmButtonText: '保存',
        cancelButtonText: '取消'
      }
    );
  }
}

/**
 * 进度反馈管理
 */
export class ProgressManager {
  private static progressInstances: Map<string, any> = new Map();

  // 显示进度条
  static showProgress(
    key: string,
    title: string,
    message: string,
    percentage = 0
  ) {
    const instance = ElMessageBox({
      title,
      message: `
        <div style="margin: 20px 0;">
          <p>${message}</p>
          <div style="margin-top: 15px;">
            <el-progress 
              :percentage="${percentage}" 
              :show-text="true"
              :stroke-width="8"
            ></el-progress>
          </div>
        </div>
      `,
      showClose: false,
      closeOnClickModal: false,
      closeOnPressEscape: false,
      showCancelButton: false,
      showConfirmButton: false
    });

    this.progressInstances.set(key, instance);
    return instance;
  }

  // 更新进度
  static updateProgress(key: string, percentage: number, message?: string) {
    const instance = this.progressInstances.get(key);
    if (instance) {
      // 这里需要更新进度条，但ElMessageBox不支持动态更新
      // 可以考虑使用自定义组件或通知
      console.log(`Progress ${key}: ${percentage}% - ${message || ''}`);
    }
  }

  // 隐藏进度条
  static hideProgress(key: string) {
    const instance = this.progressInstances.get(key);
    if (instance) {
      instance.close();
      this.progressInstances.delete(key);
    }
  }

  // 清除所有进度条
  static clearAllProgress() {
    this.progressInstances.forEach(instance => instance.close());
    this.progressInstances.clear();
  }
}

/**
 * 操作反馈管理
 */
export class OperationFeedback {
  // 文件上传反馈
  static uploadSuccess(fileName: string) {
    MessageManager.success(`文件 "${fileName}" 上传成功！`);
  }

  static uploadError(fileName: string, error: string) {
    MessageManager.error(`文件 "${fileName}" 上传失败：${error}`);
  }

  // 文件删除反馈
  static deleteSuccess(fileName: string) {
    MessageManager.success(`文件 "${fileName}" 删除成功`);
  }

  static deleteError(fileName: string, error: string) {
    MessageManager.error(`文件 "${fileName}" 删除失败：${error}`);
  }

  // 审查操作反馈
  static reviewStarted(fileName: string) {
    MessageManager.info(`文件 "${fileName}" 审查已启动`);
  }

  static reviewCompleted(fileName: string, riskLevel: string) {
    MessageManager.success(`文件 "${fileName}" 审查完成，风险等级：${riskLevel}`);
  }

  static reviewError(fileName: string, error: string) {
    MessageManager.error(`文件 "${fileName}" 审查失败：${error}`);
  }

  // 搜索反馈
  static searchNoResults(keyword: string) {
    MessageManager.warning(`搜索 "${keyword}" 未找到结果`);
  }

  static searchError(error: string) {
    MessageManager.error(`搜索失败：${error}`);
  }

  // 分页反馈
  static pageChanged(page: number, totalPages: number) {
    MessageManager.info(`已切换到第 ${page} 页，共 ${totalPages} 页`);
  }

  // 批量操作反馈
  static batchOperationSuccess(operation: string, count: number) {
    MessageManager.success(`成功${operation} ${count} 个项目`);
  }

  static batchOperationError(operation: string, error: string) {
    MessageManager.error(`${operation}失败：${error}`);
  }
}

/**
 * 系统状态反馈
 */
export class SystemFeedback {
  // 网络状态
  static networkError() {
    NotificationManager.error(
      '网络连接异常',
      '请检查网络连接后重试',
      8000
    );
  }

  static networkRestored() {
    NotificationManager.success(
      '网络连接已恢复',
      '系统已重新连接',
      3000
    );
  }

  // 系统维护
  static systemMaintenance() {
    NotificationManager.warning(
      '系统维护中',
      '系统正在维护，部分功能可能暂时不可用',
      10000
    );
  }

  // 版本更新
  static versionUpdated(version: string) {
    NotificationManager.info(
      '版本更新',
      `系统已更新到版本 ${version}，请刷新页面`,
      5000
    );
  }
}

// 导出默认实例
export const message = MessageManager;
export const notification = NotificationManager;
export const confirm = ConfirmManager;
export const progress = ProgressManager;
export const operation = OperationFeedback;
export const system = SystemFeedback;
