    def get_login_page(self):
        return """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>登录 - Agent 集群 V2.1</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .login-container {
            background: white;
            border-radius: 16px;
            padding: 40px;
            width: 100%;
            max-width: 400px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
        }
        .logo { text-align: center; margin-bottom: 30px; }
        .logo h1 { font-size: 28px; color: #333; margin-bottom: 10px; }
        .logo p { color: #666; font-size: 14px; }
        .logo .version { background: linear-gradient(135deg, #667eea, #764ba2); color: white; padding: 4px 12px; border-radius: 20px; font-size: 12px; display: inline-block; margin-top: 8px; }
        .form-group { margin-bottom: 20px; }
        .form-group label { display: block; margin-bottom: 8px; color: #555; font-weight: 500; }
        .form-group input { width: 100%; padding: 12px 16px; border: 2px solid #e0e0e0; border-radius: 8px; font-size: 14px; transition: border-color 0.3s; }
        .form-group input:focus { outline: none; border-color: #667eea; }
        .btn { width: 100%; padding: 14px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; border: none; border-radius: 8px; font-size: 16px; font-weight: 600; cursor: pointer; transition: transform 0.2s, box-shadow 0.2s; }
        .btn:hover { transform: translateY(-2px); box-shadow: 0 8px 20px rgba(102, 126, 234, 0.4); }
        .btn:disabled { opacity: 0.6; cursor: not-allowed; transform: none; }
        .error-message { background: #fee; color: #c33; padding: 12px; border-radius: 8px; margin-bottom: 20px; font-size: 14px; display: none; }
        .footer { text-align: center; margin-top: 20px; color: #999; font-size: 12px; }
        .features { margin-top: 20px; padding: 15px; background: #f8f9fa; border-radius: 8px; }
        .features h4 { color: #666; font-size: 14px; margin-bottom: 10px; }
        .features ul { list-style: none; }
        .features li { color: #888; font-size: 12px; padding: 4px 0; }
        .features li:before { content: "✅ "; }
    </style>
</head>
<body>
    <div class="login-container">
        <div class="logo">
            <h1>🤖 Agent 集群</h1>
            <p>智能协作开发系统</p>
            <span class="version">V2.1</span>
        </div>
        <div class="error-message" id="errorMessage"></div>
        <form id="loginForm">
            <div class="form-group">
                <label for="username">用户名</label>
                <input type="text" id="username" name="username" placeholder="请输入用户名" autocomplete="username" required>
            </div>
            <div class="form-group">
                <label for="password">密码</label>
                <input type="password" id="password" name="password" placeholder="请输入密码" autocomplete="current-password" required>
            </div>
            <button type="submit" class="btn" id="submitBtn">登录</button>
        </form>
        <div class="features">
            <h4>📊 系统特性</h4>
            <ul>
                <li>完整 6 阶段开发流程</li>
                <li>10 个专业 Agent 协作</li>
                <li>质量门禁自动审查</li>
                <li>钉钉双向通知</li>
            </ul>
        </div>
        <div class="footer">Agent Cluster Console v2.1</div>
    </div>
    <script>
        document.getElementById('loginForm').addEventListener('submit', async function(e) {
            e.preventDefault();
            const btn = document.getElementById('submitBtn');
            const errorDiv = document.getElementById('errorMessage');
            const username = document.getElementById('username').value;
            const password = document.getElementById('password').value;
            btn.disabled = true;
            btn.textContent = '登录中...';
            errorDiv.style.display = 'none';
            try {
                const res = await fetch('/api/login', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ username, password })
                });
                const data = await res.json();
                if (data.success) {
                    document.cookie = `auth_token=${data.token}; Path=/; Max-Age=${24*60*60}; SameSite=Strict`;
                    window.location.href = '/';
                } else {
                    errorDiv.textContent = data.error || '登录失败';
                    errorDiv.style.display = 'block';
                    btn.disabled = false;
                    btn.textContent = '登录';
                }
            } catch (err) {
                errorDiv.textContent = '网络错误，请稍后重试';
                errorDiv.style.display = 'block';
                btn.disabled = false;
                btn.textContent = '登录';
            }
        });
    </script>
</body>
</html>
"""

    def get_main_page(self):
        return """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Agent 集群 V2.1 控制台</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f5f7fa; }
        .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px 40px; }
        .header-top { display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px; }
        .header h1 { font-size: 24px; }
        .header .version { background: rgba(255,255,255,0.2); padding: 4px 12px; border-radius: 20px; font-size: 12px; }
        .nav { display: flex; gap: 15px; flex-wrap: wrap; }
        .nav a { color: rgba(255,255,255,0.9); text-decoration: none; padding: 8px 16px; border-radius: 6px; transition: background 0.3s; font-size: 14px; }
        .nav a:hover { background: rgba(255,255,255,0.2); }
        .container { max-width: 1600px; margin: 0 auto; padding: 30px; }
        .status-bar { background: white; border-radius: 12px; padding: 20px; margin-bottom: 30px; display: flex; gap: 30px; align-items: center; box-shadow: 0 2px 8px rgba(0,0,0,0.08); }
        .status-item { display: flex; align-items: center; gap: 10px; }
        .status-dot { width: 12px; height: 12px; border-radius: 50%; }
        .status-dot.green { background: #10b981; }
        .status-dot.red { background: #ef4444; }
        .status-dot.yellow { background: #f59e0b; }
        .status-label { color: #666; font-size: 14px; }
        .status-value { font-weight: 600; color: #333; }
        .status-cards { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-bottom: 30px; }
        .card { background: white; border-radius: 12px; padding: 24px; box-shadow: 0 2px 8px rgba(0,0,0,0.08); transition: transform 0.2s; }
        .card:hover { transform: translateY(-4px); }
        .card h3 { color: #666; font-size: 14px; margin-bottom: 10px; }
        .card .value { font-size: 32px; font-weight: bold; color: #333; }
        .card .sub { font-size: 12px; color: #999; margin-top: 8px; }
        .card .icon { font-size: 24px; margin-bottom: 10px; }
        .section { background: white; border-radius: 12px; padding: 24px; margin-bottom: 30px; box-shadow: 0 2px 8px rgba(0,0,0,0.08); }
        .section h2 { margin-bottom: 20px; color: #333; font-size: 18px; }
        .phase-timeline { display: flex; gap: 10px; overflow-x: auto; padding-bottom: 10px; }
        .phase-card { min-width: 200px; background: #f8f9fa; border-radius: 12px; padding: 20px; border-left: 4px solid #667eea; }
        .phase-card h4 { color: #333; margin-bottom: 8px; font-size: 16px; }
        .phase-card p { color: #666; font-size: 13px; margin-bottom: 10px; }
        .phase-card .agents { display: flex; flex-wrap: wrap; gap: 5px; }
        .phase-card .agent-tag { background: #e0e7ff; color: #4f46e5; padding: 3px 8px; border-radius: 4px; font-size: 11px; }
        .phase-card .quality-gate { background: #fef3c7; color: #d97706; padding: 3px 8px; border-radius: 4px; font-size: 11px; margin-top: 8px; display: inline-block; }
        .submit-form { background: linear-gradient(135deg, #f8f9fa, #e9ecef); border-radius: 12px; padding: 30px; margin-bottom: 30px; }
        .submit-form h2 { margin-bottom: 20px; color: #333; }
        .form-group { margin-bottom: 20px; }
        .form-group label { display: block; margin-bottom: 8px; color: #555; font-weight: 500; }
        .form-group textarea { width: 100%; padding: 12px; border: 1px solid #ddd; border-radius: 8px; font-size: 14px; resize: vertical; min-height: 120px; font-family: inherit; }
        .form-group textarea:focus { outline: none; border-color: #667eea; }
        .form-group select { width: 100%; padding: 12px; border: 1px solid #ddd; border-radius: 8px; font-size: 14px; }
        .btn { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; border: none; padding: 12px 30px; border-radius: 8px; font-size: 16px; cursor: pointer; transition: transform 0.2s; }
        .btn:hover { transform: translateY(-2px); }
        .agent-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 15px; }
        .agent-card { background: #f8f9fa; border-radius: 10px; padding: 16px; display: flex; align-items: center; gap: 15px; }
        .agent-avatar { width: 48px; height: 48px; border-radius: 8px; background: linear-gradient(135deg, #667eea, #764ba2); display: flex; align-items: center; justify-content: center; color: white; font-size: 20px; }
        .agent-info { flex: 1; }
        .agent-info h4 { color: #333; font-size: 14px; margin-bottom: 4px; }
        .agent-info p { color: #666; font-size: 12px; }
        .agent-info .model { color: #999; font-size: 11px; margin-top: 4px; }
        .status-badge { padding: 4px 10px; border-radius: 20px; font-size: 11px; font-weight: 500; }
        .status-badge.ready { background: #d1fae5; color: #065f46; }
        .status-badge.busy { background: #fef3c7; color: #92400e; }
        .workflow-list { max-height: 400px; overflow-y: auto; }
        .workflow-item { padding: 15px; border-bottom: 1px solid #eee; display: flex; justify-content: space-between; align-items: center; }
        .workflow-item:last-child { border-bottom: none; }
        .workflow-item .info { flex: 1; }
        .workflow-item .title { font-weight: 500; color: #333; font-size: 14px; }
        .workflow-item .meta { font-size: 12px; color: #999; margin-top: 5px; }
        .workflow-item .status-badge { padding: 4px 12px; border-radius: 20px; font-size: 12px; }
        .status-badge.completed { background: #d1fae5; color: #065f46; }
        .status-badge.running { background: #dbeafe; color: #1e40af; }
        .status-badge.failed { background: #fee2e2; color: #991b1b; }
        .quick-actions { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 15px; margin-top: 20px; }
        .quick-action { background: white; border: 2px solid #e0e0e0; border-radius: 10px; padding: 16px; text-align: center; cursor: pointer; transition: all 0.2s; text-decoration: none; color: #333; }
        .quick-action:hover { border-color: #667eea; background: #f0f4ff; }
        .quick-action .icon { font-size: 28px; margin-bottom: 8px; }
        .quick-action .label { font-size: 13px; font-weight: 500; }
    </style>
</head>
<body>
    <div class="header">
        <div class="header-top">
            <h1>🤖 Agent 集群控制台</h1>
            <span class="version">V2.1</span>
        </div>
        <div class="nav">
            <a href="/">📊 概览</a>
            <a href="/phases">🔄 开发流程</a>
            <a href="/agents">🤖 Agent 阵容</a>
            <a href="/workflows">📋 工作流</a>
            <a href="/quality">🚦 质量门禁</a>
            <a href="/templates">📝 模板库</a>
            <a href="/costs">💰 成本统计</a>
            <a href="/settings" style="margin-left:auto;">⚙️ 设置</a>
            <a href="#" onclick="logout(); return false;">🚪 登出</a>
        </div>
    </div>
    
    <div class="container">
        <div class="status-bar">
            <div class="status-item">
                <span class="status-dot green" id="clusterStatusDot"></span>
                <span class="status-label">集群状态:</span>
                <span class="status-value" id="clusterStatus">-</span>
            </div>
            <div class="status-item">
                <span class="status-dot green" id="deployStatusDot"></span>
                <span class="status-label">部署监听:</span>
                <span class="status-value" id="deployStatus">-</span>
            </div>
            <div class="status-item">
                <span class="status-dot green" id="dingtalkStatusDot"></span>
                <span class="status-label">钉钉通知:</span>
                <span class="status-value" id="dingtalkStatus">-</span>
            </div>
            <div class="status-item" style="margin-left:auto; color:#999; font-size:13px;" id="lastUpdate"></div>
        </div>
        
        <div class="status-cards">
            <div class="card">
                <div class="icon">🔄</div>
                <h3>进行中的工作流</h3>
                <div class="value" id="activeWorkflows">-</div>
                <div class="sub">当前正在执行</div>
            </div>
            <div class="card">
                <div class="icon">✅</div>
                <h3>今日完成</h3>
                <div class="value" id="completedToday">-</div>
                <div class="sub">成功完成的工作流</div>
            </div>
            <div class="card">
                <div class="icon">❌</div>
                <h3>今日失败</h3>
                <div class="value" id="failedToday">-</div>
                <div class="sub">需要关注</div>
            </div>
            <div class="card">
                <div class="icon">🤖</div>
                <h3>就绪 Agent</h3>
                <div class="value" id="agentsReady">-</div>
                <div class="sub">共 10 个 Agent</div>
            </div>
        </div>
        
        <div class="submit-form">
            <h2>🚀 提交新任务</h2>
            <div class="form-group">
                <label>产品需求描述</label>
                <textarea id="requirement" placeholder="详细描述你想要实现的功能，例如：创建一个电商网站的购物车功能，支持添加商品、修改数量、删除商品、结算等功能..."></textarea>
            </div>
            <div class="form-group">
                <label>选择项目</label>
                <select id="project">
                    <option value="default">默认项目</option>
                    <option value="ecommerce">电商项目</option>
                    <option value="blog">博客系统</option>
                    <option value="crm">CRM 系统</option>
                    <option value="saas">SaaS 平台</option>
                </select>
            </div>
            <button class="btn" onclick="submitTask()">🚀 启动工作流</button>
        </div>
        
        <div class="section">
            <h2>🔄 完整开发流程（6 阶段）</h2>
            <div class="phase-timeline" id="phaseTimeline">
                <div class="phase-card">
                    <h4>Phase 1: 需求分析</h4>
                    <p>Product Manager</p>
                    <div class="agents">
                        <span class="agent-tag">PRD 文档</span>
                        <span class="agent-tag">用户故事</span>
                    </div>
                </div>
                <div class="phase-card">
                    <h4>Phase 2: 技术设计</h4>
                    <p>Tech Lead + Designer + DevOps</p>
                    <div class="agents">
                        <span class="agent-tag">架构设计</span>
                        <span class="agent-tag">UI 设计</span>
                        <span class="agent-tag">部署配置</span>
                    </div>
                </div>
                <div class="phase-card">
                    <h4>Phase 3: 开发实现</h4>
                    <p>Codex + Claude-Code</p>
                    <div class="agents">
                        <span class="agent-tag">后端代码</span>
                        <span class="agent-tag">前端代码</span>
                    </div>
                </div>
                <div class="phase-card">
                    <h4>Phase 4: 测试验证</h4>
                    <p>Tester</p>
                    <div class="agents">
                        <span class="agent-tag">单元测试</span>
                        <span class="agent-tag">集成测试</span>
                    </div>
                    <span class="quality-gate">🚦 质量门禁</span>
                </div>
                <div class="phase-card">
                    <h4>Phase 5: 代码审查</h4>
                    <p>3 Reviewers</p>
                    <div class="agents">
                        <span class="agent-tag">逻辑审查</span>
                        <span class="agent-tag">安全审查</span>
                    </div>
                    <span class="quality-gate">🚦 质量门禁</span>
                </div>
                <div class="phase-card">
                    <h4>Phase 6: 部署上线</h4>
                    <p>DevOps</p>
                    <div class="agents">
                        <span class="agent-tag">Docker</span>
                        <span class="agent-tag">CI/CD</span>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="section">
            <h2>🤖 Agent 阵容（10 个）</h2>
            <div class="agent-grid" id="agentGrid">
                <div style="color:#999;text-align:center;padding:40px;grid-column:1/-1;">加载中...</div>
            </div>
        </div>
        
        <div class="section">
            <h2>📋 最近工作流</h2>
            <div class="workflow-list" id="workflowList">
                <div style="color:#999;text-align:center;padding:40px;">加载中...</div>
            </div>
            <div style="text-align:center;margin-top:20px;">
                <a href="/workflows" style="color:#667eea;text-decoration:none;">查看全部 →</a>
            </div>
        </div>
        
        <div class="section">
            <h2>⚡ 快捷操作</h2>
            <div class="quick-actions">
                <a href="/phases" class="quick-action">
                    <div class="icon">🔄</div>
                    <div class="label">查看流程</div>
                </a>
                <a href="/agents" class="quick-action">
                    <div class="icon">🤖</div>
                    <div class="label">Agent 状态</div>
                </a>
                <a href="/quality" class="quick-action">
                    <div class="icon">🚦</div>
                    <div class="label">质量门禁</div>
                </a>
                <a href="/templates" class="quick-action">
                    <div class="icon">📝</div>
                    <div class="label">模板库</div>
                </a>
                <a href="/costs" class="quick-action">
                    <div class="icon">💰</div>
                    <div class="label">成本统计</div>
                </a>
            </div>
        </div>
    </div>
    
    <script>
        async function loadStatus() {
            try {
                const res = await fetch('/api/status');
                const data = await res.json();
                
                document.getElementById('clusterStatus').textContent = data.status === 'running' ? '运行中' : '已停止';
                document.getElementById('clusterStatusDot').className = 'status-dot ' + (data.status === 'running' ? 'green' : 'red');
                
                document.getElementById('deployStatus').textContent = data.deploy_listener === 'running' ? '监听中' : '已停止';
                document.getElementById('deployStatusDot').className = 'status-dot ' + (data.deploy_listener === 'running' ? 'green' : 'yellow');
                
                document.getElementById('dingtalkStatus').textContent = data.dingtalk_enabled ? '已启用' : '未配置';
                document.getElementById('dingtalkStatusDot').className = 'status-dot ' + (data.dingtalk_enabled ? 'green' : 'yellow');
                
                document.getElementById('activeWorkflows').textContent = data.active_workflows;
                document.getElementById('completedToday').textContent = data.completed_today;
                document.getElementById('failedToday').textContent = data.failed_today;
                document.getElementById('agentsReady').textContent = data.agents_ready;
                document.getElementById('lastUpdate').textContent = '最后更新：' + new Date(data.timestamp).toLocaleString('zh-CN');
            } catch (e) {
                console.error('加载状态失败:', e);
            }
        }
        
        async function loadAgents() {
            try {
                const res = await fetch('/api/agents');
                const data = await res.json();
                const grid = document.getElementById('agentGrid');
                
                const allAgents = [...data.executors, ...data.reviewers];
                grid.innerHTML = allAgents.map(agent => {
                    const avatar = agent.name.split(' ').map(w => w[0]).join('').substring(0, 2);
                    return `
                        <div class="agent-card">
                            <div class="agent-avatar">${avatar}</div>
                            <div class="agent-info" style="flex:1;">
                                <h4>${agent.name}</h4>
                                <p>${agent.role} · ${agent.phase}</p>
                                <div class="model">${agent.model}</div>
                            </div>
                            <span class="status-badge ready">就绪</span>
                        </div>
                    `;
                }).join('');
            } catch (e) {
                console.error('加载 Agent 失败:', e);
            }
        }
        
        async function loadWorkflows() {
            try {
                const res = await fetch('/api/workflows');
                const data = await res.json();
                const list = document.getElementById('workflowList');
                
                if (data.workflows.length === 0) {
                    list.innerHTML = '<div style="color:#999;text-align:center;padding:40px;">暂无工作流记录</div>';
                    return;
                }
                
                list.innerHTML = data.workflows.slice(0, 10).map(wf => {
                    const statusClass = wf.status === 'completed' ? 'completed' : wf.status === 'failed' ? 'failed' : 'running';
                    const statusText = wf.status === 'completed' ? '✅ 完成' : wf.status === 'failed' ? '❌ 失败' : '🔄 进行中';
                    return `
                        <div class="workflow-item">
                            <div class="info">
                                <div class="title">${wf.requirement || '未命名任务'}</div>
                                <div class="meta">${wf.workflow_id || '-'} · ${wf.project || '默认项目'} · ${new Date(wf.created_at).toLocaleString('zh-CN')}</div>
                            </div>
                            <span class="status-badge ${statusClass}">${statusText}</span>
                        </div>
                    `;
                }).join('');
            } catch (e) {
                console.error('加载工作流失败:', e);
            }
        }
        
        async function submitTask() {
            const requirement = document.getElementById('requirement').value.trim();
            const project = document.getElementById('project').value;
            
            if (!requirement) {
                alert('请输入产品需求');
                return;
            }
            
            if (!confirm('确定要启动工作流吗？\\n\\n这将启动完整的 6 阶段开发流程，预计需要 10-30 分钟。')) {
                return;
            }
            
            try {
                const res = await fetch('/api/submit', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ requirement, project })
                });
                const data = await res.json();
                
                if (data.success) {
                    alert('✅ ' + data.message);
                    document.getElementById('requirement').value = '';
                    loadStatus();
                    loadWorkflows();
                } else {
                    alert('❌ ' + data.error);
                }
            } catch (e) {
                alert('提交失败：' + e.message);
            }
        }
        
        async function logout() {
            if (!confirm('确定要登出吗？')) return;
            try {
                await fetch('/api/logout', { method: 'POST' });
                document.cookie = 'auth_token=; Path=/; Max-Age=0';
                window.location.href = '/login';
            } catch (err) {
                alert('登出失败：' + err.message);
            }
        }
        
        loadStatus();
        loadAgents();
        loadWorkflows();
        setInterval(loadStatus, 30000);
    </script>
</body>
</html>
"""
