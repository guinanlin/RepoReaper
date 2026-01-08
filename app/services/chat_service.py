# 文件路径: app/services/chat_service.py
import json
import asyncio
import re
from app.core.config import settings
from app.utils.llm_client import client, create_llm_client
from app.services.vector_service import store_manager
from app.services.github_service import get_file_content
from app.services.chunking_service import UniversalChunker

chunker = UniversalChunker(min_chunk_size=100)

# === 新增：简单的中文检测 ===
def is_chinese_query(text: str) -> bool:
    """检测字符串中是否包含中文字符"""
    for char in text:
        if '\u4e00' <= char <= '\u9fff':
            return True
    return False

# === 优化 2：查询重写 (解决中英文检索不匹配问题) ===
async def _rewrite_query(user_query: str, llm_client_wrapper):
    """
    使用 LLM 将用户的自然语言（可能是中文）转换为 3-5 个代码搜索关键词（英文）。
    """
    prompt = f"""
    You are a Code Search Expert.
    Task: Convert the user's query into 3-5 English keywords for code search (BM25/Vector).
    
    User Query: "{user_query}"
    
    Rules:
    1. Output ONLY a JSON list of strings.
    2. Translate concepts to technical terms (e.g., "鉴权" -> "auth", "login", "middleware").
    3. Keep it short.
    
    Example Output: ["authentication", "login_handler", "jwt_verify"]
    """
    try:
        response = await llm_client_wrapper.chat_completions_create(
            model=None,  # 使用 wrapper 的默认模型
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=100
        )
        content = response.choices[0].message.content
        # 简单清洗
        content = re.sub(r"^```(json)?|```$", "", content.strip(), flags=re.MULTILINE).strip()
        keywords = json.loads(content)
        if isinstance(keywords, list):
            return " ".join(keywords) # 返回空格分隔的字符串供 BM25 使用
        return user_query
    except Exception as e:
        print(f"⚠️ Query Rewrite Failed: {e}")
        return user_query # 降级：直接用原句

