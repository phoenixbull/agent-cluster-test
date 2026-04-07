# 🎨 UI/UX 设计文档

**项目名称**: 个人博客系统  
**版本**: 1.0  
**创建时间**: 2026-03-09  
**创建者**: Designer Agent

---

## 1. 设计风格

### 1.1 设计理念
- **简洁现代**: 极简主义，内容为主
- **清晰易读**: 良好的排版和对比度
- **响应式**: 适配各种设备

### 1.2 色彩系统

**主色调**:
```
Primary:   #3B82F6 (蓝色 - 信任、专业)
Secondary: #10B981 (绿色 - 成功、活力)
Accent:    #F59E0B (橙色 - 活力、温暖)
```

**中性色**:
```
Gray 900:  #111827 (最深色 - 文字)
Gray 700:  #374151 (次深色 - 次要文字)
Gray 500:  #6B7280 (中灰色 - 提示)
Gray 300:  #D1D5DB (浅灰色 - 边框)
Gray 100:  #F3F4F6 (最浅色 - 背景)
White:     #FFFFFF
```

**功能色**:
```
Success:   #10B981
Warning:   #F59E0B
Error:     #EF4444
Info:      #3B82F6
```

### 1.3 字体系统

**英文字体**:
```
Primary: Inter (无衬线，现代)
Code:    Fira Code (等宽，代码)
```

**中文字体**:
```
Primary: -apple-system, BlinkMacSystemFont, "Segoe UI"
Fallback: "Microsoft YaHei", "PingFang SC"
```

**字号**:
```
xs:  12px (辅助文字)
sm:  14px (次要文字)
base: 16px (正文)
lg:  18px (小标题)
xl:  20px (中标题)
2xl: 24px (大标题)
3xl: 30px (超大标题)
```

---

## 2. 页面设计

### 2.1 首页

**布局结构**:
```
┌─────────────────────────────────────┐
│           Header (导航栏)            │
├─────────────────────────────────────┤
│                                     │
│         Hero Section                │
│    "欢迎来到我的博客"                │
│         [搜索框]                     │
│                                     │
├─────────────────────────────────────┤
│  Featured Posts  (精选文章)          │
│  ┌─────┐ ┌─────┐ ┌─────┐           │
│  │     │ │     │ │     │           │
│  └─────┘ └─────┘ └─────┘           │
├─────────────────────────────────────┤
│  Recent Posts  (最新文章)            │
│  ┌───────────────────────────┐      │
│  │ 文章 1 标题...             │      │
│  │ 文章 2 标题...             │      │
│  │ 文章 3 标题...             │      │
│  └───────────────────────────┘      │
├─────────────────────────────────────┤
│           Footer                    │
└─────────────────────────────────────┘
```

### 2.2 文章列表页

**布局**:
```
┌─────────────────────────────────────┐
│  Header                             │
├──────────────┬──────────────────────┤
│              │                      │
│  Categories  │   Article List       │
│  (左侧边栏)   │   (右侧内容)          │
│              │                      │
│  - 全部       │  ┌──────────────┐   │
│  - 技术       │  │ 文章卡片 1    │   │
│  - 生活       │  ├──────────────┤   │
│  - 随笔       │  │ 文章卡片 2    │   │
│              │  ├──────────────┤   │
│  Tags        │  │ 文章卡片 3    │   │
│  (标签云)     │  └──────────────┘   │
│              │                      │
│              │   [分页]             │
└──────────────┴──────────────────────┘
```

### 2.3 文章详情页

**布局**:
```
┌─────────────────────────────────────┐
│  Header                             │
├─────────────────────────────────────┤
│                                     │
│     文章标题 (H1, 居中)              │
│                                     │
│  作者 | 发布时间 | 阅读量 | 分类     │
│                                     │
├─────────────────────────────────────┤
│                                     │
│         文章内容 (Markdown)          │
│         (最大宽度 800px, 居中)        │
│                                     │
│  [代码块]                            │
│  [图片]                              │
│  [引用]                              │
│                                     │
├─────────────────────────────────────┤
│                                     │
│     标签：#python #fastapi          │
│                                     │
│     [点赞] [分享] [收藏]             │
│                                     │
├─────────────────────────────────────┤
│                                     │
│         评论区                       │
│         ┌──────────────┐            │
│         │ 评论 1        │            │
│         │ 评论 2        │            │
│         └──────────────┘            │
│                                     │
│         [发表评论]                   │
│                                     │
└─────────────────────────────────────┘
```

