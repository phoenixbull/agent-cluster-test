/**
 * 任务表单组件 (创建/编辑)
 */
import { useState } from 'react'
import { useTaskStore } from '@/store/taskStore'
import type { TaskCreate, TaskPriority } from '@/types'

interface Props {
  onClose: () => void
  onSuccess: () => void
  initialData?: TaskCreate
}

export default function TaskForm({ onClose, onSuccess, initialData }: Props) {
  const { createTask, isLoading } = useTaskStore()
  
  const [formData, setFormData] = useState<TaskCreate>({
    title: initialData?.title || '',
    description: initialData?.description || '',
    priority: initialData?.priority || 'medium',
    due_date: initialData?.due_date || '',
  })
  
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    try {
      await createTask(formData)
      onSuccess()
    } catch {
      // 错误已在 store 中处理
    }
  }
  
  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-lg max-w-md w-full mx-4">
        <div className="p-6 border-b border-gray-200">
          <h2 className="text-xl font-semibold">
            {initialData ? '编辑任务' : '创建任务'}
          </h2>
        </div>
        
        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              标题 *
            </label>
            <input
              type="text"
              required
              className="input"
              value={formData.title}
              onChange={(e) =>
                setFormData({ ...formData, title: e.target.value })
              }
              placeholder="任务标题"
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              描述
            </label>
            <textarea
              className="input"
              rows={3}
              value={formData.description}
              onChange={(e) =>
                setFormData({ ...formData, description: e.target.value })
              }
              placeholder="任务描述（可选）"
            />
          </div>
          
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                优先级
              </label>
              <select
                className="input"
                value={formData.priority}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    priority: e.target.value as TaskPriority,
                  })
                }
              >
                <option value="low">低</option>
                <option value="medium">中</option>
                <option value="high">高</option>
                <option value="urgent">紧急</option>
              </select>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                截止日期
              </label>
              <input
                type="date"
                className="input"
                value={formData.due_date ? formData.due_date.split('T')[0] : ''}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    due_date: e.target.value
                      ? new Date(e.target.value).toISOString()
                      : '',
                  })
                }
              />
            </div>
          </div>
          
          <div className="flex justify-end gap-2 pt-4">
            <button
              type="button"
              onClick={onClose}
              className="btn btn-secondary"
            >
              取消
            </button>
            <button
              type="submit"
              disabled={isLoading}
              className="btn btn-primary"
            >
              {isLoading ? '保存中...' : '保存'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
