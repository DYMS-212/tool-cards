"""
Agent性能监控模块 - QuantumForge vNext

提供Agent调用时间和token消耗的详细监控功能。
用于模型对比和性能分析。
"""

import time
import json
import uuid
from functools import wraps
from typing import Dict, Any, Callable
from datetime import datetime


class AgentMetrics:
    """Agent性能指标数据类"""
    
    def __init__(self, agent_name: str):
        self.agent_name = agent_name
        self.input_tokens = 0
        self.output_tokens = 0
        self.call_time = 0.0
        self.model = ""
        self.start_time = None
        self.end_time = None
    
    def start_timing(self):
        """开始计时"""
        self.start_time = time.time()
    
    def end_timing(self):
        """结束计时并计算耗时"""
        if self.start_time:
            self.end_time = time.time()
            self.call_time = self.end_time - self.start_time
    
    def set_tokens(self, input_tokens: int, output_tokens: int):
        """设置token消耗"""
        self.input_tokens = input_tokens
        self.output_tokens = output_tokens
    
    def set_model(self, model: str):
        """设置使用的模型"""
        self.model = model
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "total_tokens": self.input_tokens + self.output_tokens,
            "call_time": round(self.call_time, 3),
            "model": self.model
        }


class PerformanceMonitor:
    """性能监控器"""
    
    def __init__(self):
        self.query_id = str(uuid.uuid4())
        self.query = ""
        self.agents = {}
        self.start_time = None
        self.end_time = None
    
    def start_query(self, query: str):
        """开始监控一次查询"""
        self.query_id = str(uuid.uuid4())
        self.query = query
        self.agents = {}
        self.start_time = time.time()
    
    def end_query(self):
        """结束查询监控"""
        self.end_time = time.time()
    
    def get_agent_metrics(self, agent_name: str) -> AgentMetrics:
        """获取或创建Agent指标对象"""
        if agent_name not in self.agents:
            self.agents[agent_name] = AgentMetrics(agent_name)
        return self.agents[agent_name]
    
    def get_total_metrics(self) -> Dict[str, Any]:
        """获取总体指标"""
        total_input = sum(metrics.input_tokens for metrics in self.agents.values())
        total_output = sum(metrics.output_tokens for metrics in self.agents.values())
        total_time = sum(metrics.call_time for metrics in self.agents.values())
        
        return {
            "total_input_tokens": total_input,
            "total_output_tokens": total_output,
            "total_tokens": total_input + total_output,
            "total_agent_time": round(total_time, 3),
            "total_query_time": round(self.end_time - self.start_time, 3) if self.end_time else 0.0,
            "agent_count": len(self.agents)
        }
    
    def export_metrics(self) -> Dict[str, Any]:
        """导出完整的性能指标"""
        agent_data = {}
        for agent_name, metrics in self.agents.items():
            agent_data[agent_name] = metrics.to_dict()
        
        return {
            "query_id": self.query_id,
            "query": self.query,
            "timestamp": datetime.now().isoformat(),
            "agents": agent_data,
            "totals": self.get_total_metrics()
        }


# 全局监控器实例
_global_monitor = PerformanceMonitor()


def get_monitor() -> PerformanceMonitor:
    """获取全局监控器实例"""
    return _global_monitor


def agent_monitor(agent_name: str):
    """
    Agent性能监控装饰器
    
    Args:
        agent_name: Agent名称
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            monitor = get_monitor()
            metrics = monitor.get_agent_metrics(agent_name)
            
            # 开始计时
            metrics.start_timing()
            
            try:
                # 调用原始函数
                result = func(*args, **kwargs)
                
                # 结束计时
                metrics.end_timing()
                
                # 尝试从结果中提取token信息（如果可用）
                if isinstance(result, dict) and "usage" in result:
                    usage = result["usage"]
                    metrics.set_tokens(
                        usage.get("prompt_tokens", 0),
                        usage.get("completion_tokens", 0)
                    )
                
                return result
                
            except Exception as e:
                # 即使出错也要记录时间
                metrics.end_timing()
                raise e
        
        return wrapper
    return decorator


def estimate_tokens(text: str) -> int:
    """
    估算文本的token数量
    简单估算：1 token ≈ 4 characters (for GPT models)
    """
    return len(text) // 4


def record_agent_call(agent_name: str, input_text: str, output_text: str, call_time: float, model: str = "gpt-4"):
    """
    手动记录Agent调用数据
    
    Args:
        agent_name: Agent名称
        input_text: 输入文本
        output_text: 输出文本
        call_time: 调用时间（秒）
        model: 使用的模型名称
    """
    monitor = get_monitor()
    metrics = monitor.get_agent_metrics(agent_name)
    
    # 估算token消耗
    input_tokens = estimate_tokens(input_text)
    output_tokens = estimate_tokens(output_text)
    
    # 记录数据
    metrics.set_tokens(input_tokens, output_tokens)
    metrics.call_time = call_time
    metrics.set_model(model)


# =============================================================================
# 测试代码
# =============================================================================

if __name__ == "__main__":
    print("🧪 测试性能监控系统...")
    
    # 模拟监控
    monitor = get_monitor()
    monitor.start_query("测试查询")
    
    # 模拟Agent调用
    record_agent_call("SemanticAgent", "分析这个查询", "任务卡结果", 1.5, "gpt-4")
    record_agent_call("DiscoveryAgent", "发现组件", "组件列表", 2.3, "gpt-4")
    record_agent_call("CodegenAgent", "生成代码", "Python代码", 3.8, "gpt-4")
    
    monitor.end_query()
    
    # 导出结果
    metrics = monitor.export_metrics()
    print("\n📊 性能指标:")
    print(json.dumps(metrics, ensure_ascii=False, indent=2))
    
    print("\n✅ 性能监控测试完成！")