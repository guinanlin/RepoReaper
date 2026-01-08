# 1. 基础镜像：选择 Python 3.10 的轻量版 (Slim)
# 就像做菜先准备底料，我们使用官方提供的精简版 Linux + Python 环境
FROM python:3.10-slim

# 2. 设置环境变量
# PYTHONDONTWRITEBYTECODE=1: 防止 Python 生成 .pyc 缓存文件 (Docker 里不需要)
# PYTHONUNBUFFERED=1: 保证日志直接打印到控制台，不会被缓存 (方便调试)
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_SYSTEM_PYTHON=1

# 3. 设置工作目录
# 相当于在容器内部执行了 "mkdir /app" 和 "cd /app"
WORKDIR /app

# 4. 安装系统级依赖
# ChromaDB 有时需要编译工具，为了保险我们安装 build-essential
# curl 用于健康检查 (Healthcheck)
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 5. 安装 UV 包管理器
# UV 是一个快速的 Python 包管理器，比 pip 快很多
RUN pip install --no-cache-dir uv

# 6. 复制项目配置文件（利用 Docker 缓存层优化）
# 先只复制 pyproject.toml、.python-version 和 README.md，这样如果代码变了但依赖没变，Docker 会利用缓存
# 注意：README.md 需要在这里复制，因为 pyproject.toml 中引用了它
COPY pyproject.toml .python-version README.md ./

# 7. 使用 UV 安装依赖
# UV 会自动从 pyproject.toml 读取依赖并安装，速度比 pip 快很多
RUN uv pip install --system .

# [针对 ChromaDB 的特殊补丁]
# Linux 默认的 SQLite 版本可能过低导致 Chroma 崩溃，这里强制替换为 pysqlite3
RUN uv pip install --system pysqlite3-binary && \
    echo 'import sys; import pysqlite3; sys.modules["sqlite3"] = sys.modules.pop("pysqlite3")' > /usr/local/lib/python3.10/site-packages/google_colab_workaround.py || true

# 8. 复制项目所有代码到容器
# 将当前目录下的所有文件（app, frontend, gunicorn_conf.py 等）复制到容器的 /app 目录
COPY . .

# 9. 暴露端口
# 告诉 Docker 这个容器会占用 8000 端口
EXPOSE 8000

# 10. 启动命令
# 使用 Gunicorn 启动，加载 gunicorn_conf.py 配置，运行 app.main:app
CMD ["gunicorn", "-c", "gunicorn_conf.py", "app.main:app"]