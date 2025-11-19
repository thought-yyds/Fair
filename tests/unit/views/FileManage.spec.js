import { mount } from '@vue/test-utils'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import FileManage from '@/views/FileManage.vue'
import { createPinia } from 'pinia'

// 模拟API
vi.mock('@/api/fileApi', () => ({
  getFiles: vi.fn(),
  uploadFile: vi.fn(),
  deleteFile: vi.fn()
}))

describe('FileManage.vue', () => {
  let wrapper
  let pinia

  beforeEach(() => {
    pinia = createPinia()
    wrapper = mount(FileManage, {
      global: {
        plugins: [pinia]
      }
    })
  })

  it('渲染文件管理页面', () => {
    expect(wrapper.find('.file-manage').exists()).toBe(true)
  })

  it('显示文件上传组件', () => {
    expect(wrapper.findComponent({ name: 'FileUploader' }).exists()).toBe(true)
  })

  it('显示文件列表组件', () => {
    expect(wrapper.findComponent({ name: 'FileList' }).exists()).toBe(true)
  })

  it('处理文件上传', async () => {
    const file = new File(['test content'], 'test.pdf', { type: 'application/pdf' })
    
    await wrapper.vm.handleFileUpload(file)
    
    // 验证上传逻辑
    expect(wrapper.vm.uploading).toBe(true)
  })

  it('处理文件删除', async () => {
    const fileId = 1
    
    await wrapper.vm.handleFileDelete(fileId)
    
    // 验证删除逻辑
    expect(wrapper.vm.files).not.toContain(
      expect.objectContaining({ id: fileId })
    )
  })

  it('处理文件选择', async () => {
    const selectedFile = { id: 1, filename: 'test.pdf' }
    
    await wrapper.vm.handleFileSelect(selectedFile)
    
    expect(wrapper.vm.selectedFile).toEqual(selectedFile)
  })
})
