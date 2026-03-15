# 🔄 清除浏览器缓存指南

## 问题原因
浏览器缓存了旧版本的 `game.js` 文件，导致看不到最新修复。

---

## 🚀 快速解决（推荐）

### 方法 1：强制刷新（最简单）

**Windows/Linux:**
```
Ctrl + Shift + R
```
或
```
Ctrl + F5
```

**Mac:**
```
Cmd + Shift + R
```

---

### 方法 2：清空缓存并硬重新加载

**Chrome/Edge:**
1. 按 `F12` 打开开发者工具
2. **右键点击**刷新按钮
3. 选择 **"清空缓存并硬性重新加载"**

**Firefox:**
1. 按 `Ctrl + Shift + Delete`
2. 选择 "缓存"
3. 点击 "立即清除"

**Safari:**
1. 按 `Cmd + Option + E`
2. 按 `Cmd + R`

---

### 方法 3：禁用缓存（开发模式）

**Chrome/Edge:**
1. 按 `F12` 打开开发者工具
2. 点击 **Network（网络）** 标签
3. 勾选 **"Disable cache（禁用缓存）"**
4. 保持开发者工具打开状态
5. 刷新页面

---

### 方法 4：添加版本号强制刷新

在浏览器地址栏访问：
```
http://39.107.101.25:9000/?v=2.0.1
```

或
```
http://39.107.101.25:9000/index.html?t=202603091939
```

---

### 方法 5：清除所有浏览数据

**Chrome:**
1. `Ctrl + Shift + Delete` (Windows) 或 `Cmd + Shift + Delete` (Mac)
2. 时间范围：**全部时间**
3. 勾选：**缓存的图片和文件**
4. 点击 **清除数据**

**Firefox:**
1. `Ctrl + Shift + Delete`
2. 选择 **缓存**
3. 点击 **立即清除**

**Safari:**
1. Safari → 偏好设置 → 隐私
2. 点击 **管理网站数据**
3. 点击 **全部移除**

---

## 📱 移动端清除缓存

### iOS Safari
1. 设置 → Safari 浏览器
2. 向下滚动
3. 点击 **清除历史记录与网站数据**

### Android Chrome
1. Chrome → 三点菜单 → 历史记录
2. 点击 **清除浏览数据**
3. 选择 **缓存的图片和文件**
4. 点击 **清除数据**

---

## ✅ 验证是否生效

### 方法 1：查看文件版本
打开浏览器控制台（F12），输入：
```javascript
console.log('Game version check...');
```
如果看到 `v2.0.1` 说明是最新版本。

### 方法 2：检查调试信息
开始游戏后，控制台应该显示：
```
Game initialized!
Starting game...
Game started! State: playing
Arrow reset to: xxx yyy
```

### 方法 3：查看网络请求
1. 按 `F12` 打开开发者工具
2. 点击 **Network（网络）** 标签
3. 刷新页面
4. 找到 `game.js`
5. 查看 **Size** 列，应该是 **23KB** 左右

---

## 🎯 最快的方法

**推荐顺序:**
1. **Ctrl + Shift + R** (强制刷新) ⭐⭐⭐⭐⭐
2. **添加版本号** `?v=2.0.1` ⭐⭐⭐⭐
3. **禁用缓存** (开发者工具) ⭐⭐⭐
4. **清除所有缓存** ⭐⭐

---

## 🔍 如果还是不行

1. **尝试隐私/无痕模式**
   ```
   Ctrl + Shift + N (Chrome/Edge)
   Ctrl + Shift + P (Firefox)
   Cmd + Shift + N (Safari)
   ```

2. **换个浏览器试试**
   - Chrome
   - Firefox
   - Edge
   - Safari

3. **清除 DNS 缓存**
   ```bash
   # Windows
   ipconfig /flushdns
   
   # Mac
   sudo dscacheutil -flushcache
   
   # Linux
   sudo systemd-resolve --flush-caches
   ```

---

**刷新后应该能看到:**
- ✅ 游戏正常启动
- ✅ 不会立即死亡
- ✅ 3 条生命系统
- ✅ 重生后继续游戏

**如果还有问题，请截图或告诉我具体现象！**
