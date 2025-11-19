import { mount } from '@vue/test-utils'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import FileList from '@/components/FileList.vue'

describe('FileList.vue', () => {
  let wrapper

  const mockFiles = [
    {
      id: 1,
      filename: 'test1.pdf',
      file_type: 'pdf',
      file_size: 1024,
      status: 'completed',
      created_at: '2024-01-01T00:00:00Z'
    },
    {
      id: 2,
      filename: 'test2.docx',
      file_type: 'docx',
      file_size: 2048,
      status: 'processing',
      created_at: '2024-01-02T00:00:00Z'
    }
  ]

  beforeEach(() => {
    wrapper = mount(FileList, {
      props: {
        files: mockFiles,
        loading: false
      }
    })
  })

  it('渲染文件列表', () => {
    expect(wrapper.findAll('.file-item')).toHaveLength(2)
  })

  it('显示文件名', () => {
    expect(wrapper.text()).toContain('test1.pdf')
    expect(wrapper.text()).toContain('test2.docx')
  })

  it('显示文件状态', () => {
    expect(wrapper.text()).toContain('已完成')
    expect(wrapper.text()).toContain('处理中')
  })

  it('触发文件选择事件', async () => {
    const fileItem = wrapper.find('.file-item')
    await fileItem.trigger('click')
    
    expect(wrapper.emitted('file-select')).toBeTruthy()
    expect(wrapper.emitted('file-select')[0][0]).toBe(mockFiles[0])
  })

  it('显示加载状态', async () => {
    await wrapper.setProps({ loading: true })
    expect(wrapper.find('.loading-spinner').exists()).toBe(true)
  })

  it('显示空状态', async () => {
    await wrapper.setProps({ files: [] })
    expect(wrapper.find('.empty-state').exists()).toBe(true)
  })
})
