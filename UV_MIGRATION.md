# UV 迁移说明

本项目已迁移到使用 [UV](https://github.com/astral-sh/uv) 作为主要的 Python 包管理器。

## 变更内容

### 新增文件
- `pyproject.toml` - 项目配置和依赖定义（符合 PEP 621 标准）
- `.python-version` - 指定 Python 版本为 3.10
- `UV_MIGRATION.md` - 本迁移说明文档

### 更新的文件
- `Dockerfile` - 使用 UV 替代 pip 安装依赖
- `README.md` - 更新安装说明，优先推荐使用 UV
- `README_zh.md` - 更新中文安装说明
- `.gitignore` - 添加 UV 相关文件忽略规则

### 保留的文件
- `requirements.txt` - 保留以支持传统 pip 安装方式（向后兼容）

## 使用方法

### 使用 UV（推荐）

```bash
# 安装 UV
curl -LsSf https://astral.sh/uv/install.sh | sh
# 或使用 pip: pip install uv

# 安装项目依赖
uv pip install .

# 或使用虚拟环境模式
uv sync
```

### 使用 pip（传统方式）

```bash
pip install -r requirements.txt
```

## Docker 构建

Dockerfile 已更新为使用 UV，构建速度会显著提升。构建命令保持不变：

```bash
docker build -t reporeaper .
docker-compose up -d
```

## 优势

1. **更快的安装速度** - UV 使用 Rust 编写，比 pip 快 10-100 倍
2. **更好的依赖解析** - 更智能的依赖冲突检测和解决
3. **现代化标准** - 使用 pyproject.toml 符合 Python 包管理最佳实践
4. **向后兼容** - 仍支持传统的 requirements.txt 方式

## 注意事项

- Python 版本要求从 3.9+ 提升到 3.10+（与 pyproject.toml 中的配置一致）
- 如果遇到问题，可以回退到使用 `pip install -r requirements.txt`
