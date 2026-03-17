# 🎨 Phase 3 - 前端开发输出

**开发者**: Claude-Code Agent (前端专家)  
**技术栈**: React 18 + TypeScript + Vite + Tailwind CSS  
**完成时间**: 2026-03-09  

---

## 📁 项目结构

```
frontend/
├── src/
│   ├── main.tsx              # 应用入口
│   ├── App.tsx               # 根组件
│   ├── vite-env.d.ts
│   ├── components/           # 可复用组件
│   │   ├── ui/              # UI 基础组件
│   │   │   ├── Button.tsx
│   │   │   ├── Input.tsx
│   │   │   ├── Card.tsx
│   │   │   └── Modal.tsx
│   │   ├── layout/          # 布局组件
│   │   │   ├── Header.tsx
│   │   │   ├── Footer.tsx
│   │   │   └── Sidebar.tsx
│   │   └── post/            # 文章相关
│   │       ├── PostCard.tsx
│   │       ├── PostList.tsx
│   │       └── Editor.tsx
│   ├── pages/               # 页面组件
│   │   ├── Home.tsx
│   │   ├── Articles.tsx
│   │   ├── ArticleDetail.tsx
│   │   ├── Write.tsx
│   │   └── Login.tsx
│   ├── hooks/               # 自定义 Hooks
│   │   ├── useAuth.ts
│   │   ├── usePosts.ts
│   │   └── useApi.ts
│   ├── stores/              # 状态管理
│   │   └── authStore.ts
│   ├── services/            # API 服务
│   │   └── api.ts
│   ├── utils/               # 工具函数
│   │   └── helpers.ts
│   └── types/               # TypeScript 类型
│       └── index.ts
├── package.json
├── tsconfig.json
├── tailwind.config.js
├── vite.config.ts
└── index.html
```

---

## 🔧 核心代码

### 1. API 服务 (services/api.ts)

```typescript
import axios from 'axios';

const API_BASE_URL = '/api/v1';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// 请求拦截器 - 添加 Token
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// 响应拦截器 - 处理错误
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export const authAPI = {
  login: (email: string, password: string) =>
    api.post('/auth/login', { email, password }),
  register: (email: string, password: string, nickname: string) =>
    api.post('/auth/register', { email, password, nickname }),
  logout: () => api.post('/auth/logout'),
};

export const postsAPI = {
  getPosts: (skip = 0, limit = 20) =>
    api.get('/posts', { params: { skip, limit } }),
  getPost: (id: number) => api.get(`/posts/${id}`),
  createPost: (data: any) => api.post('/posts', data),
  updatePost: (id: number, data: any) => api.put(`/posts/${id}`, data),
  deletePost: (id: number) => api.delete(`/posts/${id}`),
};

export default api;
```

### 2. 认证 Hook (hooks/useAuth.ts)

```typescript
import { create } from 'zustand';
import { authAPI } from '../services/api';

interface User {
  id: number;
  email: string;
  nickname: string;
  avatar?: string;
}

interface AuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
  register: (email: string, password: string, nickname: string) => Promise<void>;
}

export const useAuth = create<AuthState>((set) => ({
  user: null,
  token: localStorage.getItem('token'),
  isAuthenticated: !!localStorage.getItem('token'),
  
  login: async (email, password) => {
    const response = await authAPI.login(email, password);
    const { access_token, user } = response.data;
    
    localStorage.setItem('token', access_token);
    set({ user, token: access_token, isAuthenticated: true });
  },
  
  logout: () => {
    localStorage.removeItem('token');
    set({ user: null, token: null, isAuthenticated: false });
  },
  
  register: async (email, password, nickname) => {
    await authAPI.register(email, password, nickname);
  },
}));
```

### 3. 首页组件 (pages/Home.tsx)

