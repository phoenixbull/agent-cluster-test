# 🎮 跳一跳小游戏 - 项目开发计划

**项目 ID**: jump-jump-game  
**引擎**: LayaAir 3.3.8 (2D)  
**平台**: 微信小游戏、Web、移动端  
**工作流 ID**: wf-20260306-134210-4560  
**创建时间**: 2026-03-06

---

## 📋 项目概述

复刻微信经典小游戏"跳一跳"，使用 LayaAir 3.3.8 2D 引擎实现。

### 核心特性
- ✅ 按住蓄力、松开跳跃的核心玩法
- ✅ 程序化生成关卡、难度递增
- ✅ 触摸/鼠标操作、适配移动端
- ✅ 2D 像素风格美术
- ✅ 完整音效系统
- ✅ 微信小游戏适配

---

## 🏗️ 项目架构

```
jump-jump-game/
├── index.html              # 游戏入口
├── game.config.json        # LayaAir 配置
├── src/
│   ├── main.js             # 游戏主入口
│   ├── core/
│   │   ├── Game.js         # 游戏主类
│   │   ├── Scene.js        # 场景管理
│   │   ├── Entity.js       # 实体基类
│   │   └── Physics.js      # 物理系统
│   ├── player/
│   │   ├── Player.js       # 玩家角色
│   │   └── Input.js        # 输入处理
│   ├── level/
│   │   ├── Block.js        # 方块
│   │   ├── LevelGenerator.js # 关卡生成
│   │   └── LevelConfig.js  # 关卡配置
│   ├── ui/
│   │   ├── HUD.js          # 游戏 HUD
│   │   ├── StartScreen.js  # 开始界面
│   │   └── GameOver.js     # 结算界面
│   └── audio/
│       ├── AudioManager.js # 音效管理
│       └── Sounds.js       # 音效配置
├── res/
│   ├── images/             # 美术资源
│   │   ├── player.png      # 角色精灵
│   │   ├── blocks/         # 方块精灵
│   │   └── bg/             # 背景
│   └── audio/              # 音效资源
└── wx/                     # 微信小游戏适配
    ├── game.js
    └── game.json
```

---

## 📝 开发任务清单

### 阶段 1: 项目初始化 (Task-001) ✅
- [x] 创建项目结构
- [x] 配置 LayaAir 环境
- [x] 设计游戏架构
- [ ] 编写技术文档

**产出**:
- 项目目录结构
- LayaAir 配置文件
- 游戏架构图
- 技术选型文档

### 阶段 2: 核心玩法 (Task-002) 🔄
- [ ] 实现跳跃物理引擎
- [ ] 实现碰撞检测系统
- [ ] 实现分数计算逻辑
- [ ] 实现游戏状态管理

**产出**:
- `src/core/Physics.js` - 物理系统
- `src/player/Player.js` - 玩家角色
- `src/core/Game.js` - 游戏主逻辑

### 阶段 3: 美术资源 (Task-003) ⏳
- [ ] 设计角色精灵图
- [ ] 设计方块精灵图（多种材质）
- [ ] 设计背景图
- [ ] 设计 UI 元素

**产出**:
- `res/images/player.png`
- `res/images/blocks/*.png`
- `res/images/bg/*.png`

### 阶段 4: 场景渲染 (Task-004) ⏳
- [ ] 实现场景管理器
- [ ] 实现 2D 渲染系统
- [ ] 实现角色动画
- [ ] 实现特效系统

**产出**:
- `src/core/Scene.js`
- `src/core/Entity.js`

### 阶段 5: 关卡系统 (Task-005, Task-006) ⏳
- [ ] 设计关卡难度曲线
- [ ] 设计方块布局模式
- [ ] 实现关卡生成器
- [ ] 实现存档系统

**产出**:
- `src/level/LevelGenerator.js`
- `src/level/LevelConfig.js`
- `src/level/Block.js`

### 阶段 6: 操作输入 (Task-007) ⏳
- [ ] 实现触摸输入处理
- [ ] 实现蓄力指示器
- [ ] 实现操作反馈
- [ ] 适配移动端

**产出**:
- `src/player/Input.js`

### 阶段 7: 音效系统 (Task-008) ⏳
- [ ] 生成跳跃音效
- [ ] 生成落地音效
- [ ] 生成得分音效
- [ ] 生成背景音乐

**产出**:
- `res/audio/*.mp3`
- `src/audio/AudioManager.js`

### 阶段 8: UI 界面 (Task-009) ⏳
- [ ] 实现开始界面
- [ ] 实现游戏 HUD
- [ ] 实现结算界面
- [ ] 实现排行榜界面

**产出**:
- `src/ui/StartScreen.js`
- `src/ui/HUD.js`
- `src/ui/GameOver.js`

### 阶段 9: 微信适配 (Task-010) ⏳
- [ ] 适配微信小游戏平台
- [ ] 接入微信登录 API
- [ ] 接入好友排行榜
- [ ] 接入分享功能

**产出**:
- `wx/game.js`
- `wx/game.json`

### 阶段 10: 优化测试 (Task-011, Task-012) ⏳
- [ ] 性能分析
- [ ] 资源优化
- [ ] 功能测试
- [ ] Bug 修复
- [ ] 打包发布

**产出**:
- 性能分析报告
- 测试报告
- 发布包

---

## 🎯 核心玩法设计

### 游戏流程
```
开始界面 → 游戏开始 → 蓄力 → 跳跃 → 落地判定
   ↓                              ↓
游戏结束 ← 掉落 ← 未落在方块上 ← 成功
   ↓
结算界面 → 分享/重玩
```

### 物理参数
| 参数 | 值 | 说明 |
|------|-----|------|
| 蓄力时间 | 0-2000ms | 按住时间决定跳跃距离 |
| 跳跃力度 | 0-100 | 根据蓄力时间计算 |
| 重力 | 9.8 | 模拟真实重力 |
| 方块间距 | 50-150px | 程序化生成 |

### 分数规则
| 行为 | 分数 |
|------|------|
| 成功落在方块上 | +1 |
| 落在方块中心 | +2 (完美) |
| 连续完美 | +2, +4, +6... (连击) |

---

## 📊 工作流状态

| 阶段 | 状态 | Agent | 产出 |
|------|------|-------|------|
| 需求分析 | ✅ 完成 | Zoe | 任务分解 |
| UI/UX 设计 | ✅ 完成 | Designer | 设计方案 |
| 编码实现 | 🔄 进行中 | Codex, Claude-Code | 代码文件 |
| 测试 | ⏳ 待开始 | - | - |
| AI Review | ⏳ 待开始 | Reviewers | - |
| 创建 PR | ⏳ 待开始 | - | - |

---

## 🔗 相关链接

- **GitHub 仓库**: https://github.com/phoenixbull/jump-jump-game
- **LayaAir 文档**: https://ldc.layabox.com/doc/
- **微信小游戏文档**: https://developers.weixin.qq.com/minigame/dev/guide/

---

## 📱 钉钉通知配置

- Webhook: 已配置
- 通知事件：任务完成、任务失败、需要人工介入
- 通知频率：实时

---

**最后更新**: 2026-03-06 13:42  
**状态**: 🔄 开发中
