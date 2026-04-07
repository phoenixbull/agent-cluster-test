/**
 * API 服务层
 */
import axios, { AxiosError, InternalAxiosRequestConfig } from 'axios'
import type {
  User,
  LoginRequest,
  RegisterRequest,
  AuthResponse,
  Task,
  TaskCreate,
  TaskUpdate,
  TaskListResponse,
  TaskStatistics,
  ApiError,
} from '@/types'

// 创建 axios 实例
const api = axios.create({
  baseURL: '/api/v1',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// 请求拦截器 - 添加 Token
api.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const token = localStorage.getItem('access_token')
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

// 响应拦截器 - 处理错误
api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError<ApiError>) => {
    if (error.response?.status === 401) {
      // Token 过期，尝试刷新
      const refreshToken = localStorage.getItem('refresh_token')
      if (refreshToken) {
        try {
          const response = await axios.post('/api/v1/auth/refresh', {
            refresh_token: refreshToken,
          })
          const { access_token, refresh_token } = response.data as AuthResponse
          localStorage.setItem('access_token', access_token)
          localStorage.setItem('refresh_token', refresh_token)
          
          // 重试原请求
          if (error.config) {
            error.config.headers.Authorization = `Bearer ${access_token}`
            return api.request(error.config)
          }
        } catch {
          // 刷新失败，清除登录状态
          localStorage.removeItem('access_token')
          localStorage.removeItem('refresh_token')
          window.location.href = '/login'
        }
      }
    }
    return Promise.reject(error)
  }
)

// ============== 认证 API ==============

export const authApi = {
  register: async (data: RegisterRequest): Promise<User> => {
    const response = await api.post<User>('/auth/register', data)
    return response.data
  },

  login: async (data: LoginRequest): Promise<AuthResponse> => {
    const formData = new URLSearchParams()
    formData.append('username', data.username)
    formData.append('password', data.password)
    
    const response = await api.post<AuthResponse>('/auth/login', formData, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    })
    return response.data
  },

  refreshToken: async (refreshToken: string): Promise<AuthResponse> => {
    const response = await api.post<AuthResponse>('/auth/refresh', {
      refresh_token: refreshToken,
    })
    return response.data
  },

  getCurrentUser: async (): Promise<User> => {
    const response = await api.get<User>('/users/me')
    return response.data
  },

  updateProfile: async (data: Partial<User>): Promise<User> => {
    const response = await api.patch<User>('/users/me', data)
    return response.data
  },
}

// ============== 任务 API ==============

export const tasksApi = {
  list: async (
    page = 1,
    pageSize = 20,
    status?: string,
    priority?: string
  ): Promise<TaskListResponse> => {
    const params = new URLSearchParams({
      page: page.toString(),
      page_size: pageSize.toString(),
    })
    if (status) params.append('status', status)
    if (priority) params.append('priority', priority)
    
    const response = await api.get<TaskListResponse>(`/tasks?${params}`)
    return response.data
  },

  get: async (id: number): Promise<Task> => {
    const response = await api.get<Task>(`/tasks/${id}`)
    return response.data
  },

  create: async (data: TaskCreate): Promise<Task> => {
    const response = await api.post<Task>('/tasks', data)
    return response.data
  },

  update: async (id: number, data: TaskUpdate): Promise<Task> => {
    const response = await api.patch<Task>(`/tasks/${id}`, data)
    return response.data
  },

  delete: async (id: number): Promise<void> => {
    await api.delete(`/tasks/${id}`)
  },

  getStatistics: async (): Promise<TaskStatistics> => {
    const response = await api.get<TaskStatistics>('/tasks/statistics')
    return response.data
  },
}

export default api