### 2.4 写作编辑器页

**布局**:
```
┌─────────────────────────────────────┐
│  [返回]  写文章          [发布] [保存]│
├─────────────────────────────────────┤
│  标题输入框 (占满宽度)                │
├────────────────┬────────────────────┤
│                │                    │
│  Markdown 编辑  │   实时预览         │
│  (左侧 50%)     │   (右侧 50%)       │
│                │                    │
│  - 工具栏       │   渲染后的内容      │
│  - 编辑区       │                    │
│  - 行号        │                    │
│                │                    │
├────────────────┴────────────────────┤
│  分类选择 | 标签输入 | 封面上传      │
└─────────────────────────────────────┘
```

---

## 3. 组件设计

### 3.1 按钮

**主要按钮**:
```tsx
<button className="bg-blue-500 hover:bg-blue-600 text-white px-6 py-2 rounded-lg">
  发布文章
</button>
```

**次要按钮**:
```tsx
<button className="border border-gray-300 hover:bg-gray-50 px-6 py-2 rounded-lg">
  保存草稿
</button>
```

### 3.2 卡片

**文章卡片**:
```tsx
<article className="border border-gray-200 rounded-lg p-4 hover:shadow-lg transition">
  <h3 className="text-xl font-bold mb-2">文章标题</h3>
  <p className="text-gray-600 mb-4">文章摘要...</p>
  <div className="flex items-center text-sm text-gray-500">
    <span>作者</span>
    <span className="mx-2">•</span>
    <span>2026-03-09</span>
  </div>
</article>
```

### 3.3 输入框

**文本输入**:
```tsx
<input 
  className="w-full border border-gray-300 rounded-lg px-4 py-2 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
  placeholder="请输入..."
/>
```

### 3.4 导航栏

**顶部导航**:
```tsx
<nav className="bg-white shadow-sm">
  <div className="max-w-6xl mx-auto px-4">
    <div className="flex justify-between items-center h-16">
      <div className="text-xl font-bold">我的博客</div>
      <div className="flex space-x-4">
        <a href="/" className="hover:text-blue-500">首页</a>
        <a href="/articles" className="hover:text-blue-500">文章</a>
        <a href="/about" className="hover:text-blue-500">关于</a>
      </div>
    </div>
  </div>
</nav>
```

---

## 4. 响应式设计

### 4.1 断点

```css
/* 手机 */
@media (max-width: 640px) { ... }

/* 平板 */
@media (min-width: 641px) and (max-width: 1024px) { ... }

/* 桌面 */
@media (min-width: 1025px) { ... }
```

### 4.2 适配策略

**移动端**:
- 导航栏折叠为汉堡菜单
- 单栏布局
- 字体适当缩小
- 触摸友好（按钮足够大）

**平板端**:
- 双栏布局
- 侧边栏可折叠
- 适中字体大小

**桌面端**:
- 三栏布局
- 充分利用空间
- 悬停效果

---

## 5. 交互设计

### 5.1 加载状态

**骨架屏**:
```tsx
<div className="animate-pulse">
  <div className="h-4 bg-gray-200 rounded w-3/4 mb-2"></div>
  <div className="h-4 bg-gray-200 rounded w-1/2"></div>
</div>
```

**Loading Spinner**:
```tsx
<div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
```

### 5.2 错误提示

**Toast 通知**:
```tsx
<div className="fixed top-4 right-4 bg-red-500 text-white px-4 py-2 rounded-lg shadow-lg">
  ❌ 操作失败，请重试
</div>
```

### 5.3 成功反馈

**成功提示**:
```tsx
<div className="fixed top-4 right-4 bg-green-500 text-white px-4 py-2 rounded-lg shadow-lg">
  ✅ 发布成功！
</div>
```

---

## 6. 暗色主题

**色彩映射**:
```
背景：Gray 900 (#111827)
卡片：Gray 800 (#1F2937)
文字：Gray 100 (#F3F4F6)
边框：Gray 700 (#374151)
```

**切换方式**:
- 右上角主题切换按钮
- 自动跟随系统
- LocalStorage 保存偏好

---

**设计版本**: v1.0  
**最后更新**: 2026-03-09  
**审核状态**: 待评审
