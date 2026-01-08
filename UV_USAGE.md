# UV 使用指南

## 🚀 运行项目

### 方式 1：使用 `env` 设置环境变量（推荐）

```bash
# 设置端口并运行
env PORT=8001 uv run python -m app.main

# 设置多个环境变量
env PORT=8001 HOST=0.0.0.0 uv run python -m app.main
```

### 方式 2：使用 shell 的变量设置

```bash
# Bash/Zsh
PORT=8001 uv run python -m app.main

# 或者先导出变量
export PORT=8001
uv run python -m app.main
```

### 方式 3：使用 `.env` 文件

在项目根目录创建 `.env` 文件：
```env
PORT=8001
HOST=0.0.0.0
GITHUB_TOKEN=your_token
```

然后直接运行：
```bash
uv run python -m app.main
```

### 方式 4：使用传统 Python 方式（不使用 UV 运行）

```bash
# 激活虚拟环境（如果使用 uv sync）
source .venv/bin/activate  # Linux/macOS
# 或
.venv\Scripts\activate  # Windows

# 然后直接运行
PORT=8001 python -m app.main
```

## 📝 常见问题

### ❌ 错误用法

```bash
# 这样会报错：Failed to spawn: `PORT=8001`
uv run PORT=8001 python -m app.main
```

### ✅ 正确用法

```bash
# 方法 1：使用 env
env PORT=8001 uv run python -m app.main

# 方法 2：shell 变量设置
PORT=8001 uv run python -m app.main

# 方法 3：使用 .env 文件
uv run python -m app.main
```

## 🔧 其他 UV 命令

### 安装依赖

```bash
# 同步依赖（推荐）
uv sync

# 或直接安装
uv pip install .
```

### 运行脚本

```bash
# 运行 Python 模块
uv run python -m app.main

# 运行 Python 脚本
uv run python script.py

# 运行命令行工具
uv run some-command
```

### 添加依赖

```bash
# 添加新依赖
uv add package-name

# 添加开发依赖
uv add --dev package-name

# 添加可选依赖组
uv add --group dev package-name
```

### 更新依赖

```bash
# 更新所有依赖
uv sync --upgrade

# 更新特定包
uv add package-name@latest
```

## 💡 提示

- `uv run` 会自动使用项目虚拟环境中的依赖
- 如果使用 `uv sync`，会创建 `.venv` 虚拟环境
- 环境变量可以通过 `.env` 文件或命令行设置
- `uv run` 不支持直接在命令前设置环境变量，需要使用 `env` 或 shell 语法
