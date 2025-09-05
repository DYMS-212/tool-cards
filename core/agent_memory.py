"""
Agent Memory 系统 - QuantumForge vNext

专门用于Agent间智能学习和模式记忆的存储系统。
与现有的Memory（CodeCell容器）分离，专注于Agent学习数据。
"""

from typing import Dict, List, Any, Optional
from datetime import datetime


class AgentMemory:
    """
    Agent 智能学习存储
    
    功能：
    - 记录成功的处理模式
    - 学习参数标准化历史
    - 组件组合经验积累
    - 会话内有效（不跨会话持久化）
    """
    
    def __init__(self):
        """初始化AgentMemory"""
        # 参数相关记忆
        self.param_patterns: List[Dict[str, Any]] = []
        self.param_completions: List[Dict[str, Any]] = []
        self.param_normalizations: List[Dict[str, Any]] = []
        
        # 组件相关记忆
        self.component_combinations: List[Dict[str, Any]] = []
        self.successful_discoveries: List[Dict[str, Any]] = []
        
        # 代码生成记忆
        self.generation_patterns: List[Dict[str, Any]] = []
        self.successful_generations: List[Dict[str, Any]] = []
        
        
        # 验证和错误记忆
        self.validation_failures: List[Dict[str, Any]] = []
        self.missing_param_cases: List[Dict[str, Any]] = []
    
    def record_success_case(self, agent_type: str, input_data: Any, output_data: Any) -> None:
        """
        记录Agent成功处理案例
        
        Args:
            agent_type: Agent类型名
            input_data: 输入数据
            output_data: 输出数据
        """
        case = {
            "agent_type": agent_type,
            "timestamp": datetime.now().isoformat(),
            "input": input_data,
            "output": output_data
        }
        
        # 根据Agent类型分类存储
        if agent_type == "DiscoveryAgent":
            self.successful_discoveries.append(case)
        elif agent_type == "ParamNormAgent":
            self.param_normalizations.append(case)
        elif agent_type == "CodegenAgent":
            self.successful_generations.append(case)
    
    def find_similar_case(self, agent_type: str, input_data: Any) -> Optional[Any]:
        """
        查找相似的历史案例
        
        Args:
            agent_type: Agent类型名
            input_data: 当前输入数据
            
        Returns:
            相似案例的输出，或None
        """
        # 根据Agent类型查找对应的历史
        if agent_type == "DiscoveryAgent":
            return self._find_similar_discovery(input_data)
        elif agent_type == "ParamNormAgent":
            return self._find_similar_param_norm(input_data)
        elif agent_type == "CodegenAgent":
            return self._find_similar_generation(input_data)
        
        return None
    
    def record_param_completion(self, query: str, components: List[Dict], 
                              original_params: Dict[str, Any], completed_params: Dict[str, Any]) -> None:
        """
        记录参数补全模式
        
        Args:
            query: 原始查询
            components: 选择的组件
            original_params: 原始参数
            completed_params: 补全后的参数
        """
        pattern = {
            "query_type": self._extract_query_type(query),
            "component_types": [comp.get("kind", "") for comp in components],
            "original_params": original_params.copy(),
            "completed_params": completed_params.copy(),
            "completion_added": set(completed_params.keys()) - set(original_params.keys()),
            "timestamp": datetime.now().isoformat()
        }
        self.param_completions.append(pattern)
    
    def record_param_normalization(self, task_card: Dict[str, Any], param_map: Dict[str, Any]) -> None:
        """
        记录参数标准化模式
        
        Args:
            task_card: 输入任务卡
            param_map: 输出参数映射
        """
        pattern = {
            "domain": task_card.get("domain", ""),
            "algorithm": task_card.get("algorithm", ""),
            "input_params": task_card.get("params", {}).copy(),
            "normalized_params": param_map.get("normalized_params", {}).copy(),
            "aliases": param_map.get("aliases", {}).copy(),
            "timestamp": datetime.now().isoformat()
        }
        self.param_normalizations.append(pattern)
    
    def record_component_success(self, task_card: Dict[str, Any], components: List[Dict[str, Any]]) -> None:
        """
        记录成功的组件组合
        
        Args:
            task_card: 任务卡
            components: 选择的组件
        """
        combination = {
            "domain": task_card.get("domain", ""),
            "algorithm": task_card.get("algorithm", ""),
            "component_names": [comp.get("name", "") for comp in components],
            "component_kinds": [comp.get("kind", "") for comp in components],
            "timestamp": datetime.now().isoformat()
        }
        self.component_combinations.append(combination)
    
    def record_missing_params(self, missing_params: List[str], components: List[Dict[str, Any]], 
                            context: str = "") -> None:
        """
        记录参数缺失案例
        
        Args:
            missing_params: 缺失的参数列表
            components: 相关组件
            context: 缺失的上下文信息
        """
        case = {
            "missing_params": missing_params.copy(),
            "components": [comp.get("name", "") for comp in components],
            "context": context,
            "timestamp": datetime.now().isoformat()
        }
        self.missing_param_cases.append(case)
    
    def find_param_completion_pattern(self, query: str, components: List[Dict]) -> Optional[Dict[str, Any]]:
        """
        查找相似的参数补全模式
        
        Args:
            query: 当前查询
            components: 当前组件
            
        Returns:
            相似的补全模式，或None
        """
        query_type = self._extract_query_type(query)
        component_types = [comp.get("kind", "") for comp in components]
        
        for pattern in self.param_completions:
            # 匹配查询类型和组件类型
            if (pattern["query_type"] == query_type and 
                set(pattern["component_types"]) == set(component_types)):
                return pattern
        
        return None
    
    def find_param_processing_pattern(self, query: str, components: List[Dict]) -> Optional[Dict[str, Any]]:
        """
        查找相似的参数处理模式 (合并版本)
        
        Args:
            query: 当前查询
            components: 当前组件
            
        Returns:
            相似的处理模式，或None
        """
        # 先查找参数补全模式，如果找不到则查找标准化模式
        completion_pattern = self.find_param_completion_pattern(query, components)
        if completion_pattern:
            return completion_pattern
        
        # 基于组件类型查找标准化模式
        component_types = [comp.get("kind", "") for comp in components]
        for pattern in self.param_normalizations:
            if set(pattern.get("component_types", [])) == set(component_types):
                return pattern
        
        return None
    
    def record_param_processing(self, query: str, components: List[Dict], 
                               original_params: Dict[str, Any], processed_result: Dict[str, Any]) -> None:
        """
        记录参数处理模式 (合并版本)
        
        Args:
            query: 查询内容
            components: 使用的组件
            original_params: 原始参数
            processed_result: 处理结果
        """
        # 记录到两个列表中以保持兼容性
        completion_record = {
            "query": query,
            "query_type": self._extract_query_type(query),
            "component_types": [comp.get("kind", "") for comp in components],
            "original_params": original_params,
            "completed_params": processed_result.get("normalized_params", {}),
            "timestamp": datetime.now().isoformat()
        }
        
        normalization_record = {
            "task_info": {"params": original_params, "query": query},
            "component_types": [comp.get("kind", "") for comp in components],
            "param_map": processed_result,
            "timestamp": datetime.now().isoformat()
        }
        
        self.param_completions.append(completion_record)
        self.param_normalizations.append(normalization_record)
        
        # 保持列表大小限制
        if len(self.param_completions) > 50:
            self.param_completions.pop(0)
        if len(self.param_normalizations) > 50:
            self.param_normalizations.pop(0)
    
    
    def find_param_normalization_pattern(self, task_card: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        查找相似的参数标准化模式
        
        Args:
            task_card: 当前任务卡
            
        Returns:
            相似的标准化模式，或None
        """
        domain = task_card.get("domain", "")
        algorithm = task_card.get("algorithm", "")
        
        for pattern in self.param_normalizations:
            if (pattern["domain"] == domain and 
                pattern["algorithm"] == algorithm):
                return pattern
        
        return None
    
    def get_memory_stats(self) -> Dict[str, int]:
        """
        获取Memory统计信息
        
        Returns:
            各类记忆的数量统计
        """
        return {
            "param_patterns": len(self.param_patterns),
            "param_completions": len(self.param_completions),  
            "param_normalizations": len(self.param_normalizations),
            "component_combinations": len(self.component_combinations),
            "successful_discoveries": len(self.successful_discoveries),
            "generation_patterns": len(self.generation_patterns),
            "validation_failures": len(self.validation_failures),
            "missing_param_cases": len(self.missing_param_cases)
        }
    
    def clear(self) -> None:
        """清空所有记忆（会话结束时调用）"""
        self.param_patterns.clear()
        self.param_completions.clear()
        self.param_normalizations.clear()
        self.component_combinations.clear()
        self.successful_discoveries.clear()
        self.generation_patterns.clear()
        self.validation_failures.clear()
        self.missing_param_cases.clear()
    
    # 私有辅助方法
    def _extract_query_type(self, query: str) -> str:
        """从查询中提取任务类型"""
        query_lower = query.lower()
        if "ising" in query_lower or "spin" in query_lower:
            return "SPIN_MODEL"
        elif "molecular" in query_lower or "molecule" in query_lower:
            return "molecular"
        elif "heisenberg" in query_lower:
            return "heisenberg"
        else:
            return "general"
    
    def _find_similar_discovery(self, input_data: Any) -> Optional[Any]:
        """查找相似的组件发现案例"""
        # 实现组件发现的相似性匹配逻辑
        for discovery in self.successful_discoveries:
            # 简单的相似性匹配（可以后续优化）
            if discovery["input"].get("domain") == input_data.get("domain"):
                return discovery["output"]
        return None
    
    def _find_similar_param_norm(self, input_data: Any) -> Optional[Any]:
        """查找相似的参数标准化案例"""
        for norm in self.param_normalizations:
            if (norm["domain"] == input_data.get("domain") and
                norm["algorithm"] == input_data.get("algorithm")):
                return norm["output"] 
        return None
    
    def _find_similar_generation(self, input_data: Any) -> Optional[Any]:
        """查找相似的代码生成案例"""
        for generation in self.successful_generations:
            # 基于组件组合匹配
            if generation["input"] == input_data:
                return generation["output"]
        return None


def create_agent_memory() -> AgentMemory:
    """
    创建新的AgentMemory实例
    
    Returns:
        AgentMemory实例
    """
    return AgentMemory()


# =============================================================================
# 测试代码
# =============================================================================

if __name__ == "__main__":
    print("🧪 Testing AgentMemory...")
    
    # 创建AgentMemory
    agent_memory = create_agent_memory()
    
    # 测试参数补全记录
    agent_memory.record_param_completion(
        "Spin system ground state energy",
        [{"kind": "hamiltonian"}, {"kind": "algorithm"}],
        {"J": 1.0, "h": 0.5},
        {"J": 1.0, "h": 0.5, "n": 8, "boundary": "periodic"}
    )
    
    # 测试统计
    stats = agent_memory.get_memory_stats()
    print(f"📊 Memory stats: {stats}")
    assert stats["param_completions"] == 1
    
    # 测试查找
    pattern = agent_memory.find_param_completion_pattern(
        "Spin system analysis",
        [{"kind": "hamiltonian"}, {"kind": "algorithm"}]
    )
    print(f"🔍 Found pattern: {pattern is not None}")
    
    print("✅ AgentMemory测试通过！")