/**
 * 任务状态管理 (Zustand)
 */
import { create } from 'zustand'
import type { Task, TaskCreate, TaskUpdate, TaskListResponse, TaskStatistics } from '@/types'
import { tasksApi } from '@/services/api'

interface TaskState {
  tasks: Task[]
  statistics: TaskStatistics | null
  isLoading: boolean
  error: string | null
  pagination: {
    page: number
    pageSize: number
    total: number
  }
  
  // Actions
  fetchTasks: (page?: number, pageSize?: number) => Promise<void>
  fetchTask: (id: number) => Promise<Task>
  createTask: (data: TaskCreate) => Promise<Task>
  updateTask: (id: number, data: TaskUpdate) => Promise<Task>
  deleteTask: (id: number) => Promise<void>
  fetchStatistics: () => Promise<void>
  clearError: () => void
}

export const useTaskStore = create<TaskState>((set, get) => ({
  tasks: [],
  statistics: null,
  isLoading: false,
  error: null,
  pagination: {
    page: 1,
    pageSize: 20,
    total: 0,
  },

  fetchTasks: async (page = 1, pageSize = 20) => {
    set({ isLoading: true, error: null })
    try {
      const response: TaskListResponse = await tasksApi.list(page, pageSize)
      set({
        tasks: response.items,
        pagination: {
          page: response.page,
          pageSize: response.page_size,
          total: response.total,
        },
        isLoading: false,
      })
    } catch (error) {
      const message = error instanceof Error ? error.message : '获取任务失败'
      set({ error: message, isLoading: false })
    }
  },

  fetchTask: async (id: number) => {
    set({ isLoading: true, error: null })
    try {
      const task = await tasksApi.get(id)
      set({ isLoading: false })
      return task
    } catch (error) {
      const message = error instanceof Error ? error.message : '获取任务失败'
      set({ error: message, isLoading: false })
      throw error
    }
  },

  createTask: async (data: TaskCreate) => {
    set({ isLoading: true, error: null })
    try {
      const task = await tasksApi.create(data)
      // 刷新任务列表
      await get().fetchTasks(get().pagination.page, get().pagination.pageSize)
      set({ isLoading: false })
      return task
    } catch (error) {
      const message = error instanceof Error ? error.message : '创建任务失败'
      set({ error: message, isLoading: false })
      throw error
    }
  },

  updateTask: async (id: number, data: TaskUpdate) => {
    set({ isLoading: true, error: null })
    try {
      const task = await tasksApi.update(id, data)
      // 更新本地任务列表
      set((state) => ({
        tasks: state.tasks.map((t) => (t.id === id ? task : t)),
        isLoading: false,
      }))
      return task
    } catch (error) {
      const message = error instanceof Error ? error.message : '更新任务失败'
      set({ error: message, isLoading: false })
      throw error
    }
  },

  deleteTask: async (id: number) => {
    set({ isLoading: true, error: null })
    try {
      await tasksApi.delete(id)
      // 从本地移除
      set((state) => ({
        tasks: state.tasks.filter((t) => t.id !== id),
        pagination: {
          ...state.pagination,
          total: state.pagination.total - 1,
        },
        isLoading: false,
      }))
    } catch (error) {
      const message = error instanceof Error ? error.message : '删除任务失败'
      set({ error: message, isLoading: false })
      throw error
    }
  },

  fetchStatistics: async () => {
    try {
      const statistics = await tasksApi.getStatistics()
      set({ statistics })
    } catch (error) {
      console.error('获取统计信息失败:', error)
    }
  },

  clearError: () => set({ error: null }),
}))
