// Jest测试设置
import { config } from '@vue/test-utils'

// 全局配置
config.global.mocks = {
  $t: (msg) => msg
}

// 模拟Element Plus
jest.mock('element-plus', () => ({
  ElMessage: {
    success: jest.fn(),
    error: jest.fn(),
    warning: jest.fn(),
    info: jest.fn()
  },
  ElLoading: {
    service: jest.fn(() => ({
      close: jest.fn()
    }))
  }
}))

// 模拟API请求
global.fetch = jest.fn()

// 模拟localStorage
const localStorageMock = {
  getItem: jest.fn(),
  setItem: jest.fn(),
  removeItem: jest.fn(),
  clear: jest.fn(),
}
global.localStorage = localStorageMock
