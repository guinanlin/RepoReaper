# 文件路径: app/utils/llm_client.py
from openai import AsyncOpenAI
from app.core.config import settings
import os
from typing import Optional, AsyncIterator, Dict, Any

# 根据配置选择 LLM Provider
llm_provider = getattr(settings, "LLM_PROVIDER", "kimi").lower()
print(f"🔧 LLM Provider 配置: {llm_provider.upper()}")

# 初始化客户端
client = None
groq_client = None
kimi_client = None

if llm_provider == "groq":
    # 使用 Groq
    try:
        from groq import Groq, AsyncGroq
        
        api_key = getattr(settings, "GROQ_API_KEY", os.getenv("GROQ_API_KEY"))
        if api_key:
            # 清理 API key：去除前后空格和换行符
            api_key = api_key.strip()
            # 移除可能的引号
            if api_key.startswith('"') and api_key.endswith('"'):
                api_key = api_key[1:-1]
            if api_key.startswith("'") and api_key.endswith("'"):
                api_key = api_key[1:-1]
            api_key = api_key.strip()
            
            # 调试信息：显示 API key 预览
            key_preview = f"{api_key[:8]}...{api_key[-4:]}" if len(api_key) > 12 else "***"
            print(f"🔑 Groq API Key 预览: {key_preview} (长度: {len(api_key)})")
            print(f"📦 使用模型: {settings.MODEL_NAME}")
            
            # Groq 同时支持同步和异步客户端
            groq_client = AsyncGroq(api_key=api_key)
            print(f"✅ Groq Client 初始化成功 (Model: {settings.MODEL_NAME})")
        else:
            print("❌ 未找到 GROQ_API_KEY")
    except ImportError:
        print("❌ 未安装 groq 包，请运行: pip install groq")
    except Exception as e:
        print(f"❌ Groq Client 初始化失败: {e}")
        import traceback
        traceback.print_exc()
elif llm_provider == "kimi":
    # 使用 Kimi (GitCode, 兼容 OpenAI SDK)
    try:
        api_key = getattr(settings, "GITCODE_API_KEY", os.getenv("GITCODE_API_KEY"))
        base_url = getattr(settings, "GITCODE_BASE_URL", "https://api-ai.gitcode.com/v1")
        
        if api_key:
            # 清理 API key：去除前后空格和换行符
            api_key = api_key.strip()
            # 移除可能的引号
            if api_key.startswith('"') and api_key.endswith('"'):
                api_key = api_key[1:-1]
            if api_key.startswith("'") and api_key.endswith("'"):
                api_key = api_key[1:-1]
            api_key = api_key.strip()
        
        if base_url:
            base_url = base_url.strip()
        
        if api_key:
            # 调试信息：显示 API key 预览
            key_preview = f"{api_key[:8]}...{api_key[-4:]}" if len(api_key) > 12 else "***"
            print(f"🔑 GitCode (Kimi) API Key 预览: {key_preview} (长度: {len(api_key)})")
            print(f"🌐 GitCode Base URL: {base_url}")
            print(f"📦 使用模型: {settings.GITCODE_MODEL_NAME}")
            
            kimi_client = AsyncOpenAI(
                api_key=api_key,
                base_url=base_url
            )
            print(f"✅ Kimi (GitCode) Client 初始化成功 (Model: {settings.GITCODE_MODEL_NAME})")
        else:
            print("❌ 未找到 GITCODE_API_KEY")
    except Exception as e:
        print(f"❌ Kimi Client 初始化失败: {e}")
        import traceback
        traceback.print_exc()
