.PHONY: test test-cov test-ci test-specific lint clean help

# 默认运行所有测试
test:
	@echo "🧪 运行所有测试..."
	python3 -m pytest tests/ -v

# 运行测试并生成覆盖率报告
test-cov:
	@echo "📊 运行测试并生成覆盖率报告..."
	python3 -m pytest tests/ \
		--cov=utils \
		--cov=metrics_collector \
		--cov-report=html:htmlcov \
		--cov-report=term

# CI 模式 (安静，生成 XML 报告)
test-ci:
	@echo "🔄 CI 模式运行测试..."
	python3 -m pytest tests/ \
		--cov=utils \
		--cov=metrics_collector \
		--cov-report=xml:coverage.xml \
		-q

# 运行特定测试文件
test-specific:
	@echo "🎯 运行特定测试: $(TEST)"
	python3 -m pytest tests/$(TEST).py -v

# 代码风格检查
lint:
	@echo "🔍 检查代码风格..."
	python3 -m flake8 utils/ tests/ --max-line-length=120 --ignore=E501,W503

# 清理测试产物
clean:
	@echo "🧹 清理测试产物..."
	rm -rf htmlcov/
	rm -f coverage.xml
	rm -rf .pytest_cache/
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true

# 帮助
help:
	@echo "可用命令:"
	@echo "  make test           - 运行所有测试"
	@echo "  make test-cov       - 运行测试并生成覆盖率报告"
	@echo "  make test-ci        - CI 模式运行测试"
	@echo "  make test-specific  - 运行特定测试 (TEST=test_incremental)"
	@echo "  make lint           - 代码风格检查"
	@echo "  make clean          - 清理测试产物"
	@echo "  make help           - 显示帮助"
