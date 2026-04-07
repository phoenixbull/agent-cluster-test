/**
 * 统计卡片组件
 */
import type { TaskStatistics } from '@/types'

interface Props {
  data: TaskStatistics
}

export default function Statistics({ data }: Props) {
  const statCards = [
    {
      title: '总任务数',
      value: data.total,
      color: 'bg-blue-500',
    },
    {
      title: '待处理',
      value: data.by_status.pending || 0,
      color: 'bg-gray-500',
    },
    {
      title: '进行中',
      value: data.by_status.in_progress || 0,
      color: 'bg-yellow-500',
    },
    {
      title: '已完成',
      value: data.by_status.completed || 0,
      color: 'bg-green-500',
    },
    {
      title: '已过期',
      value: data.overdue,
      color: 'bg-red-500',
    },
    {
      title: '今日完成',
      value: data.completed_today,
      color: 'bg-purple-500',
    },
  ]
  
  return (
    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
      {statCards.map((stat) => (
        <div
          key={stat.title}
          className="bg-white rounded-lg shadow p-4"
        >
          <div className="text-sm text-gray-600 mb-1">{stat.title}</div>
          <div className="flex items-center justify-between">
            <div className="text-2xl font-bold">{stat.value}</div>
            <div className={`w-3 h-3 rounded-full ${stat.color}`}></div>
          </div>
        </div>
      ))}
    </div>
  )
}
