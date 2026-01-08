# UV 安装指南

## 🚀 快速安装

### Linux / macOS

**一键安装（推荐）：**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

安装完成后，重启终端或执行：
```bash
source $HOME/.cargo/env
```

### Windows

**PowerShell：**
```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### 使用 pip 安装（所有平台通用）

```bash
pip install uv
```

### 使用 pipx 安装（推荐，隔离环境）

```bash
pip install pipx
pipx install uv
```

## ✅ 验证安装

```bash
uv --version
```

如果显示版本号，说明安装成功！

## 📦 使用 UV 安装项目依赖

安装 UV 后，在项目根目录执行：

```bash
# 安装项目依赖
uv pip install .

# 或使用虚拟环境模式
uv sync
```

## 🔧 故障排除

### 问题：命令未找到 (command not found)

**解决方案：**

1. **检查 PATH：**
   ```bash
   echo $PATH
   ```

2. **Linux/macOS：** UV 通常安装在 `$HOME/.cargo/bin` 或 `$HOME/.local/bin`
   
   添加到 PATH：
   ```bash
   # 对于 ~/.cargo/bin
   export PATH="$HOME/.cargo/bin:$PATH"
   
   # 对于 ~/.local/bin
   export PATH="$HOME/.local/bin:$PATH"
   
   # 永久添加（添加到 ~/.bashrc 或 ~/.zshrc）
   echo 'export PATH="$HOME/.cargo/bin:$PATH"' >> ~/.bashrc
   source ~/.bashrc
   ```

3. **Windows：** 检查是否添加到了系统 PATH，通常安装程序会自动添加

### 问题：权限错误

如果遇到权限问题，可以使用 `--user` 标志（pip 安装时）：
```bash
pip install --user uv
```

## 📚 更多信息

- [UV 官方文档](https://github.com/astral-sh/uv)
- [UV 安装说明](https://github.com/astral-sh/uv#installation)
