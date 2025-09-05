"""
Base Agent 类 - QuantumForge vNext

提供所有Agent的公共基础功能，包括统一的重试逻辑和错误处理。
从 llm_engine.py 重构而来，消除重复代码。
"""

import json
import time
import asyncio
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from openai import OpenAI, AsyncOpenAI
from .performance_monitor import record_agent_call, get_monitor


class BaseAgent(ABC):
    """
    所有Agent的基类
    
    提供统一的：
    - 重试逻辑
    - 错误处理  
    - OpenAI API调用
    - JSON响应解析
    """
    
    def __init__(self, client: OpenAI, async_client: AsyncOpenAI = None, max_retries: int = 3):
        """
        初始化BaseAgent
        
        Args:
            client: OpenAI客户端实例
            async_client: AsyncOpenAI客户端实例（可选）
            max_retries: 最大重试次数
        """
        self.client = client
        self.async_client = async_client
        self.max_retries = max_retries
        self.prompt = self._get_prompt()
    
    @abstractmethod
    def _get_prompt(self) -> str:
        """
        获取Agent专用的prompt模板
        
        Returns:
            Agent的prompt字符串
        """
        pass
    
    @abstractmethod  
    def process(self, *args, **kwargs) -> Any:
        """
        Agent的核心处理方法
        
        Args:
            *args: 输入参数
            **kwargs: 关键字参数
            
        Returns:
            处理结果
        """
        pass
    
    def _call_with_retry(self, user_message: str, agent_name: str) -> Dict[str, Any]:
        """
        统一的重试调用逻辑
        
        Args:
            user_message: 发送给LLM的消息
            agent_name: Agent名称（用于日志）
            
        Returns:
            解析后的JSON响应
            
        Raises:
            RuntimeError: 重试次数耗尽后抛出异常
        """
        for attempt in range(self.max_retries):
            try:
                response = self._call_openai(self.prompt, user_message, agent_name)
                return self._parse_json_with_retry(response, agent_name)
            except Exception as e:
                if attempt == self.max_retries - 1:
                    raise RuntimeError(f"{agent_name} failed after {self.max_retries} retries: {str(e)}")
                
                print(f"⚠️ {agent_name} retry {attempt + 1}/{self.max_retries}: {str(e)}")
                time.sleep(0.5)
    
    def _call_openai(self, prompt: str, user_message: str, agent_name: str) -> str:
        """
        调用OpenAI API
        
        Args:
            prompt: 系统提示词
            user_message: 用户消息
            agent_name: Agent名称
            
        Returns:
            API响应内容
        """
        try:
            start_time = time.time()
            
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": user_message}
                ],
                temperature=0.1,
                max_tokens=4096
            )
            
            call_time = time.time() - start_time
            content = response.choices[0].message.content.strip()
            
            # 记录性能数据
            if agent_name:
                input_tokens = response.usage.prompt_tokens if response.usage else 0
                output_tokens = response.usage.completion_tokens if response.usage else 0
                record_agent_call(agent_name, prompt + user_message, content, call_time, "gpt-4o-mini")
                
                # 更新精确的token数据
                metrics = get_monitor().get_agent_metrics(agent_name)
                metrics.set_tokens(input_tokens, output_tokens)
            
            return content
        except Exception as e:
            raise RuntimeError(f"{agent_name} API call failed: {str(e)}")
    
    async def _call_openai_async(self, prompt: str, user_message: str, agent_name: str = "UnknownAgent") -> str:
        """
        调用OpenAI API (异步版本)
        
        Args:
            prompt: 系统提示词
            user_message: 用户消息
            agent_name: Agent名称
            
        Returns:
            API响应内容
        """
        if not self.async_client:
            raise RuntimeError(f"{agent_name} async client not available")
            
        try:
            response = await self.async_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": user_message}
                ],
                temperature=0.1,
                max_tokens=4096
            )
            
            return response.choices[0].message.content.strip()
        except Exception as e:
            raise RuntimeError(f"{agent_name} async API call failed: {str(e)}")
    
    def _parse_json_with_retry(self, response: str, agent_name: str) -> Dict[str, Any]:
        """
        解析JSON响应，带重试机制
        
        Args:
            response: API响应字符串
            agent_name: Agent名称
            
        Returns:
            解析后的JSON数据
            
        Raises:
            ValueError: JSON解析失败
        """
        try:
            # 调试：检查响应是否为空
            if not response or response.strip() == "":
                raise ValueError(f"{agent_name} returned empty response")
            
            # 清理markdown代码块
            if response.startswith("```json"):
                response = response.replace("```json", "").replace("```", "").strip()
            
            # 尝试解析完整响应
            try:
                data = json.loads(response)
                return data
            except json.JSONDecodeError:
                # 如果失败，尝试提取第一个完整的JSON对象
                lines = response.split('\n')
                json_lines = []
                brace_count = 0
                started = False
                
                for line in lines:
                    stripped = line.strip()
                    if stripped.startswith('{') and not started:
                        started = True
                    
                    if started:
                        json_lines.append(line)
                        brace_count += line.count('{') - line.count('}')
                        
                        # 当大括号匹配时，我们可能有完整的JSON
                        if brace_count == 0:
                            break
                
                if json_lines:
                    json_text = '\n'.join(json_lines)
                    data = json.loads(json_text)
                    return data
                else:
                    raise ValueError(f"{agent_name} response contains no valid JSON")
            
        except json.JSONDecodeError as e:
            raise ValueError(f"{agent_name} returned invalid JSON: {str(e)}")
        except Exception as e:
            raise ValueError(f"{agent_name} response parsing failed: {str(e)}")


class AgentWithMemory(BaseAgent):
    """
    带Memory访问的Agent基类
    
    为需要学习和记忆功能的Agent提供基础功能
    """
    
    def __init__(self, client: OpenAI, async_client: AsyncOpenAI = None, max_retries: int = 3, agent_memory=None):
        """
        初始化带Memory的Agent
        
        Args:
            client: OpenAI客户端实例
            async_client: AsyncOpenAI客户端实例（可选）
            max_retries: 最大重试次数
            agent_memory: AgentMemory实例
        """
        super().__init__(client, async_client, max_retries)
        self.agent_memory = agent_memory
    
    def _has_memory(self) -> bool:
        """检查是否有可用的Memory"""
        return self.agent_memory is not None
    
    def _record_success(self, input_data: Any, output_data: Any) -> None:
        """
        记录成功的处理案例
        
        Args:
            input_data: 输入数据
            output_data: 输出数据
        """
        if self._has_memory():
            self.agent_memory.record_success_case(
                agent_type=self.__class__.__name__,
                input_data=input_data,
                output_data=output_data
            )
    
    def _find_similar_case(self, input_data: Any) -> Optional[Any]:
        """
        查找相似的历史案例
        
        Args:
            input_data: 当前输入数据
            
        Returns:
            相似案例的输出，或None
        """
        if self._has_memory():
            return self.agent_memory.find_similar_case(
                agent_type=self.__class__.__name__,
                input_data=input_data
            )
        return None