```typescript
import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { postsAPI } from '../services/api';
import PostCard from '../components/post/PostCard';
import { Post } from '../types';

export default function Home() {
  const [posts, setPosts] = useState<Post[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadPosts();
  }, []);

  const loadPosts = async () => {
    try {
      const response = await postsAPI.getPosts(0, 10);
      setPosts(response.data);
    } catch (error) {
      console.error('加载文章失败:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Hero Section */}
      <section className="bg-gradient-to-r from-blue-500 to-purple-600 text-white py-20">
        <div className="max-w-6xl mx-auto px-4 text-center">
          <h1 className="text-5xl font-bold mb-4">欢迎来到我的博客</h1>
          <p className="text-xl mb-8">分享技术，记录生活</p>
          <Link
            to="/write"
            className="bg-white text-blue-600 px-8 py-3 rounded-lg font-semibold hover:bg-gray-100 transition"
          >
            开始写作
          </Link>
        </div>
      </section>

      {/* 精选文章 */}
      <section className="max-w-6xl mx-auto px-4 py-12">
        <h2 className="text-3xl font-bold mb-8">精选文章</h2>
        {loading ? (
          <div className="text-center py-12">加载中...</div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {posts.map((post) => (
              <PostCard key={post.id} post={post} />
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
```

### 4. 文章卡片组件 (components/post/PostCard.tsx)

```typescript
import { Link } from 'react-router-dom';
import { Post } from '../../types';

interface PostCardProps {
  post: Post;
}

export default function PostCard({ post }: PostCardProps) {
  const formatDate = (date: string) => {
    return new Date(date).toLocaleDateString('zh-CN', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
    });
  };

  return (
    <article className="bg-white rounded-lg shadow-md overflow-hidden hover:shadow-lg transition">
      <Link to={`/post/${post.id}`}>
        <div className="p-6">
          <h3 className="text-xl font-bold mb-2 text-gray-900 line-clamp-2">
            {post.title}
          </h3>
          <p className="text-gray-600 mb-4 line-clamp-3">
            {post.content.replace(/[#*`]/g, '').substring(0, 150)}...
          </p>
          <div className="flex items-center text-sm text-gray-500">
            <span>{formatDate(post.created_at)}</span>
            <span className="mx-2">•</span>
            <span>{post.view_count} 阅读</span>
          </div>
        </div>
      </Link>
    </article>
  );
}
```

### 5. Markdown 编辑器 (components/post/Editor.tsx)

```typescript
import { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

interface EditorProps {
  value: string;
  onChange: (value: string) => void;
}

export default function Editor({ value, onChange }: EditorProps) {
  const [mode, setMode] = useState<'edit' | 'preview' | 'split'>('split');

  return (
    <div className="flex h-full border border-gray-300 rounded-lg overflow-hidden">
      {/* 编辑区 */}
      {(mode === 'edit' || mode === 'split') && (
        <div className="flex-1 border-r border-gray-300">
          <textarea
            value={value}
            onChange={(e) => onChange(e.target.value)}
            className="w-full h-full p-4 font-mono text-sm resize-none focus:outline-none"
            placeholder="使用 Markdown 语法写作..."
          />
        </div>
      )}

      {/* 预览区 */}
      {(mode === 'preview' || mode === 'split') && (
        <div className="flex-1 p-4 overflow-auto prose prose-lg max-w-none">
          <ReactMarkdown remarkPlugins={[remarkGfm]}>
            {value}
          </ReactMarkdown>
        </div>
      )}

      {/* 模式切换 */}
      <div className="absolute top-2 right-2 flex space-x-2">
        <button
          onClick={() => setMode('edit')}
          className={`px-3 py-1 rounded ${mode === 'edit' ? 'bg-blue-500 text-white' : 'bg-gray-200'}`}
        >
          编辑
        </button>
        <button
          onClick={() => setMode('split')}
          className={`px-3 py-1 rounded ${mode === 'split' ? 'bg-blue-500 text-white' : 'bg-gray-200'}`}
        >
          分屏
        </button>
        <button
          onClick={() => setMode('preview')}
          className={`px-3 py-1 rounded ${mode === 'preview' ? 'bg-blue-500 text-white' : 'bg-gray-200'}`}
        >
          预览
        </button>
      </div>
    </div>
  );
}
```

### 6. 写作页面 (pages/Write.tsx)

```typescript
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import Editor from '../components/post/Editor';
import { postsAPI } from '../services/api';
import { useAuth } from '../hooks/useAuth';

export default function Write() {
  const navigate = useNavigate();
  const { isAuthenticated } = useAuth();
  const [title, setTitle] = useState('');
  const [content, setContent] = useState('');
  const [saving, setSaving] = useState(false);

  const handlePublish = async () => {
    if (!title.trim() || !content.trim()) {
      alert('请填写标题和内容');
      return;
    }

    setSaving(true);
    try {
      await postsAPI.createPost({
        title,
        content,
        status: 'published',
      });
      alert('发布成功！');
      navigate('/');
    } catch (error) {
      alert('发布失败，请重试');
    } finally {
      setSaving(false);
    }
  };

  if (!isAuthenticated) {
    navigate('/login');
    return null;
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* 顶部工具栏 */}
      <div className="bg-white border-b border-gray-300 px-4 py-3 flex justify-between items-center sticky top-0">
        <input
          type="text"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          placeholder="输入文章标题..."
          className="text-2xl font-bold flex-1 focus:outline-none"
        />
        <div className="flex space-x-3">
          <button
            onClick={() => setContent('')}
            className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
          >
            清空
          </button>
          <button
            onClick={handlePublish}
            disabled={saving}
            className="px-6 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:opacity-50"
          >
            {saving ? '发布中...' : '发布文章'}
          </button>
        </div>
      </div>

      {/* 编辑器 */}
      <div className="h-[calc(100vh-80px)] p-4">
        <Editor value={content} onChange={setContent} />
      </div>
    </div>
  );
}
```

### 7. 应用入口 (App.tsx)

```typescript
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Header from './components/layout/Header';
import Home from './pages/Home';
import Articles from './pages/Articles';
import ArticleDetail from './pages/ArticleDetail';
import Write from './pages/Write';
import Login from './pages/Login';

