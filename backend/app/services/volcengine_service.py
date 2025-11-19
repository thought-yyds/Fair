"""
火山引擎AI服务集成
"""
import httpx
import json
from typing import Dict, Any, Optional, AsyncGenerator
from app.config import settings
import logging

logger = logging.getLogger(__name__)

class VolcengineService:
    """火山引擎AI服务"""
    
    def __init__(self):
        self.api_key = settings.ai_api_key
        self.api_url = settings.ai_api_url
        self.model = settings.ai_model
        self.max_tokens = settings.ai_max_tokens
        self.timeout = settings.ai_processing_timeout
    
    async def chat_completion(
        self, 
        messages: list, 
        temperature: float = 0.7,
        stream: bool = False
    ) -> Dict[str, Any]:
        """
        调用火山引擎聊天完成API
        
        Args:
            messages: 消息列表
            temperature: 温度参数
            stream: 是否流式返回
            
        Returns:
            API响应结果
        """
        if not self.api_key:
            raise ValueError("火山引擎API密钥未配置")
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": self.max_tokens,
            "stream": stream
        }
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.api_url}/chat/completions",
                    headers=headers,
                    json=payload
                )
                response.raise_for_status()
                
                if stream:
                    return response
                else:
                    return response.json()
                    
        except httpx.HTTPStatusError as e:
            logger.error(f"火山引擎API HTTP错误: {e.response.status_code} - {e.response.text}")
            raise Exception(f"API请求失败: {e.response.status_code}")
        except httpx.RequestError as e:
            logger.error(f"火山引擎API请求错误: {str(e)}")
            raise Exception(f"网络请求失败: {str(e)}")
        except Exception as e:
            logger.error(f"火山引擎API未知错误: {str(e)}")
            raise Exception(f"API调用失败: {str(e)}")
    
    async def chat_completion_stream(
        self, 
        messages: list, 
        temperature: float = 0.7
    ) -> AsyncGenerator[str, None]:
        """
        流式调用火山引擎聊天完成API
        
        Args:
            messages: 消息列表
            temperature: 温度参数
            
        Yields:
            流式响应数据
        """
        try:
            response = await self.chat_completion(messages, temperature, stream=True)
            
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    data = line[6:]  # 移除 "data: " 前缀
                    if data.strip() == "[DONE]":
                        break
                    try:
                        chunk = json.loads(data)
                        if "choices" in chunk and len(chunk["choices"]) > 0:
                            delta = chunk["choices"][0].get("delta", {})
                            if "content" in delta:
                                yield delta["content"]
                    except json.JSONDecodeError:
                        continue
                        
        except Exception as e:
            logger.error(f"火山引擎流式API错误: {str(e)}")
            yield f"错误: {str(e)}"
    
    async def analyze_document(self, content: str, prompt: str = "请分析这个文档的内容") -> str:
        """
        分析文档内容
        
        Args:
            content: 文档内容
            prompt: 分析提示
            
        Returns:
            分析结果
        """
        messages = [
            {
                "role": "system",
                "content": "你是一个专业的文档分析助手，能够深入分析各种类型的文档内容，提取关键信息并提供有价值的见解。"
            },
            {
                "role": "user",
                "content": f"{prompt}\n\n文档内容：\n{content}"
            }
        ]
        
        try:
            response = await self.chat_completion(messages)
            return response["choices"][0]["message"]["content"]
        except Exception as e:
            logger.error(f"文档分析失败: {str(e)}")
            return f"文档分析失败: {str(e)}"
    
    async def generate_summary(self, content: str) -> str:
        """
        生成内容摘要
        
        Args:
            content: 要摘要的内容
            
        Returns:
            摘要结果
        """
        messages = [
            {
                "role": "system",
                "content": "你是一个专业的内容摘要助手，能够准确提取关键信息并生成简洁明了的摘要。"
            },
            {
                "role": "user",
                "content": f"请为以下内容生成摘要：\n\n{content}"
            }
        ]
        
        try:
            response = await self.chat_completion(messages)
            return response["choices"][0]["message"]["content"]
        except Exception as e:
            logger.error(f"内容摘要失败: {str(e)}")
            return f"内容摘要失败: {str(e)}"
    
    async def risk_assessment(self, content: str) -> Dict[str, Any]:
        """
        风险评估
        
        Args:
            content: 要评估的内容
            
        Returns:
            风险评估结果
        """
        messages = [
            {
                "role": "system",
                "content": "你是一个专业的风险评估专家，能够识别和分析各种潜在风险，并提供风险等级评估。"
            },
            {
                "role": "user",
                "content": f"请对以下内容进行风险评估，包括风险等级（低/中/高）、风险类型和具体风险点：\n\n{content}"
            }
        ]
        
        try:
            response = await self.chat_completion(messages)
            content = response["choices"][0]["message"]["content"]
            
            # 解析风险评估结果
            risk_level = "中"  # 默认风险等级
            if "高风险" in content or "高" in content:
                risk_level = "高"
            elif "低风险" in content or "低" in content:
                risk_level = "低"
            
            return {
                "risk_level": risk_level,
                "analysis": content,
                "confidence": 0.85
            }
        except Exception as e:
            logger.error(f"风险评估失败: {str(e)}")
            return {
                "risk_level": "中",
                "analysis": f"风险评估失败: {str(e)}",
                "confidence": 0.0
            }

# 全局服务实例
volcengine_service = VolcengineService()
