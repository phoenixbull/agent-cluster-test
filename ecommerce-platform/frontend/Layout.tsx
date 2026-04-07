/**
 * 布局组件
 */
import { Outlet, Link, useNavigate } from 'react-router-dom'
import { useAuthStore } from '@/store/authStore'

export default function Layout() {
  const navigate = useNavigate()
  const { user, logout } = useAuthStore()
  
  const handleLogout = () => {
    logout()
    navigate('/login')
  }
  
  return (
    <div className="min-h-screen bg-gray-50">
      {/* 顶部导航 */}
      <header className="bg-white shadow">
        <div className="container flex items-center justify-between h-16">
          <Link to="/" className="text-xl font-bold text-blue-600">
            📋 Task Dashboard
          </Link>
          
          <div className="flex items-center gap-4">
            <span className="text-sm text-gray-600">
              欢迎，{user?.username}
            </span>
            <button
              onClick={handleLogout}
              className="btn btn-secondary text-sm"
            >
              退出登录
            </button>
          </div>
        </div>
      </header>
      
      {/* 侧边栏 + 主内容 */}
      <div className="container flex mt-6">
        {/* 侧边栏 */}
        <aside className="w-64 mr-6">
          <nav className="bg-white rounded-lg shadow p-4">
            <ul className="space-y-2">
              <li>
                <Link
                  to="/"
                  className="block p-2 rounded hover:bg-gray-100 text-gray-700"
                >
                  📊 仪表盘
                </Link>
              </li>
              <li>
                <Link
                  to="/tasks"
                  className="block p-2 rounded hover:bg-gray-100 text-gray-700"
                >
                  📝 任务列表
                </Link>
              </li>
            </ul>
          </nav>
        </aside>
        
        {/* 主内容 */}
        <main className="flex-1">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
