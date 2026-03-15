# 🎮 箭头会拐弯 - 微信小程序游戏复刻

经典微信小程序游戏"箭头会拐弯"的 HTML5 复刻版。

## 🎯 游戏玩法

1. **箭头自动前进** - 箭头会持续向当前方向移动
2. **点击转向** - 点击屏幕或按空格键使箭头 90 度右转
3. **避开障碍** - 撞到红色障碍物或边界游戏结束
4. **连击系统** - 连续无碰撞转弯获得连击分数

## 🚀 快速开始

### 在浏览器中运行

```bash
# 进入项目目录
cd /home/admin/.openclaw/workspace/arrow-turn-game

# 直接用浏览器打开
open index.html  # macOS
xdg-open index.html  # Linux
start index.html  # Windows
```

### 本地服务器

```bash
# Python 3
python3 -m http.server 8080

# 访问 http://localhost:8080
```

## 📱 控制方式

| 平台 | 操作 |
|------|------|
| **移动端** | 点击屏幕任意位置 |
| **桌面端** | 鼠标点击 或 空格键 |

## 🎨 游戏特性

- ✅ 流畅的 60 FPS 动画
- ✅ 响应式设计，适配各种屏幕
- ✅ 箭头拖尾效果
- ✅ 连击系统
- ✅ 多关卡设计
- ✅ 触摸和键盘双支持

## 📂 项目结构

```
arrow-turn-game/
├── index.html      # 游戏主页面
├── game.js         # 核心游戏逻辑
└── README.md       # 项目说明
```

## 🛠️ 技术栈

- **HTML5 Canvas** - 游戏渲染
- **Vanilla JavaScript** - 无框架，原生实现
- **CSS3** - 响应式布局
- **RequestAnimationFrame** - 流畅动画

## 🎯 游戏目标

- 尽可能获得高分
- 保持连击不断
- 通过所有关卡

## 📊 分数计算

- **基础分数**: 每移动 10 像素 = 1 分
- **连击奖励**: 连击数 × 10 分
- **关卡奖励**: 每关完成 +100 分

## 🔧 开发说明

### 修改游戏速度

编辑 `game.js` 中的 `arrow.speed` 属性：

```javascript
this.arrow = {
    speed: 200, // 像素/秒，数值越大越快
    // ...
};
```

### 添加新关卡

在 `loadLevels()` 方法中添加：

```javascript
{
    level: 3,
    obstacles: [
        { x: 100, y: 100, width: 20, height: 100 },
        // ... 更多障碍物
    ],
    targetScore: 30
}
```

### 修改箭头颜色

编辑 `arrow.color` 属性：

```javascript
this.arrow = {
    color: '#FF6B6B', // 改为其他颜色
    // ...
};
```

## 📝 待开发功能

- [ ] 更多关卡设计（目标 20 关）
- [ ] 道具系统（加速、减速、无敌）
- [ ] 排行榜系统
- [ ] 音效和背景音乐
- [ ] 粒子效果（碰撞、得分）
- [ ] 微信小游戏适配

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

MIT License

---

**享受游戏！** 🎮✨
