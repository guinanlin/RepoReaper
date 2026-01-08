.PHONY: help install install-dev run run-dev stop clean docker-build docker-up docker-down docker-logs docker-restart docker-rebuild test format lint check health

# 默认变量
HOST ?= 127.0.0.1
PORT ?= 8000
PYTHON ?= python3

# 帮助信息
help: ## 显示帮助信息
	@echo "RepoReaper - Makefile 命令列表"
	@echo ""
	@echo "安装和依赖:"
	@echo "  make install       - 安装项目依赖（使用 UV）"
	@echo "  make install-dev   - 安装项目依赖（包含开发依赖）"
	@echo ""
	@echo "运行服务:"
	@echo "  make run            - 启动服务（默认端口 8000）"
	@echo "  make run-dev       - 启动开发服务器（自动重载）"
	@echo "  make stop          - 停止运行中的服务"
	@echo ""
	@echo "Docker 命令:"
	@echo "  make docker-build  - 构建 Docker 镜像"
	@echo "  make docker-up     - 启动 Docker 容器"
	@echo "  make docker-down   - 停止 Docker 容器"
	@echo "  make docker-logs   - 查看 Docker 日志"
	@echo "  make docker-restart - 重启 Docker 容器"
	@echo "  make docker-rebuild - 停止 → 重新构建 → 启动（一条命令完成）"
	@echo ""
	@echo "代码质量:"
	@echo "  make format        - 格式化代码（使用 black）"
	@echo "  make lint          - 代码检查（使用 ruff）"
	@echo "  make check         - 运行格式化和检查"
	@echo ""
	@echo "其他:"
	@echo "  make clean         - 清理临时文件和缓存"
	@echo "  make health        - 检查服务健康状态"
	@echo "  make test          - 运行测试"
	@echo ""
	@echo "环境变量:"
	@echo "  HOST=0.0.0.0 make run  - 指定主机地址"
	@echo "  PORT=8001 make run     - 指定端口"

# 安装依赖
install: ## 安装项目依赖
	@echo "📦 使用 UV 安装依赖..."
	uv sync --no-dev

install-dev: ## 安装项目依赖（包含开发依赖）
	@echo "📦 使用 UV 安装依赖（包含开发依赖）..."
	uv sync

# 运行服务
run: ## 启动服务
	@echo "🚀 启动 RepoReaper 服务..."
	@echo "   地址: http://$(HOST):$(PORT)"
	@echo "   按 Ctrl+C 停止服务"
	@env HOST=$(HOST) PORT=$(PORT) uv run python -m app.main

run-dev: ## 启动开发服务器（自动重载）
	@echo "🚀 启动 RepoReaper 开发服务器（自动重载）..."
	@echo "   地址: http://$(HOST):$(PORT)"
	@echo "   按 Ctrl+C 停止服务"
	@env HOST=$(HOST) PORT=$(PORT) uv run uvicorn app.main:app --host $(HOST) --port $(PORT) --reload

stop: ## 停止运行中的服务
	@echo "🛑 停止服务..."
	@pkill -f "python -m app.main" || pkill -f "uvicorn app.main:app" || echo "没有运行中的服务"

# Docker 命令
docker-build: ## 构建 Docker 镜像
	@echo "🐳 构建 Docker 镜像..."
	docker compose build

docker-up: ## 启动 Docker 容器
	@echo "🐳 启动 Docker 容器..."
	docker compose up -d
	@echo "✅ 服务已启动，访问: http://localhost:7000"

docker-down: ## 停止 Docker 容器
	@echo "🐳 停止 Docker 容器..."
	docker compose down

docker-logs: ## 查看 Docker 日志
	@echo "📋 查看 Docker 日志..."
	docker compose logs -f

docker-restart: ## 重启 Docker 容器
	@echo "🔄 重启 Docker 容器..."
	docker compose restart

docker-rebuild: ## 停止 → 重新构建 → 启动 Docker 容器（一条命令完成）
	@echo "🔄 开始重建 Docker 容器..."
	@echo "📋 步骤 1/3: 停止现有容器..."
	@docker compose down || true
	@echo "📋 步骤 2/3: 重新构建镜像..."
	@docker compose build
	@echo "📋 步骤 3/3: 启动容器..."
	@docker compose up -d
	@echo "✅ 重建完成！服务已启动，访问: http://localhost:7000"

# 代码质量
format: ## 格式化代码
	@echo "✨ 格式化代码..."
	@if command -v black >/dev/null 2>&1; then \
		black app/ --line-length 120; \
	else \
		uv run black app/ --line-length 120; \
	fi

lint: ## 代码检查
	@echo "🔍 代码检查..."
	@if command -v ruff >/dev/null 2>&1; then \
		ruff check app/; \
	else \
		uv run ruff check app/; \
	fi

check: format lint ## 运行格式化和检查
	@echo "✅ 代码检查和格式化完成"

# 测试
test: ## 运行测试
	@echo "🧪 运行测试..."
	@if [ -d "tests" ]; then \
		uv run pytest tests/ -v; \
	else \
		echo "⚠️  未找到 tests 目录"; \
	fi

# 清理
clean: ## 清理临时文件和缓存
	@echo "🧹 清理临时文件和缓存..."
	@find . -type d -name "__pycache__" -exec rm -r {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@find . -type f -name "*.pyo" -delete 2>/dev/null || true
	@find . -type f -name "*.pyd" -delete 2>/dev/null || true
	@find . -type d -name "*.egg-info" -exec rm -r {} + 2>/dev/null || true
	@find . -type d -name ".pytest_cache" -exec rm -r {} + 2>/dev/null || true
	@find . -type d -name ".mypy_cache" -exec rm -r {} + 2>/dev/null || true
	@find . -type d -name ".ruff_cache" -exec rm -r {} + 2>/dev/null || true
	@echo "✅ 清理完成"

# 健康检查
health: ## 检查服务健康状态
	@echo "🏥 检查服务健康状态..."
	@curl -s http://$(HOST):$(PORT)/health || echo "❌ 服务未运行或无法访问"

# 开发工具
dev-setup: install-dev ## 设置开发环境
	@echo "🛠️  开发环境设置完成"
	@echo "   已安装所有依赖（包含开发工具）"

# 快速启动（开发模式）
dev: install-dev run-dev ## 快速启动开发环境（安装依赖 + 启动服务）

# 默认目标
.DEFAULT_GOAL := help
