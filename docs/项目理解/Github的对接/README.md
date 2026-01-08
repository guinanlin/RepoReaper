# GitHub 对接文档

## 目录

- [概述](#概述)
- [配置说明](#配置说明)
- [核心函数详解](#核心函数详解)
- [业务流程](#业务流程)
- [错误处理](#错误处理)
- [使用示例](#使用示例)

---

## 概述

本项目通过 **PyGithub** 库与 GitHub API 进行交互，实现以下核心功能：

1. **解析 GitHub 仓库 URL**：从各种格式的 URL 中提取 `owner/repo` 信息
2. **获取仓库目录结构**：递归获取仓库中的所有文件路径（带过滤）
3. **读取文件内容**：按需读取单个文件的完整内容
4. **智能文件选择**：结合 LLM 分析，优先读取关键文件

### 技术栈

- **PyGithub**：GitHub API 的 Python 封装库
- **GitHub API v3**：RESTful API
- **认证方式**：Personal Access Token（可选，但强烈建议）

---

## 配置说明

### 环境变量

在 `.env` 文件中配置以下变量：

```bash
# GitHub Token（可选但强烈建议配置）
# 无 Token 时每小时只能请求 60 次，有 Token 可提升至 5000 次
GITHUB_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

### 配置位置

配置文件位于：`app/core/config.py`

```python
class Settings:
    GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
    
    def validate(self):
        # GitHub Token 验证（可选）
        if not self.GITHUB_TOKEN:
            print("⚠️ 警告: 未找到 GITHUB_TOKEN，GitHub API 请求将受到每小时 60 次的严格限制。")
```

---

## 核心函数详解

### 1. `parse_repo_url(url)` - URL 解析函数

**位置**：`app/services/github_service.py:6`

**功能**：从各种格式的 GitHub URL 中提取 `owner/repo` 格式的仓库标识符。

**业务逻辑**：

```python
def parse_repo_url(url):
    """解析 GitHub URL 提取 owner/repo"""
    # 1. 移除 .git 后缀（如果存在）
    if url.endswith(".git"):
        url = url[:-4]
    
    # 2. 按 "/" 分割 URL
    parts = url.split("/")
    
    # 3. 查找 "github.com" 的位置
    if "github.com" in parts:
        index = parts.index("github.com")
        
        # 4. 提取 owner 和 repo（github.com 后的两个部分）
        if len(parts) > index + 2:
            return f"{parts[index+1]}/{parts[index+2]}"
    
    return None
```

**支持的 URL 格式**：

- `https://github.com/owner/repo`
- `https://github.com/owner/repo.git`
- `git@github.com:owner/repo.git`
- `http://github.com/owner/repo`

**返回值**：

- 成功：`"owner/repo"` 字符串
- 失败：`None`

**示例**：

```python
parse_repo_url("https://github.com/microsoft/vscode")
# 返回: "microsoft/vscode"

parse_repo_url("https://github.com/microsoft/vscode.git")
# 返回: "microsoft/vscode"
```

---

### 2. `get_repo_structure(repo_url)` - 获取目录结构

**位置**：`app/services/github_service.py:17`

**功能**：获取 GitHub 仓库的完整文件树结构，并应用过滤规则排除不需要的文件。

**业务逻辑流程**：

```
1. 解析 URL → 获取 owner/repo
2. 连接 GitHub API（使用 Token 或匿名）
3. 获取仓库对象
4. 获取默认分支的完整文件树（递归）
5. 应用过滤规则：
   - 排除非文件类型（只保留 blob）
   - 排除特定目录
   - 排除特定扩展名
6. 返回过滤后的文件路径列表
```

**详细代码逻辑**：

```python
def get_repo_structure(repo_url):
    """获取仓库文件树，包含过滤逻辑"""
    # 步骤1: 解析 URL
    repo_name = parse_repo_url(repo_url)
    if not repo_name:
        raise ValueError("Invalid GitHub URL format")
    
    # 步骤2: 连接 GitHub API
    g = Github(auth=Auth.Token(settings.GITHUB_TOKEN)) if settings.GITHUB_TOKEN else Github()
    repo = g.get_repo(repo_name)
    default_branch = repo.default_branch
    
    # 步骤3: 获取完整文件树（递归）
    contents = repo.get_git_tree(default_branch, recursive=True).tree
    
    # 步骤4: 定义过滤规则
    IGNORED_EXTS = {
        '.png', '.jpg', '.jpeg', '.gif', '.svg', '.ico', '.mp4',
        '.pyc', '.lock', '.zip', '.tar', '.gz', '.pdf',
        '.DS_Store', '.gitignore', '.gitattributes'
    }
    IGNORED_DIRS = {
        '.git', '.github', '.vscode', '.idea', '__pycache__', 
        'node_modules', 'venv', 'env', 'build', 'dist', 'site-packages',
        'migrations'
    }
    
    # 步骤5: 应用过滤
    file_list = []
    for content in contents:
        path = content.path
        
        # 只保留文件（blob），排除目录（tree）
        if content.type != "blob": 
            continue
        
        # 排除特定目录
        if any(part in IGNORED_DIRS for part in path.split("/")): 
            continue
        
        # 排除特定扩展名
        ext = os.path.splitext(path)[1]
        if ext in IGNORED_EXTS: 
            continue
        
        file_list.append(path)
    
    return file_list
```

**过滤规则说明**：

| 类型 | 规则 | 示例 |
|------|------|------|
| **扩展名过滤** | 排除二进制文件、编译文件等 | `.png`, `.pyc`, `.lock` |
| **目录过滤** | 排除依赖目录、构建目录等 | `node_modules`, `venv`, `.git` |
| **类型过滤** | 只保留文件，排除目录 | `content.type == "blob"` |

**返回值**：

- 成功：文件路径列表 `["path/to/file1.py", "path/to/file2.js", ...]`
- 失败：抛出异常

**API 调用**：

- `repo.get_git_tree(branch, recursive=True)`：获取递归文件树
- 需要 GitHub API 权限：`public_repo`（公开仓库）或 `repo`（私有仓库）

---

### 3. `get_file_content(repo_url, file_path)` - 读取文件内容

**位置**：`app/services/github_service.py:68`

**功能**：读取 GitHub 仓库中指定文件的完整内容，支持文件和目录两种类型。

**业务逻辑流程**：

```
1. 解析 URL → 获取 owner/repo
2. 连接 GitHub API
3. 获取指定路径的内容
4. 判断内容类型：
   - 如果是文件：返回解码后的 UTF-8 文本
   - 如果是目录：返回目录清单
5. 处理异常（文件不存在、权限不足等）
```

**详细代码逻辑**：

```python
def get_file_content(repo_url, file_path):
    """
    下载单个文件内容。
    支持文件和目录两种类型。
    """
    # 步骤1: 解析 URL
    repo_name = parse_repo_url(repo_url)
    if not repo_name: 
        return None
    
    try:
        # 步骤2: 连接 GitHub API
        g = Github(auth=Auth.Token(settings.GITHUB_TOKEN)) if settings.GITHUB_TOKEN else Github()
        repo = g.get_repo(repo_name)
        
        # 步骤3: 获取内容（可能返回文件或目录列表）
        content = repo.get_contents(file_path, ref=repo.default_branch)
        
        # 步骤4: 判断类型并处理
        if isinstance(content, list):
            # 情况 A: 这是一个目录
            file_names = [f.name for f in content]
            return f"Directory '{file_path}' contains:\n" + "\n".join([f"- {name}" for name in file_names])
        else:
            # 情况 B: 这是一个文件
            return content.decoded_content.decode('utf-8')
            
    except Exception as e:
        print(f"❌ [GitHub Error] 读取路径 {file_path} 失败: {e}")
        return None
```

**处理逻辑说明**：

| 输入类型 | 处理方式 | 返回值示例 |
|----------|----------|------------|
| **文件** | 解码为 UTF-8 文本 | 完整的文件内容字符串 |
| **目录** | 返回目录清单 | `"Directory 'src' contains:\n- file1.py\n- file2.js"` |
| **不存在** | 捕获异常，返回 `None` | `None` |

**API 调用**：

- `repo.get_contents(path, ref=branch)`：获取文件或目录内容
- `content.decoded_content.decode('utf-8')`：解码文件内容

**注意事项**：

- 文件大小限制：GitHub API 单个文件最大 1MB（超过会返回下载 URL）
- 编码：默认使用 UTF-8，二进制文件可能解码失败
- 性能：每次调用都是一个 HTTP 请求，建议批量读取时使用异步

---

### 4. `generate_repo_map(repo_url, file_list, limit=20)` - 生成仓库地图

**位置**：`app/services/agent_service.py:113`

**功能**：智能选择关键文件，提取类和方法签名，生成结构化的仓库地图供 LLM 分析。

**业务逻辑流程**：

```
1. 从文件列表中筛选高优先级文件：
   - 优先选择特定扩展名的文件（.py, .java, .go 等）
   - 优先选择包含关键词的文件（main, app, core, api 等）
   - 限制深度（路径层级 <= 2 或包含关键词）
2. 并发读取选中的文件内容
3. 提取代码符号（类、函数）：
   - Python: 使用 AST 解析（最准确）
   - 其他语言: 使用正则表达式
4. 生成结构化地图：
   - 关键文件 + 符号列表
   - 其他文件列表（限制数量）
```

**详细代码逻辑**：

```python
async def generate_repo_map(repo_url, file_list, limit=20):
    """生成增强版仓库地图 (多语言版)"""
    
    # 步骤1: 定义优先级规则
    priority_exts = ('.py', '.java', '.go', '.js', '.ts', '.tsx', '.cpp', '.cs')
    priority_keywords = ['main', 'app', 'core', 'api', 'service', 'utils', 'controller', 'model']
    
    # 步骤2: 筛选高优先级文件
    priority_files = [
        f for f in file_list 
        if f.endswith(priority_exts) and 
        (f.count('/') <= 2 or any(k in f.lower() for k in priority_keywords))
    ]
    
    # 步骤3: 去重并限制数量
    targets = sorted(list(set(priority_files)))[:limit]
    remaining = [f for f in file_list if f not in targets]
    
    # 步骤4: 并发处理文件
    async def process_file(path):
        # 读取文件内容
        content = await asyncio.to_thread(get_file_content, repo_url, path)
        if not content: 
            return f"{path} (Read Failed)"
        
        # 提取符号（类、函数）
        symbols = await asyncio.to_thread(_extract_symbols, content, path)
        
        if symbols:
            return f"{path}\n" + "\n".join(symbols)
        return path
    
    # 步骤5: 生成地图
    repo_map_lines = [f"--- Key Files Structure (Top {len(targets)}) ---"]
    
    tasks = [process_file(f) for f in targets]
    results = await asyncio.gather(*tasks)
    repo_map_lines.extend(results)
    
    # 步骤6: 添加其他文件列表
    if remaining:
        repo_map_lines.append("\n--- Other Files ---")
        if len(remaining) > 300:
            repo_map_lines.extend(remaining[:300])
            repo_map_lines.append(f"... ({len(remaining)-300} more files)")
        else:
            repo_map_lines.extend(remaining)
    
    return "\n".join(repo_map_lines)
```

**符号提取逻辑**：

**Python（AST 解析）**：

```python
def _extract_symbols_python(content):
    tree = ast.parse(content)
    symbols = []
    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            symbols.append(f"  [C] {node.name}")
            for sub in node.body:
                if isinstance(sub, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    if not sub.name.startswith("_") or sub.name == "__init__":
                        symbols.append(f"    - {sub.name}")
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            symbols.append(f"  [F] {node.name}")
    return symbols
```

**其他语言（正则表达式）**：

- Java: 匹配 `class X`, `public void x()`
- JavaScript/TypeScript: 匹配 `class X`, `function x()`, `const x = () =>`
- Go: 匹配 `type X struct`, `func X()`

**输出格式示例**：

```
--- Key Files Structure (Top 15) ---
app/main.py
  [F] main
  [F] lifespan
app/services/github_service.py
  [F] parse_repo_url
  [F] get_repo_structure
  [F] get_file_content
app/services/agent_service.py
  [F] agent_stream
  [F] generate_repo_map

--- Other Files ---
requirements.txt
README.md
...
```

---

## 业务流程

### 完整流程图

```
┌─────────────────┐
│  用户输入 URL   │
└────────┬────────┘
         │
         ▼
┌─────────────────────────┐
│  parse_repo_url()       │ 解析 URL → owner/repo
└────────┬────────────────┘
         │
         ▼
┌─────────────────────────┐
│  get_repo_structure()   │ 获取文件列表（过滤后）
└────────┬────────────────┘
         │
         ▼
┌─────────────────────────┐
│  generate_repo_map()    │ 生成仓库地图
│  - 选择关键文件         │
│  - 提取符号             │
└────────┬────────────────┘
         │
         ▼
┌─────────────────────────┐
│  LLM 分析（多轮）       │
│  Round 1: 选择关键文件  │
│  Round 2: 补充文件      │
│  Round 3: 完善上下文    │
└────────┬────────────────┘
         │
         ▼
┌─────────────────────────┐
│  get_file_content()     │ 读取选中文件内容
│  - 分块处理             │
│  - 存储到向量数据库     │
└────────┬────────────────┘
         │
         ▼
┌─────────────────────────┐
│  生成技术分析报告       │
└─────────────────────────┘
```

### 智能读取策略

项目采用 **多轮迭代 + LLM 决策** 的智能读取策略：

1. **第 1 轮**：
   - LLM 分析仓库地图
   - 选择 1-3 个最关键的文件（通常是入口文件、核心服务等）
   - 读取文件内容（前 50 行预览）
   - 存储到向量数据库

2. **第 2-3 轮**：
   - 基于已读取的内容，LLM 判断还需要哪些文件
   - 继续读取补充文件
   - 更新上下文摘要

3. **终止条件**：
   - 达到最大轮数（3 轮）
   - LLM 判断上下文已足够
   - 没有更多关键文件需要读取

**优势**：

- ✅ 避免读取所有文件（节省 Token 和 API 调用）
- ✅ 优先读取核心逻辑（提高理解效率）
- ✅ 动态调整读取策略（根据实际情况补充）

---

## 错误处理

### 异常类型和处理

**1. URL 解析失败**

```python
if not repo_name:
    raise ValueError("Invalid GitHub URL format")
```

**2. GitHub API 错误**

```python
except GithubException as e:
    if e.status == 401:
        raise Exception("GitHub Token 无效或过期 (401 Unauthorized)")
    elif e.status == 403:
        raise Exception("GitHub API 请求受限 (403 Rate Limit)")
    elif e.status == 404:
        raise Exception(f"找不到仓库 {repo_name} (404 Not Found)")
    else:
        raise Exception(f"GitHub API Error: {e.data.get('message', str(e))}")
```

**3. 文件读取失败**

```python
except Exception as e:
    print(f"❌ [GitHub Error] 读取路径 {file_path} 失败: {e}")
    return None  # 返回 None，不影响整体流程
```

### 常见错误场景

| 错误码 | 原因 | 解决方案 |
|--------|------|----------|
| **401** | Token 无效或过期 | 检查 `.env` 中的 `GITHUB_TOKEN` |
| **403** | 速率限制 | 添加 Token 或等待限制重置 |
| **404** | 仓库不存在或无权访问 | 检查 URL 或 Token 权限 |
| **500** | GitHub 服务器错误 | 稍后重试 |

---

## 使用示例

### 示例 1：解析 URL

```python
from app.services.github_service import parse_repo_url

url = "https://github.com/microsoft/vscode"
repo_name = parse_repo_url(url)
print(repo_name)  # 输出: "microsoft/vscode"
```

### 示例 2：获取目录结构

```python
from app.services.github_service import get_repo_structure

repo_url = "https://github.com/microsoft/vscode"
file_list = get_repo_structure(repo_url)
print(f"找到 {len(file_list)} 个文件")
# 输出: 找到 1234 个文件
```

### 示例 3：读取文件内容

```python
from app.services.github_service import get_file_content

repo_url = "https://github.com/microsoft/vscode"
content = get_file_content(repo_url, "package.json")
if content:
    print(content[:200])  # 打印前 200 个字符
```

### 示例 4：完整分析流程

```python
from app.services.agent_service import agent_stream

async def analyze_repo():
    repo_url = "https://github.com/user/repo"
    session_id = "session_123"
    
    async for event in agent_stream(repo_url, session_id, language="zh"):
        data = json.loads(event)
        print(f"[{data['step']}] {data.get('message', '')}")
```

---

## 性能优化建议

1. **使用 Token**：将 API 速率限制从 60/小时 提升到 5000/小时
2. **异步读取**：使用 `asyncio.to_thread()` 并发读取多个文件
3. **智能过滤**：提前过滤不需要的文件，减少 API 调用
4. **缓存机制**：对于相同仓库，可以缓存文件列表和内容
5. **批量处理**：尽量批量读取文件，减少网络往返

---

## 相关文件

- **核心服务**：`app/services/github_service.py`
- **业务逻辑**：`app/services/agent_service.py`
- **配置管理**：`app/core/config.py`
- **主入口**：`app/main.py`

---

## 总结

本项目通过 PyGithub 实现了完整的 GitHub 仓库读取功能：

1. ✅ **URL 解析**：支持多种 URL 格式
2. ✅ **目录结构**：递归获取并智能过滤
3. ✅ **文件内容**：按需读取，支持文件和目录
4. ✅ **智能选择**：结合 LLM 分析，优先读取关键文件
5. ✅ **错误处理**：完善的异常处理和用户提示

整个流程设计合理，既保证了功能的完整性，又兼顾了性能和用户体验。
