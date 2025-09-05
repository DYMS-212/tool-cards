"""
Semantic Agent - QuantumForge vNext

语义解析Agent，负责将自然语言查询转换为结构化TaskCard格式。
从 llm_engine.py 重构而来，专门处理语义理解和任务卡生成。
"""

from typing import Dict, Any
from openai import OpenAI, AsyncOpenAI
from .base_agent import BaseAgent


class SemanticAgent(BaseAgent):
    """
    语义解析Agent
    
    功能：
    - 解析自然语言查询
    - 生成TaskCard格式
    - 领域分类和算法推断
    """
    
    def _get_prompt(self) -> str:
        """获取SemanticAgent的prompt模板"""
        return """Quantum task analyzer: Parse queries into TaskCard JSON.

Keys: domain, problem, algorithm, backend, params
- Extract domain/algorithm from context
- Keep original parameter names/values 
- backend: "qiskit"

DOMAINS: spin.heisenberg, spin.tfim, chemistry.molecular, qml, optimization, custom
ALGORITHMS: vqe, qaoa, qpe, qnn, vqd

Output JSON only."""
    
    def process(self, query: str) -> Dict[str, Any]:
        """
        处理自然语言查询，生成TaskCard
        
        Args:
            query: 用户自然语言查询
            
        Returns:
            TaskCard字典
        """
        try:
            result = self._call_with_retry(query, "SemanticAgent")
            
            if self._validate_task_card(result):
                return result
            else:
                raise ValueError("TaskCard格式验证失败")
                
        except Exception as e:
            raise RuntimeError(f"SemanticAgent处理失败: {str(e)}")
    
    def _validate_task_card(self, data: Dict[str, Any]) -> bool:
        """验证TaskCard格式"""
        required_fields = ["domain", "problem", "algorithm", "backend", "params"]
        valid_domains = {"spin", "spin.tfim", "spin.heisenberg", "spin.ising", "chemistry.molecular", "optimization", "custom"}
        
        # 检查必需字段
        for field in required_fields:
            if field not in data:
                return False
        
        # 检查domain枚举值
        if data["domain"] not in valid_domains:
            return False
        
        # 检查backend固定值
        if data["backend"] != "qiskit":
            return False
        
        return True
