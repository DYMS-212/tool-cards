"""
Parameter Processor Agent - QuantumForge vNext

合并的参数处理Agent，集成参数补全和标准化功能。
从ParamCompletionAgent和ParamNormAgent合并而来，减少中间数据传递。
"""

import json
import asyncio
from typing import Dict, Any, List
from openai import OpenAI, AsyncOpenAI
from .base_agent import AgentWithMemory


class ParamProcessorAgent(AgentWithMemory):
    """
    参数处理Agent - 合并版本
    
    功能：
    - 智能推断和补全缺失参数
    - 参数别名映射和标准化
    - 学习和记忆参数处理模式
    - 一次性完成补全+标准化，减少中间数据传递
    """
    
    def _get_prompt(self) -> str:
        """获取ParamProcessorAgent的prompt模板"""
        return """Quantum parameter processor: Complete missing parameters + normalize to canonical names.

WORKFLOW:
1. Extract parameters from query 
2. Map to canonical schema names
3. Fill missing with intelligent defaults

Output JSON only:
{
  "normalized_params": {"canonical_name": value},
  "aliases": {"user_name": "canonical_name"}, 
  "defaults": {"canonical_name": default_value},
  "completion_rationale": "brief explanation",
  "validation_errors": []
}"""
    
    def process(self, query: str, task_card: Dict[str, Any], components: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        一次性完成参数补全和标准化
        
        Args:
            query: 原始用户查询
            task_card: 任务卡
            components: 选择的组件列表
            
        Returns:
            处理完成的ParamMap字典
        """
        
        # 从组件中提取所需参数的schema
        required_schema = {}
        for component in components:
            if "params_schema" in component:
                required_schema.update(component["params_schema"])
        
        # TOKEN优化：压缩组件数据用于LLM调用
        compressed_components = self._compress_components_for_llm(components)
        
        # 准备用户消息
        user_message = f"""
Query: {query}

TaskCard: {json.dumps(task_card, ensure_ascii=False)}

Components: {json.dumps(compressed_components, ensure_ascii=False)}

Required Schema: {json.dumps(self._compress_schema(required_schema), ensure_ascii=False)}

Please complete missing parameters AND normalize them in a single step based on query analysis and domain expertise."""
        
        try:
            result = self._call_with_retry(user_message, "ParamProcessorAgent")
            
            # 验证处理结果
            validation_result = self._validate_param_map(result, required_schema)
            
            if validation_result["valid"]:
                return result
            else:
                raise ValueError(f"参数处理验证失败: 缺失参数 {validation_result['missing']}")
                
        except Exception as e:
            raise RuntimeError(f"ParamProcessorAgent处理失败: {str(e)}")
    
    async def process_async(self, query: str, task_card: Dict[str, Any], components: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        异步参数处理
        
        Args:
            query: 原始用户查询
            task_card: 任务卡
            components: 选择的组件列表
            
        Returns:
            处理完成的ParamMap字典
        """
        
        # 从组件中提取所需参数的schema
        required_schema = {}
        for component in components:
            if "params_schema" in component:
                required_schema.update(component["params_schema"])
        
        # TOKEN优化：压缩组件数据用于LLM调用
        compressed_components = self._compress_components_for_llm(components)
        
        user_message = f"""
Query: {query}

TaskCard: {json.dumps(task_card, ensure_ascii=False)}

Components: {json.dumps(compressed_components, ensure_ascii=False)}

Required Schema: {json.dumps(self._compress_schema(required_schema), ensure_ascii=False)}

Please complete missing parameters AND normalize them in a single step based on query analysis and domain expertise."""
        
        for attempt in range(self.max_retries):
            try:
                response = await self._call_openai_async(self.prompt, user_message, "ParamProcessorAgent")
                parsed_data = self._parse_json_with_retry(response, "ParamProcessorAgent")
                
                validation_result = self._validate_param_map(parsed_data, required_schema)
                if validation_result["valid"]:
                    return parsed_data
                else:
                    raise ValueError(f"ParamMap验证失败: 缺失参数 {validation_result['missing']}")
            
            except Exception as e:
                if attempt == self.max_retries - 1:
                    raise RuntimeError(f"ParamProcessorAgent异步调用失败，已重试{self.max_retries}次: {str(e)}")
                
                await asyncio.sleep(0.5)
    
    def _validate_param_map(self, data: Dict[str, Any], required_schema: Dict[str, Any]) -> Dict[str, Any]:
        """
        验证ParamMap格式和完整性
        
        Args:
            data: ParamMap数据
            required_schema: 所需的参数schema
            
        Returns:
            验证结果 {"valid": bool, "missing": List[str]}
        """
        # 格式验证
        required_fields = ["normalized_params", "aliases", "defaults", "validation_errors"]
        for field in required_fields:
            if field not in data:
                return {"valid": False, "missing": [f"Missing field: {field}"]}
        
        # 参数完整性验证
        missing_params = []
        normalized_params = data.get("normalized_params", {})
        
        for param_name, param_spec in required_schema.items():
            if param_name not in normalized_params:
                # 检查是否有默认值
                if not (isinstance(param_spec, dict) and param_spec.get("default") is not None):
                    missing_params.append(param_name)
        
        return {
            "valid": len(missing_params) == 0,
            "missing": missing_params
        }
    
    def _compress_components_for_llm(self, components: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        压缩组件数据用于LLM调用，只保留核心字段
        
        Args:
            components: 完整的组件列表
            
        Returns:
            压缩后的组件列表
        """
        compressed_components = []
        
        for component in components:
            compressed_comp = {
                "name": component.get("name", ""),
                "kind": component.get("kind", ""),
                "params_schema": self._compress_schema(component.get("params_schema", {}))
            }
            compressed_components.append(compressed_comp)
        
        return compressed_components
    
    def _compress_schema(self, schema: Dict[str, Any]) -> Dict[str, Any]:
        """
        压缩参数schema，保留type/default/range，移除description等
        
        Args:
            schema: 完整的参数schema
            
        Returns:
            压缩后的schema
        """
        compressed_schema = {}
        
        for param_name, param_spec in schema.items():
            if isinstance(param_spec, dict):
                compressed_schema[param_name] = {
                    key: value for key, value in param_spec.items()
                    if key in ["type", "default", "range", "options"]
                }
            else:
                compressed_schema[param_name] = param_spec
        
        return compressed_schema