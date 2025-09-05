"""
Pipeline Agent - QuantumForge vNext

流水线编排Agent，负责生成组件的执行顺序和依赖关系图。
从 llm_engine.py 重构而来，专门处理组件依赖解析。
"""

import json
from typing import Dict, Any, List
from openai import OpenAI, AsyncOpenAI
from .base_agent import BaseAgent


class PipelineAgent(BaseAgent):
    """
    流水线编排Agent
    
    功能：
    - 分析组件依赖关系
    - 生成执行顺序
    - 检测依赖冲突
    """
    
    def _get_prompt(self) -> str:
        """获取PipelineAgent的prompt模板"""
        return """You are a quantum pipeline orchestration agent. Generate PipelinePlan JSON based on TaskCard, ComponentCards, and ParamMap.
Implement linear topological sorting to resolve component dependencies.
Analyze needs/provides relationships to create proper execution order.
CRITICAL: You must respond with ONLY valid JSON, no explanatory text before or after.

Output format: {"execution_order": ["component_id_list"], "dependency_graph": {}, "conflicts": []}"""
    
    def process(self, task_card: Dict[str, Any], components: List[Dict[str, Any]], param_map: Dict[str, Any]) -> Dict[str, Any]:
        """
        生成执行流水线计划
        
        Args:
            task_card: 任务卡
            components: 组件列表
            param_map: 参数映射
            
        Returns:
            PipelinePlan字典
        """
        # 准备用户消息
        user_message = f"""
TaskCard: {json.dumps(task_card, ensure_ascii=False)}

ComponentCards: {json.dumps(components, ensure_ascii=False)}

ParamMap: {json.dumps(param_map, ensure_ascii=False)}
Please generate a linear execution pipeline plan based on component needs/provides dependencies."""
        
        try:
            result = self._call_with_retry(user_message, "PipelineAgent")
            
            if self._validate_pipeline_plan(result):
                return result
            else:
                raise ValueError("PipelinePlan格式验证失败")
                
        except Exception as e:
            raise RuntimeError(f"PipelineAgent处理失败: {str(e)}")
    
    def _validate_pipeline_plan(self, data: Dict[str, Any]) -> bool:
        """验证PipelinePlan格式"""
        required_fields = ["execution_order", "dependency_graph", "conflicts"]
        
        for field in required_fields:
            if field not in data:
                return False
        
        return True