function App() {
  return (
    <BrowserRouter>
      <div className="min-h-screen bg-gray-50">
        <Header />
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/articles" element={<Articles />} />
          <Route path="/post/:id" element={<ArticleDetail />} />
          <Route path="/write" element={<Write />} />
          <Route path="/login" element={<Login />} />
        </Routes>
      </div>
    </BrowserRouter>
  );
}

export default App;
```

---

## 📦 依赖配置

### package.json

```json
{
  "name": "blog-frontend",
  "version": "1.0.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "tsc && vite build",
    "preview": "vite preview",
    "lint": "eslint . --ext ts,tsx"
  },
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-router-dom": "^6.21.0",
    "axios": "^1.6.5",
    "zustand": "^4.4.7",
    "react-markdown": "^9.0.1",
    "remark-gfm": "^4.0.0"
  },
  "devDependencies": {
    "@types/react": "^18.2.45",
    "@types/react-dom": "^18.2.18",
    "@vitejs/plugin-react": "^4.2.1",
    "typescript": "^5.3.3",
    "vite": "^5.0.10",
    "tailwindcss": "^3.4.0",
    "autoprefixer": "^10.4.16",
    "postcss": "^8.4.32"
  }
}
```

### vite.config.ts

```typescript
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
});
```

---

## ✅ 完成功能

| 功能 | 状态 | 代码行数 |
|------|------|----------|
| 首页 | ✅ 完成 | ~100 行 |
| 文章列表 | ✅ 完成 | ~80 行 |
| 文章详情 | ✅ 完成 | ~120 行 |
| 写作编辑器 | ✅ 完成 | ~150 行 |
| 用户认证 | ✅ 完成 | ~100 行 |
| UI 组件库 | ✅ 完成 | ~200 行 |

**总代码量**: ~750 行  
**组件数量**: 15+ 个

---

**状态**: ✅ Phase 3-Frontend 完成  
**下一步**: Phase 4 测试验证 (Tester)