else:
    # 默认使用 DeepSeek (兼容 OpenAI SDK)
    try:
        api_key = getattr(settings, "DEEPSEEK_API_KEY", os.getenv("DEEPSEEK_API_KEY"))
        if api_key:
            # 清理 API key：去除前后空格和换行符
            api_key = api_key.strip()
        base_url = getattr(settings, "DEEPSEEK_BASE_URL", "https://api.deepseek.com")
        if base_url:
            base_url = base_url.strip()
        
        if api_key:
            # 清理 API key：去除前后空格和换行符
            api_key = api_key.strip()
            # 移除可能的引号
            if api_key.startswith('"') and api_key.endswith('"'):
                api_key = api_key[1:-1]
            if api_key.startswith("'") and api_key.endswith("'"):
                api_key = api_key[1:-1]
            api_key = api_key.strip()
            
            # 验证 API key 格式（DeepSeek 通常以 sk- 开头）
            if not api_key.startswith('sk-'):
                print(f"⚠️ 警告: API Key 格式可能不正确（通常应以 'sk-' 开头）")
            
            # 调试信息：显示 API key 的前几个字符和后几个字符（用于验证格式）
            key_preview = f"{api_key[:8]}...{api_key[-4:]}" if len(api_key) > 12 else "***"
            print(f"🔑 DeepSeek API Key 预览: {key_preview} (长度: {len(api_key)})")
            print(f"🌐 DeepSeek Base URL: {base_url}")
            
            client = AsyncOpenAI(
                api_key=api_key,
                base_url=base_url
            )
            print(f"✅ DeepSeek Client 初始化成功 (Model: {settings.MODEL_NAME})")
        else:
            print("❌ 未找到 DEEPSEEK_API_KEY")
    except Exception as e:
        print(f"❌ DeepSeek Client 初始化失败: {e}")
        import traceback
        traceback.print_exc()


class LLMClientWrapper:
    """
    统一的 LLM 客户端包装器，支持 DeepSeek、Groq 和 Kimi
    """
    def __init__(self):
        self.provider = llm_provider
        if llm_provider == "kimi":
            self.model_name = settings.GITCODE_MODEL_NAME
        else:
            self.model_name = settings.MODEL_NAME
        
    async def chat_completions_create(
        self,
        model: Optional[str] = None,
        messages: list = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        max_completion_tokens: Optional[int] = None,
        top_p: float = 1.0,
        stream: bool = False,
        stop: Optional[list] = None,
        timeout: Optional[float] = None,
        compound_custom: Optional[Dict[str, Any]] = None,
        **kwargs
    ):
        """
        统一的聊天完成接口
        
        Args:
            model: 模型名称，如果为 None 则使用配置的默认模型
            messages: 消息列表
            temperature: 温度参数
            max_tokens: 最大 token 数 (DeepSeek)
            max_completion_tokens: 最大完成 token 数 (Groq)
            top_p: top_p 参数
            stream: 是否流式输出
            stop: 停止序列
            timeout: 超时时间
            compound_custom: Groq compound 模型的特殊参数
            **kwargs: 其他参数
        """
        if self.provider == "groq":
            if not groq_client:
                raise ValueError("Groq 客户端未初始化")
            
            # 使用指定的模型或默认模型
            model = model or self.model_name
            
            # 准备 Groq 参数
            groq_params = {
                "model": model,
                "messages": messages or [],
                "temperature": temperature,
                "top_p": top_p,
                "stream": stream,
            }
            
            # Groq 使用 max_completion_tokens 而不是 max_tokens
            if max_completion_tokens is not None:
                groq_params["max_completion_tokens"] = max_completion_tokens
            elif max_tokens is not None:
                groq_params["max_completion_tokens"] = max_tokens
            
            if stop is not None:
                groq_params["stop"] = stop
            
            # 如果是 compound 模型，添加 compound_custom 参数
            if "compound" in model.lower():
                # 优先使用传入的参数，否则使用配置中的默认值
                if compound_custom is not None:
                    groq_params["compound_custom"] = compound_custom
                else:
                    # 尝试从配置中获取默认的 compound_custom
                    default_compound_custom = settings.get_groq_compound_custom()
                    if default_compound_custom:
                        groq_params["compound_custom"] = default_compound_custom
            
            # 调用 Groq API
            return await groq_client.chat.completions.create(**groq_params)
        elif self.provider == "kimi":
            # 使用 Kimi (GitCode, OpenAI 兼容)
            if not kimi_client:
                raise ValueError("Kimi 客户端未初始化")
            
            # 使用指定的模型或默认模型
            model = model or self.model_name
            
            # 准备 OpenAI 兼容参数
            openai_params = {
                "model": model,
                "messages": messages or [],
                "temperature": temperature,
                "top_p": top_p,
                "stream": stream,
            }
            
            if max_tokens is not None:
                openai_params["max_tokens"] = max_tokens
            
            if stop is not None:
                openai_params["stop"] = stop
            
            if timeout is not None:
                openai_params["timeout"] = timeout
            
            # 添加其他参数（包括 thinking_budget 等 Kimi 特有参数）
            openai_params.update(kwargs)
            
            # 调用 OpenAI 兼容 API
            return await kimi_client.chat.completions.create(**openai_params)
        else:
            # 使用 DeepSeek (OpenAI 兼容)
            if not client:
                raise ValueError("DeepSeek 客户端未初始化")
            
            # 使用指定的模型或默认模型
            model = model or self.model_name
            
            # 准备 OpenAI 兼容参数
            openai_params = {
                "model": model,
                "messages": messages or [],
                "temperature": temperature,
                "top_p": top_p,
                "stream": stream,
            }
            
            if max_tokens is not None:
                openai_params["max_tokens"] = max_tokens
            
            if stop is not None:
                openai_params["stop"] = stop
            
            if timeout is not None:
                openai_params["timeout"] = timeout
            
            # 添加其他参数
            openai_params.update(kwargs)
            
            # 调用 OpenAI 兼容 API
            return await client.chat.completions.create(**openai_params)


