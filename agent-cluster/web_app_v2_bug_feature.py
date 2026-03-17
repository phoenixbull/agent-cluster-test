    def get_bugs_page(self):
        return """<!DOCTYPE html><html lang="zh-CN"><head><meta charset="UTF-8"><title>Bug 管理 - Agent 集群 V2.1</title>
<style>*{margin:0;padding:0;box-sizing:border-box}body{font-family:-apple-system,BlinkMacSystemFont,sans-serif;background:#f5f7fa}.header{background:linear-gradient(135deg,#667eea,#764ba2);color:white;padding:20px 40px}.nav{display:flex;gap:15px;margin-top:15px}.nav a{color:rgba(255,255,255,0.9);text-decoration:none;padding:8px 16px;border-radius:6px}.container{max-width:1400px;margin:0 auto;padding:30px}.grid{display:grid;grid-template-columns:1fr 2fr;gap:30px}.card{background:white;border-radius:12px;padding:24px;box-shadow:0 2px 8px rgba(0,0,0,0.08)}.card h2{margin-bottom:20px;color:#333}.form-group{margin-bottom:15px}.form-group label{display:block;margin-bottom:5px;color:#555;font-weight:500}.form-group input,.form-group textarea,.form-group select{width:100%;padding:10px;border:1px solid #ddd;border-radius:6px;font-family:inherit}.form-group textarea{min-height:120px;resize:vertical}.btn{background:linear-gradient(135deg,#667eea,#764ba2);color:white;border:none;padding:12px 24px;border-radius:8px;cursor:pointer;font-size:14px}.btn:hover{transform:translateY(-2px)}.btn-danger{background:#f44336}.table-container{overflow-x:auto}table{width:100%;border-collapse:collapse}th,td{padding:12px;text-align:left;border-bottom:1px solid #eee}th{background:#f8f9fa;color:#666;font-weight:500;font-size:14px}.status-badge{padding:4px 10px;border-radius:20px;font-size:12px}.status-badge.new{background:#dbeafe;color:#1e40af}.status-badge.fixing{background:#fef3c7;color:#92400e}.status-badge.fixed{background:#d1fae5;color:#065f46}.priority-badge{padding:4px 8px;border-radius:4px;font-size:11px}.priority-high{background:#fee2e2;color:#991b1b}.priority-medium{background:#fef3c7;color:#92400e}.priority-low{background:#e0e7ff;color:#4f46e5}.info-box{background:#f0f9ff;border:1px solid #bae6fd;border-radius:8px;padding:15px;margin-bottom:20px}.info-box p{color:#0369a1;font-size:14px}</style></head><body>
<div class="header"><h1>🐛 Bug 管理</h1><div class="nav"><a href="/">📊 概览</a><a href="/workflows">📋 工作流</a><a href="/agents">🤖 Agent</a><a href="/phases">🔄 流程</a><a href="/quality">🚦 质量门禁</a><a href="/bugs" style="background:rgba(255,255,255,0.2);">🐛 Bug 管理</a><a href="/templates">📝 模板</a><a href="/costs">💰 成本</a><a href="/settings" style="margin-left:auto;">⚙️ 设置</a><a href="#" onclick="logout()">🚪 登出</a></div></div>
<div class="container"><div class="grid"><div class="card"><h2>📝 提交 Bug</h2><div class="info-box"><p>💡 提交 Bug 后，Agent 集群将自动启动完整修复流程：分析→修复→测试→审查→PR</p></div>
<form id="bugForm"><div class="form-group"><label>Bug 标题</label><input type="text" id="title" placeholder="简短描述 Bug" required></div>
<div class="form-group"><label>优先级</label><select id="priority"><option value="high">🔴 高 - 严重影响功能</option><option value="medium" selected>🟡 中 - 部分影响</option><option value="low">🟢 低 - 轻微问题</option></select></div>
<div class="form-group"><label>Bug 描述</label><textarea id="description" placeholder="详细描述 Bug 现象、复现步骤、预期行为..." required></textarea></div>
<div class="form-group"><label>相关文件/路径</label><input type="text" id="files" placeholder="例如：src/api/user.py, tests/test_user.py"></div>
<div class="form-group"><label>关联项目</label><select id="project"><option value="default">默认项目</option><option value="ecommerce">电商项目</option><option value="blog">博客系统</option><option value="crm">CRM 系统</option></select></div>
<button type="submit" class="btn">🚀 提交并启动修复流程</button></form></div>
<div class="card"><h2>📊 Bug 统计</h2><div style="display:grid;grid-template-columns:repeat(2,1fr);gap:15px;margin-top:20px"><div style="background:#dbeafe;border-radius:8px;padding:15px;text-align:center"><div style="font-size:24px;font-weight:bold;color:#1e40af" id="newCount">0</div><div style="color:#666;font-size:13px">待处理</div></div><div style="background:#fef3c7;border-radius:8px;padding:15px;text-align:center"><div style="font-size:24px;font-weight:bold;color:#92400e" id="fixingCount">0</div><div style="color:#666;font-size:13px">修复中</div></div><div style="background:#d1fae5;border-radius:8px;padding:15px;text-align:center"><div style="font-size:24px;font-weight:bold;color:#065f46" id="fixedCount">0</div><div style="color:#666;font-size:13px">已修复</div></div><div style="background:#f3e8ff;border-radius:8px;padding:15px;text-align:center"><div style="font-size:24px;font-weight:bold;color:#7e22ce" id="totalToday">0</div><div style="color:#666;font-size:13px">今日提交</div></div></div></div></div>
<div class="card"><h2>📋 Bug 列表</h2><div class="table-container"><table><thead><tr><th>ID</th><th>标题</th><th>优先级</th><th>状态</th><th>项目</th><th>提交时间</th><th>操作</th></tr></thead><tbody id="bugTable"><tr><td colspan="7" style="text-align:center;color:#999;">加载中...</td></tr></tbody></table></div></div></div></div>
<script>async function loadBugs(){try{const res=await fetch('/api/bugs');const d=await res.json();const tbody=document.getElementById('bugTable');if(!d.bugs||d.bugs.length===0){tbody.innerHTML='<tr><td colspan="7" style="text-align:center;color:#999;">暂无 Bug 记录</td></tr>';return;}tbody.innerHTML=d.bugs.map(b=>`<tr><td>#${b.id||'-'}</td><td>${b.title||'未命名'}</td><td><span class="priority-badge priority-${b.priority||'medium'}">${b.priority==='high'?'🔴 高':b.priority==='medium'?'🟡 中':'🟢 低'}</span></td><td><span class="status-badge ${b.status||'new'}">${b.status==='new'?'🆕 待处理':b.status==='fixing'?'🔧 修复中':'✅ 已修复'}</span></td><td>${b.project||'-'}</td><td>${new Date(b.created_at).toLocaleString('zh-CN')}</td><td><button class="btn" style="padding:6px 12px;font-size:12px;" onclick="viewBug('${b.id}')">查看</button></td></tr>`).join('');const stats={new:d.bugs.filter(b=>b.status==='new').length,fixing:d.bugs.filter(b=>b.status==='fixing').length,fixed:d.bugs.filter(b=>b.status==='fixed').length,today:d.bugs.filter(b=>new Date(b.created_at).toDateString()===new Date().toDateString()).length};document.getElementById('newCount').textContent=stats.new;document.getElementById('fixingCount').textContent=stats.fixing;document.getElementById('fixedCount').textContent=stats.fixed;document.getElementById('totalToday').textContent=stats.today;}catch(e){console.error('加载失败:',e);}}
document.getElementById('bugForm').addEventListener('submit',async function(e){e.preventDefault();const title=document.getElementById('title').value;const priority=document.getElementById('priority').value;const description=document.getElementById('description').value;const files=document.getElementById('files').value;const project=document.getElementById('project').value;if(!title||!description){alert('请填写标题和描述');return;}if(!confirm('确定提交 Bug 并启动自动修复流程吗？\\n\\nAgent 集群将执行：\\n1️⃣ 分析 Bug 原因\\n2️⃣ 修复代码\\n3️⃣ 运行测试\\n4️⃣ 代码审查\\n5️⃣ 创建 PR'))return;try{const res=await fetch('/api/bugs/submit',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({title,priority,description,files,project})});const d=await res.json();if(d.success){alert('✅ '+d.message+'\\n\\n工作流 ID: '+(d.workflow_id||'-'));document.getElementById('title').value='';document.getElementById('description').value='';document.getElementById('files').value='';loadBugs();}else{alert('❌ '+d.error);}}catch(e){alert('提交失败：'+e.message);}});
function viewBug(id){alert('查看 Bug #'+id+'\\n\\n此功能可展示 Bug 详情、修复进度、相关 PR 链接等');}
async function logout(){if(!confirm('确定登出？'))return;await fetch('/api/logout',{method:'POST'});document.cookie='auth_token=;Path=/;Max-Age=0';window.location.href='/login';}
loadBugs();setInterval(loadBugs,30000);</script></body></html>"""

    def submit_bug(self, data):
        """提交 Bug 并触发修复流程"""
        title = data.get("title", "")
        priority = data.get("priority", "medium")
        description = data.get("description", "")
        files = data.get("files", "")
        project = data.get("project", "default")
        
        if not title or not description:
            return {"success": False, "error": "标题和描述不能为空"}
        
        # 生成 Bug ID
        import random
        bug_id = f"BUG{random.randint(1000, 9999)}"
        
        # 保存 Bug 记录
        bugs_file = MEMORY_DIR / "bugs.json"
        bugs = []
        if bugs_file.exists():
            try:
                with open(bugs_file, 'r', encoding='utf-8') as f:
                    bugs = json.load(f)
            except:
                pass
        
        bug_record = {
            "id": bug_id,
            "title": title,
            "priority": priority,
            "description": description,
            "files": files,
            "project": project,
            "status": "new",
            "created_at": datetime.now().isoformat(),
            "workflow_id": None,
            "pr_url": None
        }
        bugs.append(bug_record)
        
        with open(bugs_file, 'w', encoding='utf-8') as f:
            json.dump(bugs, f, ensure_ascii=False, indent=2)
        
        # 构建修复需求
        requirement = f"""🐛 Bug 修复任务

**Bug ID**: {bug_id}
**标题**: {title}
**优先级**: {priority}

**问题描述**:
{description}

**相关文件**: {files if files else '待分析'}

**修复要求**:
1. 分析 Bug 根本原因
2. 修复相关代码
3. 编写/更新单元测试
4. 确保测试覆盖率 > 80%
5. 通过所有质量门禁
6. 创建 Pull Request

**完整流程**:
Phase 1: 分析 Bug 原因
Phase 2: 设计修复方案
Phase 3: 实现修复代码
Phase 4: 测试验证
Phase 5: 代码审查
Phase 6: 部署并创建 PR
"""
        
        # 触发修复工作流
        try:
            cmd = f"cd {BASE_DIR} && python3 orchestrator.py \"{requirement}\""
            subprocess.Popen(cmd, shell=True, stdout=open(LOGS_DIR / f"bug_{bug_id}.log", 'a'), stderr=subprocess.STDOUT)
            
            # 更新 Bug 状态
            bug_record["status"] = "fixing"
            bug_record["workflow_id"] = f"wf_{bug_id}"
            
            with open(bugs_file, 'w', encoding='utf-8') as f:
                json.dump(bugs, f, ensure_ascii=False, indent=2)
            
            return {
                "success": True,
                "message": "Bug 已提交，Agent 集群正在修复中",
                "bug_id": bug_id,
                "workflow_id": bug_record["workflow_id"]
            }
        except Exception as e:
            return {"success": False, "error": f"提交成功但启动修复失败：{str(e)}"}
    
    def get_bugs(self):
        """获取 Bug 列表"""
        bugs_file = MEMORY_DIR / "bugs.json"
        if bugs_file.exists():
            try:
                with open(bugs_file, 'r', encoding='utf-8') as f:
                    bugs = json.load(f)
                bugs.sort(key=lambda x: x.get("created_at", ""), reverse=True)
                return {"bugs": bugs[-50:]}
            except:
                pass
        return {"bugs": []}
