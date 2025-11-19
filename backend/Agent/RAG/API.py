"""
简单的火山方舟 LLM API 调用客户端（SDK + .env 配置 + 流式输出）
"""
import os
from typing import Optional, Generator
from dotenv import load_dotenv  # 用于加载 .env 文件

# 确保已安装依赖：pip install -U 'volcengine-python-sdk[ark]' python-dotenv
from volcenginesdkarkruntime import Ark


class LLMClient:
    def __init__(self, model: str = "doubao-seed-1.6-250615", timeout: int = 1800):
        # 1. 加载 .env 文件（自动读取项目根目录的 .env）
        load_dotenv()  # 关键：这行代码会加载 .env 中的配置到环境变量

        # 2. 从环境变量读取 API Key（此时环境变量已包含 .env 中的配置）
        self.api_key = os.environ.get("ARK_API_KEY")
        if not self.api_key:
            raise ValueError("请在 .env 文件中配置 ARK_API_KEY")

        self.model = model
        self.timeout = timeout

        # 3. 初始化火山方舟官方 SDK 客户端
        self.client = Ark(
            api_key=self.api_key,
            timeout=self.timeout
        )

    def chat_completion(self, messages: list, **kwargs) -> Optional[str]:
        """同步调用（一次性返回结果）"""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                **kwargs
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"火山方舟API调用失败: {e}")
            return None

    def stream_chat(self, messages: list, **kwargs) -> Generator[str, None, None]:
        """流式调用（逐块返回）"""
        try:
            stream = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                stream=True,
                **kwargs
            )
            for chunk in stream:
                delta = chunk.choices[0].delta
                if delta and delta.content:
                    yield delta.content
        except Exception as e:
            print(f"火山方舟流式API调用失败: {e}")
            return

    def simple_chat(self, prompt: str, **kwargs) -> Optional[str]:
        """简单单轮同步对话"""
        messages = [{"role": "user", "content": prompt}]
        return self.chat_completion(messages, **kwargs)

    def simple_stream_chat(self, prompt: str, **kwargs) -> Generator[str, None, None]:
        """简单单轮流式对话"""
        messages = [{"role": "user", "content": prompt}]
        yield from self.stream_chat(messages, **kwargs)


# 使用示例
if __name__ == "__main__":
    # 无需手动设置环境变量，只需确保 .env 文件存在且配置正确
    client = LLMClient(model="doubao-seed-1.6-250615")

    print("=== 同步调用示例 ===")
    resp = client.simple_chat("你好，请简单介绍一下你自己。")
    print(resp)

    print("\n=== 流式调用示例 ===")
    for chunk in client.simple_stream_chat("现在在做流失测试，你只需要输出100字即可"):
        print(chunk, end="", flush=True)
    print("\n=== 流式结束 ===")