# 创建全局包装器实例
_wrapper = LLMClientWrapper()

# 为了保持向后兼容，创建一个兼容 OpenAI SDK 的客户端对象
class CompatibleClient:
    """兼容 OpenAI SDK 的客户端包装器"""
    
    @property
    def chat(self):
        return self
    
    @property
    def completions(self):
        return self
    
    async def create(self, **kwargs):
        """兼容 OpenAI SDK 的 create 方法"""
        return await _wrapper.chat_completions_create(**kwargs)


# 导出兼容的客户端对象
if llm_provider == "groq":
    # 如果使用 Groq，导出包装器
    client = CompatibleClient()
elif llm_provider == "kimi":
    # 如果使用 Kimi，导出包装器
    client = CompatibleClient()
else:
    # 如果使用 DeepSeek，保持原有的 client 对象
    pass  # client 已经在上面初始化了

# 为了向后兼容，也导出 wrapper 以便直接使用
wrapper = _wrapper


def create_llm_client(provider: str, model_name: Optional[str] = None):
    """
    动态创建 LLM 客户端
    
    Args:
        provider: "groq"、"deepseek" 或 "kimi"
        model_name: 模型名称，如果为 None 则使用配置的默认值
    
    Returns:
        LLMClientWrapper 实例
    """
    import os
    from groq import AsyncGroq
    from openai import AsyncOpenAI
    
    provider = provider.lower()
    
    # 根据 provider 确定默认模型名称
    if provider == "kimi":
        model_name = model_name or settings.GITCODE_MODEL_NAME
    else:
        model_name = model_name or settings.MODEL_NAME
    
    if provider == "groq":
        api_key = getattr(settings, "GROQ_API_KEY", os.getenv("GROQ_API_KEY"))
        if not api_key:
            raise ValueError("GROQ_API_KEY 未配置")
        
        # 清理 API key
        api_key = api_key.strip()
        if api_key.startswith('"') and api_key.endswith('"'):
            api_key = api_key[1:-1]
        if api_key.startswith("'") and api_key.endswith("'"):
            api_key = api_key[1:-1]
        api_key = api_key.strip()
        
        groq_client_instance = AsyncGroq(api_key=api_key)
        
        class DynamicGroqWrapper:
            def __init__(self, client_instance, model):
                self.client = client_instance
                self.model = model
                self.provider = "groq"
            
            async def chat_completions_create(self, model=None, messages=None, temperature=0.7,
                                             max_tokens=None, max_completion_tokens=None,
                                             top_p=1.0, stream=False, stop=None,
                                             compound_custom=None, **kwargs):
                model = model or self.model
                groq_params = {
                    "model": model,
                    "messages": messages or [],
                    "temperature": temperature,
                    "top_p": top_p,
                    "stream": stream,
                }
                
                if max_completion_tokens is not None:
                    groq_params["max_completion_tokens"] = max_completion_tokens
                elif max_tokens is not None:
                    groq_params["max_completion_tokens"] = max_tokens
                
                if stop is not None:
                    groq_params["stop"] = stop
                
                if "compound" in model.lower():
                    if compound_custom is not None:
                        groq_params["compound_custom"] = compound_custom
                    else:
                        default_compound_custom = settings.get_groq_compound_custom()
                        if default_compound_custom:
                            groq_params["compound_custom"] = default_compound_custom
                
                return await self.client.chat.completions.create(**groq_params)
        
        return DynamicGroqWrapper(groq_client_instance, model_name)
    
    elif provider == "deepseek":
        api_key = getattr(settings, "DEEPSEEK_API_KEY", os.getenv("DEEPSEEK_API_KEY"))
        base_url = getattr(settings, "DEEPSEEK_BASE_URL", "https://api.deepseek.com")
        
        if not api_key:
            raise ValueError("DEEPSEEK_API_KEY 未配置")
        
        # 清理 API key
        api_key = api_key.strip()
        if api_key.startswith('"') and api_key.endswith('"'):
            api_key = api_key[1:-1]
        if api_key.startswith("'") and api_key.endswith("'"):
            api_key = api_key[1:-1]
        api_key = api_key.strip()
        base_url = base_url.strip()
        
        deepseek_client = AsyncOpenAI(api_key=api_key, base_url=base_url)
        
        class DynamicDeepSeekWrapper:
            def __init__(self, client_instance, model):
                self.client = client_instance
                self.model = model
                self.provider = "deepseek"
            
            async def chat_completions_create(self, model=None, messages=None, temperature=0.7,
                                             max_tokens=None, top_p=1.0, stream=False,
                                             stop=None, timeout=None, **kwargs):
                model = model or self.model
                openai_params = {
                    "model": model,
                    "messages": messages or [],
                    "temperature": temperature,
                    "top_p": top_p,
                    "stream": stream,
                }
                
                if max_tokens is not None:
                    openai_params["max_tokens"] = max_tokens
                if stop is not None:
                    openai_params["stop"] = stop
                if timeout is not None:
                    openai_params["timeout"] = timeout
                
                openai_params.update(kwargs)
                return await self.client.chat.completions.create(**openai_params)
        
        return DynamicDeepSeekWrapper(deepseek_client, model_name)
    
    elif provider == "kimi":
        api_key = getattr(settings, "GITCODE_API_KEY", os.getenv("GITCODE_API_KEY"))
        base_url = getattr(settings, "GITCODE_BASE_URL", "https://api-ai.gitcode.com/v1")
        
        if not api_key:
            raise ValueError("GITCODE_API_KEY 未配置")
        
        # 清理 API key
        api_key = api_key.strip()
        if api_key.startswith('"') and api_key.endswith('"'):
            api_key = api_key[1:-1]
        if api_key.startswith("'") and api_key.endswith("'"):
            api_key = api_key[1:-1]
        api_key = api_key.strip()
        base_url = base_url.strip()
        
        kimi_client_instance = AsyncOpenAI(api_key=api_key, base_url=base_url)
        
        class DynamicKimiWrapper:
            def __init__(self, client_instance, model):
                self.client = client_instance
                self.model = model
                self.provider = "kimi"
            
            async def chat_completions_create(self, model=None, messages=None, temperature=0.7,
                                             max_tokens=None, top_p=1.0, stream=False,
                                             stop=None, timeout=None, **kwargs):
                model = model or self.model
                openai_params = {
                    "model": model,
                    "messages": messages or [],
                    "temperature": temperature,
                    "top_p": top_p,
                    "stream": stream,
                }
                
                if max_tokens is not None:
                    openai_params["max_tokens"] = max_tokens
                if stop is not None:
                    openai_params["stop"] = stop
                if timeout is not None:
                    openai_params["timeout"] = timeout
                
                # 添加其他参数（包括 thinking_budget 等 Kimi 特有参数）
                openai_params.update(kwargs)
                return await self.client.chat.completions.create(**openai_params)
        
        return DynamicKimiWrapper(kimi_client_instance, model_name)
    
    else:
        raise ValueError(f"不支持的 provider: {provider}，仅支持 'groq'、'deepseek' 或 'kimi'")
