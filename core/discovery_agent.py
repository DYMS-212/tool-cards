"""
Discovery Agent - QuantumForge vNext

组件发现Agent，负责从组件注册表中选择合适的组件来满足任务需求。
从 llm_engine.py 重构而来，具备学习和记忆能力。
"""

import json
import asyncio
from typing import Dict, Any, List
from openai import OpenAI, AsyncOpenAI
from .base_agent import AgentWithMemory


class DiscoveryAgent(AgentWithMemory):
    """
    组件发现Agent
    
    功能：
    - 从组件注册表中选择合适组件
    - 学习和记忆成功的组件组合
    - 支持同步和异步操作
    """
    
    def _get_prompt(self) -> str:
        """获取DiscoveryAgent的prompt模板"""
        return """Quantum component discovery: Select components from registry matching TaskCard domain/algorithm.
Return exact copies from registry - preserve ALL fields unchanged.

CRITICAL: No modifications to field names or values.
❌ Don't shorten: "build_molecular_hamiltonian" → "molecular_h" 
✅ Exact copy only

Output: JSON array of selected components with all original fields."""
    
    def process(self, task_card: Dict[str, Any], registry_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        发现合适的组件
        
        Args:
            task_card: 任务卡
            registry_data: 组件注册表数据
            
        Returns:
            ComponentCards列表
        """
        
        # TOKEN优化：智能预过滤registry
        filtered_registry = self._filter_relevant_components(task_card, registry_data)
        
        # TOKEN优化：压缩schema用于LLM调用
        compressed_registry = self._compress_schema_for_llm(filtered_registry)
        print(f"🔍 Registry优化: {len(registry_data)} → {len(filtered_registry)} 组件，schema已压缩")
        
        # 准备用户消息
        user_message = f"""
TaskCard: {json.dumps(task_card, ensure_ascii=False)}

Component Registry:
{json.dumps(compressed_registry, ensure_ascii=False, indent=2)}
Please select appropriate components from the registry to satisfy this task requirement."""
        
        try:
            result = self._call_with_retry(user_message, "DiscoveryAgent")
            
            if self._validate_component_cards(result):
                return result
            else:
                raise ValueError("ComponentCards格式验证失败")
                
        except Exception as e:
            raise RuntimeError(f"DiscoveryAgent处理失败: {str(e)}")
    
    async def process_async(self, task_card: Dict[str, Any], registry_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        异步发现合适的组件
        
        Args:
            task_card: 任务卡
            registry_data: 组件注册表数据
            
        Returns:
            ComponentCards列表
        """
        
        # TOKEN优化：智能预过滤registry + schema压缩
        filtered_registry = self._filter_relevant_components(task_card, registry_data)
        compressed_registry = self._compress_schema_for_llm(filtered_registry)
        print(f"🔍 Async Registry优化: {len(registry_data)} → {len(filtered_registry)} 组件，schema已压缩")
        
        user_message = f"""
TaskCard: {json.dumps(task_card, ensure_ascii=False)}
Component Registry: {json.dumps(compressed_registry, ensure_ascii=False)}
Please select appropriate components from the registry based on the TaskCard."""
        
        for attempt in range(self.max_retries):
            try:
                response = await self._call_openai_async(self.prompt, user_message, "DiscoveryAgent")
                parsed_data = self._parse_json_with_retry(response, "DiscoveryAgent")
                
                if self._validate_component_cards(parsed_data):
                    return parsed_data
                else:
                    raise ValueError("ComponentCards格式验证失败")
            
            except Exception as e:
                if attempt == self.max_retries - 1:
                    raise RuntimeError(f"DiscoveryAgent异步调用失败，已重试{self.max_retries}次: {str(e)}")
                
                await asyncio.sleep(0.5)
    
    def _validate_component_cards(self, data: List[Dict[str, Any]]) -> bool:
        """验证ComponentCards格式"""
        if not isinstance(data, list):
            return False
        
        required_fields = ["name", "kind", "tags", "needs", "provides", "params_schema", "yields", "codegen_hint"]
        
        for card in data:
            if not isinstance(card, dict):
                return False
            for field in required_fields:
                if field not in card:
                    return False
        
        return True
    
    def _filter_relevant_components(self, task_card: Dict[str, Any], registry_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        智能预过滤组件，基于domain和algorithm匹配
        
        Args:
            task_card: 任务卡，包含domain和algorithm信息
            registry_data: 完整的组件注册表
            
        Returns:
            过滤后的组件列表
        """
        domain = task_card.get("domain", "").lower()
        algorithm = task_card.get("algorithm", "").lower()
        
        filtered_components = []
        
        for component in registry_data:
            # 基础信息提取
            tags = [tag.lower() for tag in component.get("tags", [])]
            kind = component.get("kind", "").lower()
            name = component.get("name", "").lower()
            
            # 多维度匹配评分
            relevance_score = 0
            
            # 1. Domain匹配 (权重40%)
            if any(domain_keyword in name or domain_keyword in " ".join(tags) 
                   for domain_keyword in domain.split(".")):
                relevance_score += 0.4
            
            # 2. Algorithm匹配 (权重30%)
            if algorithm in name or algorithm in " ".join(tags):
                relevance_score += 0.3
            
            # 3. Kind相关性 (权重20%)
            if kind in ["hamiltonian", "ansatz", "optimizer", "algorithm"]:
                relevance_score += 0.2
            
            # 4. 通用组件 (权重10%)
            if kind in ["core", "backend"] or "core" in tags:
                relevance_score += 0.1
            
            # 阈值过滤：relevance >= 0.2 保留
            if relevance_score >= 0.2:
                filtered_components.append(component)
        
        # 确保至少保留核心组件（backend、algorithm）
        if len(filtered_components) < 3:
            for component in registry_data:
                if component.get("kind") in ["core", "backend", "algorithm"]:
                    if component not in filtered_components:
                        filtered_components.append(component)
        
        return filtered_components
    
    def _compress_schema_for_llm(self, components: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        压缩组件schema用于LLM调用，移除冗余描述保留核心信息
        
        Args:
            components: 完整的组件列表
            
        Returns:
            压缩后的组件列表
        """
        compressed_components = []
        
        for component in components:
            compressed_comp = component.copy()
            
            # 压缩params_schema：保留type/default/range，移除description/format_rules
            if "params_schema" in compressed_comp:
                compressed_schema = {}
                for param_name, param_spec in compressed_comp["params_schema"].items():
                    if isinstance(param_spec, dict):
                        compressed_schema[param_name] = {
                            key: value for key, value in param_spec.items()
                            if key in ["type", "default", "range", "options"]
                        }
                    else:
                        compressed_schema[param_name] = param_spec
                
                compressed_comp["params_schema"] = compressed_schema
            
            compressed_components.append(compressed_comp)
        
        return compressed_components
