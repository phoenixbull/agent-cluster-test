/**
 * 任务列表组件
 */
import { useTaskStore } from '@/store/taskStore'
import dayjs from 'dayjs'
import relativeTime from 'dayjs/plugin/relativeTime'
import 'dayjs/locale/zh-cn'

dayjs.extend(relativeTime)
dayjs.locale('zh-cn')

interface Props {
  isLoading: boolean
}

export default function TaskList({ isLoading }: Props) {
  const { tasks, updateTask, deleteTask } = useTaskStore()
  
  const handleStatusChange = async (taskId: number, newStatus: string) => {
    await updateTask(taskId, { status: newStatus as any })
  }
  
  const handleDelete = async (taskId: number) => {
    if (confirm('确定要删除这个任务吗？')) {
      await deleteTask(taskId)
    }
  }
  
  const getStatusLabel = (status: string) => {
    const labels: Record<string, string> = {
      pending: '待处理',
      in_progress: '进行中',
      completed: '已完成',
      cancelled: '已取消',
    }
    return labels[status] || status
  }
  
  const getPriorityLabel = (priority: string) => {
    const labels: Record<string, string> = {
      low: '低',
      medium: '中',
      high: '高',
      urgent: '紧急',
    }
    return labels[priority] || priority
  }
  
  if (isLoading) {
    return (
      <div className="loading">
        <div className="spinner"></div>
      </div>
    )
  }
  
  if (tasks.length === 0) {
    return (
      <div className="p-8 text-center text-gray-500">
        暂无任务，点击右上角创建第一个任务吧！
      </div>
    )
  }
  
  return (
    <div className="overflow-x-auto">
      <table className="table">
        <thead>
          <tr>
            <th>任务</th>
            <th>状态</th>
            <th>优先级</th>
            <th>截止日期</th>
            <th>创建时间</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          {tasks.map((task) => (
            <tr key={task.id}>
              <td>
                <div className="font-medium">{task.title}</div>
                {task.description && (
                  <div className="text-sm text-gray-500 truncate max-w-xs">
                    {task.description}
                  </div>
                )}
              </td>
              <td>
                <select
                  value={task.status}
                  onChange={(e) => handleStatusChange(task.id, e.target.value)}
                  className="text-sm border rounded px-2 py-1"
                >
                  <option value="pending">待处理</option>
                  <option value="in_progress">进行中</option>
                  <option value="completed">已完成</option>
                  <option value="cancelled">已取消</option>
                </select>
              </td>
              <td>
                <span className={`priority-${task.priority}`}>
                  {getPriorityLabel(task.priority)}
                </span>
              </td>
              <td>
                {task.due_date ? (
                  <span className={dayjs(task.due_date).isBefore(dayjs()) ? 'text-red-600' : ''}>
                    {dayjs(task.due_date).format('YYYY-MM-DD')}
                  </span>
                ) : (
                  <span className="text-gray-400">-</span>
                )}
              </td>
              <td className="text-sm text-gray-500">
                {dayjs(task.created_at).fromNow()}
              </td>
              <td>
                <button
                  onClick={() => handleDelete(task.id)}
                  className="text-red-600 hover:text-red-800 text-sm"
                >
                  删除
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