async def process_chat_stream(user_query: str, session_id: str, model_provider: str = "kimi"):
    """
    处理聊天流
    
    Args:
        user_query: 用户查询
        session_id: 会话 ID
        model_provider: 模型提供商，"groq"、"deepseek" 或 "kimi"，默认为 "groq"
    """
    vector_db = store_manager.get_store(session_id)
    
    # === 动态创建 LLM 客户端 ===
    try:
        # 根据 provider 确定模型名称
        if model_provider.lower() == "groq":
            model_name = "groq/compound"
        elif model_provider.lower() == "deepseek":
            model_name = "deepseek-chat"
        elif model_provider.lower() == "kimi":
            from app.core.config import settings
            model_name = settings.GITCODE_MODEL_NAME
        else:
            # 默认使用 kimi
            model_provider = "kimi"
            from app.core.config import settings
            model_name = settings.GITCODE_MODEL_NAME
        
        llm_client_wrapper = create_llm_client(model_provider, model_name)
    except Exception as e:
        yield f"❌ 模型初始化失败: {str(e)}\n"
        return
    
    # === 1. 语言环境检测 ===
    use_chinese = is_chinese_query(user_query)
    
    # 定义 UI 提示语 (根据语言切换)
    ui_msgs = {
        "thinking": f"> 🧠 **Thinking:** Searching for code related to: " if not use_chinese else f"> 🧠 **思考中:** 正在检索相关代码: ",
        "action": f"\n\n> 🔍 **Agent Action:** Retrieving missing files: " if not use_chinese else f"\n\n> 🔍 **Agent 动作:** 正在读取缺失文件: ",
        "error_url": f"> ⚠️ Error: Repository URL lost.\n" if not use_chinese else f"> ⚠️ 错误: 仓库链接丢失。\n",
        "warning_file": f"> ⚠️ Warning: Failed to access " if not use_chinese else f"> ⚠️ 警告: 无法读取 ",
        "system_note": "Please provide the FINAL answer." if not use_chinese else "System Notification: Files loaded. Please provide the FINAL answer in Chinese."
    }

    # === 步骤 0: 查询重写 (增强检索命中率) ===
    # 比如用户问 "鉴权在哪里？" -> rewrite -> "auth login verify"
    search_query = await _rewrite_query(user_query, llm_client_wrapper)
    # 可以在这里 yield 一个 debug 信息给前端，如果不想要可以注释掉
    yield f"{ui_msgs['thinking']}`{search_query}`...\n\n"
    
    # 1. 检索 RAG (使用重写后的 Query)
    # 使用 asyncio.to_thread 避免阻塞主线程
    relevant_docs = await vector_db.search_hybrid(search_query, top_k=6)
    rag_context = _build_context(relevant_docs)
    
    # 2. 获取全局上下文
    global_context = vector_db.global_context or {}
    file_tree = global_context.get("file_tree", "(File tree not available.)")
    agent_summary = global_context.get("summary", "") 
    
    # 3. 构造 Prompt (Context Priority)
    lang_instruction = "IMPORTANT: The user is asking in Chinese. You MUST reply in Simplified Chinese (简体中文)." if use_chinese else "Reply in English."
    system_instruction = f"""
    You are a Senior GitHub Repository Analyst.
    {lang_instruction}
    
    [Global Context - Repo Map]
    {file_tree}
    
    [Agent Analysis Summary]
    {agent_summary}
    
    [Current Code Context (Retrieved)]
    {rag_context}
    
    [INSTRUCTIONS]
    1. **CHECK CONTEXT FIRST**: Look at the [Current Code Context]. Does it contain the answer?
    2. **IF YES**: Answer directly. DO NOT use tools.
    3. **IF NO**: Request missing files using tags.
    
    [Tool Usage]
    Format: <tool_code>path/to/file</tool_code>
    """
    
    augmented_user_query = f"""
    {user_query}
    
    (System Note: Priority 1: Answer using context. Priority 2: Use <tool_code> ONLY if critical info is missing.)
    """
    
    messages = [
        {"role": "system", "content": system_instruction},
        {"role": "user", "content": augmented_user_query}
    ]

    try:
        # === Phase 1: 思考与回答 ===
        stream = await llm_client_wrapper.chat_completions_create(
            messages=messages,
            stream=True,
            temperature=0.1, 
            max_tokens=4096
        )
        
        buffer = ""
        full_response = ""
        requested_files = set()
        
        async for chunk in stream:
            content = chunk.choices[0].delta.content or ""
            if not content: continue
            
            buffer += content
            full_response += content
            
            # 检测标签
            if "</tool_code>" in buffer:
                matches = re.findall(r"<tool_code>\s*(.*?)\s*</tool_code>", buffer, re.DOTALL)
                for f in matches:
                    clean_f = f.strip().replace("'", "").replace('"', "").replace("`", "")
                    requested_files.add(clean_f)
                
                yield content
                buffer = "" 
            else:
                yield content

        if "</tool_code>" in buffer:
            matches = re.findall(r"<tool_code>\s*(.*?)\s*</tool_code>", buffer, re.DOTALL)
            for f in matches:
                clean_f = f.strip().replace("'", "").replace('"', "").replace("`", "")
                requested_files.add(clean_f)

        # === Phase 2: 按需下载 ===
        if requested_files:
            file_list_str = ", ".join([f"`{f}`" for f in requested_files])
            yield f"\n\n> 🔍 **Agent Action:** Retrieving missing files: {file_list_str}...\n\n"
            
            if not vector_db.repo_url:
                yield f"> ⚠️ Error: Repository URL lost.\n"
                return

            new_docs_accumulated = []
            for file_path in requested_files:
                if file_path in vector_db.indexed_files:
                    docs = vector_db.get_documents_by_file(file_path)
                    new_docs_accumulated.extend(docs)
                else:
                    success = await _download_and_index(vector_db, file_path)
                    if success:
                        docs = vector_db.get_documents_by_file(file_path)
                        new_docs_accumulated.extend(docs)
                    else:
                        yield f"> ⚠️ Warning: Failed to access `{file_path}`.\n"

            # === Phase 3: 最终回答 ===
            if new_docs_accumulated:
                supplementary_context = _build_context(new_docs_accumulated)
                
                final_messages = [
                    {"role": "system", "content": system_instruction},
                    {"role": "user", "content": augmented_user_query},
                    {"role": "assistant", "content": full_response},
                    {"role": "user", "content": f"System Notification: Requested files loaded.\n\n[New Code Context]\n{supplementary_context}\n\nPlease provide the FINAL answer."}
                ]
                
                stream_final = await llm_client_wrapper.chat_completions_create(
                    messages=final_messages,
                    stream=True,
                    temperature=0.2
                )
                
                async for chunk in stream_final:
                    content = chunk.choices[0].delta.content or ""
                    if content:
                        yield content

    except Exception as e:
        import traceback
        traceback.print_exc()
        yield f"❌ System Error: {str(e)}"

# 辅助函数保持不变
def _build_context(docs):
    if not docs: return "(No relevant code snippets found yet)"
    context = ""
    for doc in docs:
        file_info = doc['file']
        if 'class' in doc.get('metadata', {}):
            cls = doc['metadata']['class']
            if cls: file_info += f" (Class: {cls})"
        context += f"\n--- File: {file_info} ---\n{doc['content'][:2000]}\n"
    return context

async def _download_and_index(vector_db, file_path):
    try:
        content = get_file_content(vector_db.repo_url, file_path)
        if not content: return False
        
        chunks = await asyncio.to_thread(chunker.chunk_file, content, file_path)
        if not chunks: 
            chunks = [{
                "content": content,
                "metadata": {"file": file_path, "type": "text", "name": "root", "class": ""}
            }]
            
        documents = [c["content"] for c in chunks]
        metadatas = []
        for c in chunks:
            meta = c["metadata"]
            metadatas.append({
                "file": meta["file"],
                "type": meta["type"],
                "name": meta.get("name", ""),
                "class": meta.get("class") or ""
            })
        await vector_db.add_documents(documents, metadatas)
        return True
    except Exception as e:
        print(f"Download Error: {e}")
        return False