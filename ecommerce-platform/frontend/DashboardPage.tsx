/**
 * 仪表盘页面
 */
import { useEffect, useState } from 'react'
import { useTaskStore } from '@/store/taskStore'
import TaskList from '@/components/TaskList'
import TaskForm from '@/components/TaskForm'
import Statistics from '@/components/Statistics'

export default function DashboardPage() {
  const { fetchTasks, fetchStatistics, statistics, isLoading } = useTaskStore()
  const [showCreateForm, setShowCreateForm] = useState(false)
  
  useEffect(() => {
    fetchTasks()
    fetchStatistics()
  }, [fetchTasks, fetchStatistics])
  
  return (
    <div className="space-y-6">
      {/* 页面标题 */}
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">任务管理</h1>
        <button
          onClick={() => setShowCreateForm(true)}
          className="btn btn-primary"
        >
          + 新建任务
        </button>
      </div>
      
      {/* 统计卡片 */}
      {statistics && <Statistics data={statistics} />}
      
      {/* 任务列表 */}
      <div className="bg-white rounded-lg shadow">
        <div className="p-6 border-b border-gray-200">
          <h2 className="text-lg font-semibold">任务列表</h2>
        </div>
        <TaskList isLoading={isLoading} />
      </div>
      
      {/* 创建任务模态框 */}
      {showCreateForm && (
        <TaskForm
          onClose={() => setShowCreateForm(false)}
          onSuccess={() => {
            setShowCreateForm(false)
            fetchTasks()
            fetchStatistics()
          }}
        />
      )}
    </div>
  )
}
