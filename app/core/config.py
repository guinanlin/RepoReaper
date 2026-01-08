# 文件路径: app/core/config.py
import os
from dotenv import load_dotenv

# 加载 .env 文件
load_dotenv()

class Settings:
    # --- API Keys ---
    GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
    
    # [新增] SiliconFlow API Key (用于 BGE-M3 Embedding)
    SILICON_API_KEY = os.getenv("SILICON_API_KEY")
    
    # --- DeepSeek 配置 ---
    DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "").strip() if os.getenv("DEEPSEEK_API_KEY") else None
    DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com").strip()
    
    # --- Groq 配置 ---
    GROQ_API_KEY = os.getenv("GROQ_API_KEY", "").strip() if os.getenv("GROQ_API_KEY") else None
    
    # Groq Compound 模型的自定义配置 (JSON 字符串，会被解析为字典)
    GROQ_COMPOUND_CUSTOM = os.getenv("GROQ_COMPOUND_CUSTOM")
    
    # --- Kimi (GitCode) 配置 ---
    GITCODE_API_KEY = os.getenv("GITCODE_API_KEY", "").strip() if os.getenv("GITCODE_API_KEY") else None
    GITCODE_BASE_URL = os.getenv("GITCODE_BASE_URL", "https://api-ai.gitcode.com/v1").strip()
    GITCODE_MODEL_NAME = os.getenv("GITCODE_MODEL_NAME", "moonshotai/Kimi-K2-Instruct-0905")
    
    # 模型名称 (支持 deepseek-chat、groq/compound 或 moonshotai/Kimi-K2-Instruct-0905 等)
    MODEL_NAME = os.getenv("MODEL_NAME", "moonshotai/Kimi-K2-Instruct-0905")
    
    # LLM 提供商类型 (deepseek、groq 或 kimi)
    LLM_PROVIDER = os.getenv("LLM_PROVIDER", "kimi")
    
    def get_groq_compound_custom(self):
        """解析 GROQ_COMPOUND_CUSTOM 环境变量为字典"""
        if not self.GROQ_COMPOUND_CUSTOM:
            return None
        try:
            import json
            return json.loads(self.GROQ_COMPOUND_CUSTOM)
        except:
            return None
    
    # --- 服务配置 ---
    HOST = os.getenv("HOST", "127.0.0.1")
    PORT = int(os.getenv("PORT", 8000))

    def validate(self):
        """启动时检查必要的 Key 是否存在"""
        missing_keys = []

        # 1. 检查 LLM Provider Key (DeepSeek、Groq 或 Kimi)
        if self.LLM_PROVIDER.lower() == "groq":
            if not self.GROQ_API_KEY:
                missing_keys.append("GROQ_API_KEY")
        elif self.LLM_PROVIDER.lower() == "kimi":
            if not self.GITCODE_API_KEY:
                missing_keys.append("GITCODE_API_KEY")
        else:
            # 默认使用 DeepSeek
            if not self.DEEPSEEK_API_KEY:
                missing_keys.append("DEEPSEEK_API_KEY")

        # 2. 检查 SiliconCloud Key (Embedding 必需)
        # 如果你现在的代码强制依赖它，这里最好报错
        if not self.SILICON_API_KEY:
             # 为了避免再次报错 AttributeError，这里只是打印警告，或者你可以选择 raise ValueError
             print("⚠️ 警告: 未找到 SILICON_API_KEY，向量检索功能可能无法工作。")
            
        if missing_keys:
            raise ValueError(f"❌ 错误: 缺少必要的环境变量: {', '.join(missing_keys)}。请检查 .env 文件。")
            
        # 3. 检查 GitHub Token (可选但建议)
        if not self.GITHUB_TOKEN:
            print("⚠️ 警告: 未找到 GITHUB_TOKEN，GitHub API 请求将受到每小时 60 次的严格限制。建议配置 Token。")

settings = Settings()
# 立即执行验证，确保启动时就暴露问题
settings.validate()