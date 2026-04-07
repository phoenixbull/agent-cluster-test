#!/bin/bash

# Task Dashboard - 快速启动脚本
# 用法：./run.sh [dev|test|prod]

set -e

COLOR_GREEN='\033[0;32m'
COLOR_BLUE='\033[0;34m'
COLOR_YELLOW='\033[1;33m'
COLOR_RED='\033[0;31m'
COLOR_RESET='\033[0m'

print_info() {
    echo -e "${COLOR_BLUE}ℹ️  $1${COLOR_RESET}"
}

print_success() {
    echo -e "${COLOR_GREEN}✅ $1${COLOR_RESET}"
}

print_warning() {
    echo -e "${COLOR_YELLOW}⚠️  $1${COLOR_RESET}"
}

print_error() {
    echo -e "${COLOR_RED}❌ $1${COLOR_RESET}"
}

show_help() {
    echo "Task Dashboard v2.3.0 - 快速启动脚本"
    echo ""
    echo "用法：./run.sh [命令]"
    echo ""
    echo "命令:"
    echo "  dev       启动开发环境（后端 + 前端）"
    echo "  test      运行测试"
    echo "  prod      启动生产环境（Docker）"
    echo "  clean     清理临时文件"
    echo "  help      显示帮助信息"
    echo ""
}

check_python() {
    if command -v python3 &> /dev/null; then
        PYTHON_CMD=python3
    elif command -v python &> /dev/null; then
        PYTHON_CMD=python
    else
        print_error "未找到 Python，请先安装 Python 3.8+"
        exit 1
    fi
}

check_node() {
    if command -v node &> /dev/null; then
        NODE_CMD=node
    else
        print_error "未找到 Node.js，请先安装 Node.js 18+"
        exit 1
    fi
}

run_dev() {
    print_info "启动开发环境..."
    
    # 检查依赖
    check_python
    check_node
    
    # 后端
    print_info "启动后端服务..."
    cd backend
    
    if [ ! -d "venv" ]; then
        print_info "创建虚拟环境..."
        $PYTHON_CMD -m venv venv
    fi
    
    source venv/bin/activate
    pip install -q -r requirements.txt
    
    if [ ! -f ".env" ]; then
        cp .env.example .env
        print_warning "已创建 .env 文件，请根据需要修改配置"
    fi
    
    # 启动后端（后台）
    uvicorn app.main:app --reload --port 8000 &
    BACKEND_PID=$!
    
    cd ..
    
    # 前端
    print_info "启动前端服务..."
    cd frontend
    
    if [ ! -d "node_modules" ]; then
        print_info "安装前端依赖..."
        npm install
    fi
    
    npm run dev &
    FRONTEND_PID=$!
    
    cd ..
    
    print_success "开发环境已启动！"
    echo ""
    print_info "后端 API: http://localhost:8000"
    print_info "API 文档：http://localhost:8000/docs"
    print_info "前端页面：http://localhost:5173"
    echo ""
    print_info "按 Ctrl+C 停止所有服务"
    
    # 等待中断
    trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; print_info '服务已停止'; exit" INT
    wait
}

run_test() {
    print_info "运行测试..."
    
    check_python
    
    cd backend
    
    if [ ! -d "venv" ]; then
        print_info "创建虚拟环境..."
        $PYTHON_CMD -m venv venv
    fi
    
    source venv/bin/activate
    pip install -q -r requirements.txt
    
    print_info "运行后端测试..."
    pytest app/tests --cov=app --cov-report=term-missing
    
    cd ..
    
    print_info "运行前端测试..."
    cd frontend
    
    if [ ! -d "node_modules" ]; then
        npm install
    fi
    
    npm test -- --run
    
    cd ..
    
    print_success "测试完成！"
}

run_prod() {
    print_info "启动生产环境（Docker）..."
    
    if ! command -v docker &> /dev/null; then
        print_error "未找到 Docker，请先安装 Docker"
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        print_error "未找到 Docker Compose，请先安装"
        exit 1
    fi
    
    # 使用 docker compose 或 docker-compose
    if docker compose version &> /dev/null; then
        COMPOSE_CMD="docker compose"
    else
        COMPOSE_CMD="docker-compose"
    fi
    
    print_info "构建镜像..."
    $COMPOSE_CMD build
    
    print_info "启动服务..."
    $COMPOSE_CMD up -d
    
    print_success "生产环境已启动！"
    echo ""
    print_info "后端 API: http://localhost:8000"
    print_info "前端页面：http://localhost:5173"
    echo ""
    print_info "查看日志：$COMPOSE_CMD logs -f"
    print_info "停止服务：$COMPOSE_CMD down"
}

clean() {
    print_info "清理临时文件..."
    
    # 清理 Python
    rm -rf backend/venv
    rm -rf backend/__pycache__
    rm -rf backend/app/__pycache__
    rm -rf backend/app/*/__pycache__
    rm -f backend/test.db
    rm -f backend/task_dashboard.db
    
    # 清理前端
    rm -rf frontend/node_modules
    rm -rf frontend/dist
    
    # 清理 Docker
    # docker-compose down -v  # 如果需要清理数据卷
    
    print_success "清理完成！"
}

# 主逻辑
case "${1:-help}" in
    dev)
        run_dev
        ;;
    test)
        run_test
        ;;
    prod)
        run_prod
        ;;
    clean)
        clean
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        print_error "未知命令：$1"
        show_help
        exit 1
        ;;
esac
