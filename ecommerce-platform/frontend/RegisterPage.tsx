/**
 * 注册页面
 */
import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuthStore } from '@/store/authStore'

export default function RegisterPage() {
  const navigate = useNavigate()
  const { register, isLoading, error, clearError } = useAuthStore()
  
  const [formData, setFormData] = useState({
    email: '',
    username: '',
    password: '',
    confirmPassword: '',
  })
  
  const [validationError, setValidationError] = useState<string | null>(null)
  
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    clearError()
    setValidationError(null)
    
    // 前端验证
    if (formData.password !== formData.confirmPassword) {
      setValidationError('两次输入的密码不一致')
      return
    }
    
    if (formData.password.length < 8) {
      setValidationError('密码至少需要 8 个字符')
      return
    }
    
    try {
      await register(formData.email, formData.username, formData.password)
      navigate('/login')
    } catch {
      // 错误已在 store 中处理
    }
  }
  
  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="max-w-md w-full">
        <div className="bg-white rounded-lg shadow-md p-8">
          <h1 className="text-2xl font-bold text-center mb-8">
            📋 Task Dashboard
          </h1>
          
          <h2 className="text-xl font-semibold mb-6">注册账号</h2>
          
          {(error || validationError) && (
            <div className="error-message mb-4">
              {validationError || error}
            </div>
          )}
          
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                邮箱
              </label>
              <input
                type="email"
                required
                className="input"
                value={formData.email}
                onChange={(e) =>
                  setFormData({ ...formData, email: e.target.value })
                }
                placeholder="your@email.com"
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                用户名
              </label>
              <input
                type="text"
                required
                minLength={3}
                className="input"
                value={formData.username}
                onChange={(e) =>
                  setFormData({ ...formData, username: e.target.value })
                }
                placeholder="username"
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                密码
              </label>
              <input
                type="password"
                required
                minLength={8}
                className="input"
                value={formData.password}
                onChange={(e) =>
                  setFormData({ ...formData, password: e.target.value })
                }
                placeholder="至少 8 位，包含大小写字母和数字"
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                确认密码
              </label>
              <input
                type="password"
                required
                className="input"
                value={formData.confirmPassword}
                onChange={(e) =>
                  setFormData({ ...formData, confirmPassword: e.target.value })
                }
                placeholder="再次输入密码"
              />
            </div>
            
            <button
              type="submit"
              disabled={isLoading}
              className="w-full btn btn-primary py-2"
            >
              {isLoading ? '注册中...' : '注册'}
            </button>
          </form>
          
          <p className="mt-6 text-center text-sm text-gray-600">
            已有账号？{' '}
            <Link to="/login" className="text-blue-600 hover:underline">
              立即登录
            </Link>
          </p>
        </div>
      </div>
    </div>
  )
}
