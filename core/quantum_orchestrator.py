"""
Quantum Orchestrator - QuantumForge vNext

统一编排器，协调所有Agent的执行流程。
重构自 llm_engine.py，提供清晰的编排API。
"""

import asyncio
import os
from typing import Dict, Any, List, Optional
from openai import OpenAI, AsyncOpenAI
from dotenv import load_dotenv

from .semantic_agent import SemanticAgent
from .discovery_agent import DiscoveryAgent
from .param_processor_agent import ParamProcessorAgent
from .pipeline_agent import PipelineAgent
from .codegen_agent import CodegenAgent
from .agent_memory import create_agent_memory
from .execution_memory import Memory
from .cache_manager import create_cache_manager


class QuantumOrchestrator:
    """
    量子计算代码生成编排器
    
    管理所有Agent的协调和数据流：
    Query → SemanticAgent → DiscoveryAgent → ParamProcessorAgent → PipelineAgent → CodegenAgent → Code
    """
    
    def __init__(self, max_retries: int = 3):
        """
        初始化QuantumOrchestrator
        
        Args:
            max_retries: Agent最大重试次数
        """
        # 加载环境变量
        load_dotenv()
        self.api_key = os.getenv('OPENAI_API_KEY')
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required")
        
        self.max_retries = max_retries
        
        # 创建OpenAI客户端
        self.client = OpenAI(api_key=self.api_key)
        self.async_client = AsyncOpenAI(api_key=self.api_key)
        
        # 创建Memory和Cache系统
        self.agent_memory = create_agent_memory()  # Agent学习记忆
        self.code_memory = Memory()  # CodeCell存储
        self.cache_manager = create_cache_manager()  # 缓存管理器
        
        # 预加载Helper函数到缓存
        self._preload_helpers()
        
        # 初始化各个Agent
        self._setup_agents()
    
    def _preload_helpers(self):
        """预加载所有Helper函数到缓存"""
        try:
            import os
            # 获取项目根目录的绝对路径
            project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            helpers_dir = os.path.join(project_root, "components", "helpers")
            
            self.cache_manager.preload_all_helpers(helpers_dir)
            helper_count = len(self.cache_manager.get_all_helper_names())
            print(f"📦 预加载了 {helper_count} 个Helper函数到缓存")
        except Exception as e:
            print(f"⚠️ Helper预加载失败: {e}")
    
    def _setup_agents(self) -> None:
        """初始化所有Agent实例"""
        self.semantic_agent = SemanticAgent(self.client, self.async_client, self.max_retries)
        
        self.discovery_agent = DiscoveryAgent(
            self.client, self.async_client, self.max_retries, self.agent_memory
        )
        
        self.param_processor_agent = ParamProcessorAgent(
            self.client, self.async_client, self.max_retries, self.agent_memory
        )
        
        self.pipeline_agent = PipelineAgent(self.client, self.async_client, self.max_retries)
        
        self.codegen_agent = CodegenAgent(
            self.client, self.async_client, self.max_retries, 
            self.agent_memory, self.code_memory, self.cache_manager
        )
        
    
    def generate_quantum_code(self, query: str, registry_data: List[Dict[str, Any]]) -> str:
        """
        完整的量子代码生成流程
        
        Args:
            query: 用户自然语言查询
            registry_data: 组件注册表
            
        Returns:
            完整的Python源码字符串
        """
        try:
            print(f"🎯 开始处理查询: {query}")
            
            # 步骤1: 语义解析
            print("📋 步骤1: 语义解析...")
            task_card = self.semantic_agent.process(query)
            print(f"✅ TaskCard: {task_card}")
            
            # 步骤2: 组件发现
            print("🔍 步骤2: 组件发现...")
            components = self.discovery_agent.process(task_card, registry_data)
            print(f"✅ Selected {len(components)} components")
            
            # 步骤3: 参数处理 (补全+标准化)
            print("🧠 步骤3: 参数处理...")
            param_map = self.param_processor_agent.process(query, task_card, components)
            print(f"✅ Processed {len(param_map.get('normalized_params', {}))} parameters")
            
            # 步骤4: 流水线计划
            print("⚙️ 步骤4: 流水线计划...")
            pipeline_plan = self.pipeline_agent.process(task_card, components, param_map)
            print(f"✅ Pipeline order: {pipeline_plan.get('execution_order', [])}")
            
            # 步骤5: 准备helper函数信息
            print("📚 步骤5: 准备helper函数...")
            # 从缓存获取helper函数名列表，而不是加载完整源码
            helper_names = []
            for comp in components:
                if "helper_function" in comp:
                    helper_names.append(comp["helper_function"])
            print(f"✅ 准备了 {len(helper_names)} 个helper函数引用")
            
            component_imports = []
            for component in components:
                if "imports" in component:
                    if isinstance(component["imports"], list):
                        component_imports.extend(component["imports"])
                    else:
                        component_imports.append(component["imports"])
            print(f"✅ 准备了 {len(helper_names)} 个helper函数引用和 {len(component_imports)} 个导入")
            
            # 步骤6: 加载helper函数源码
            print("📚 步骤6: 加载helper函数...")
            # 从缓存获取helper函数源码
            helper_sources = {}
            for helper_name in helper_names:
                if self.cache_manager:
                    source = self.cache_manager.get_cached_helper_source(helper_name)
                    if source:
                        helper_sources[helper_name] = source
            print(f"✅ 从缓存加载了 {len(helper_sources)} 个helper函数")
            
            # 步骤7: 代码生成
            print("🏗️ 步骤7: 代码生成...")
            final_code = self.codegen_agent.process(
                pipeline_plan, components, param_map, helper_sources, component_imports
            )
            print(f"✅ Generated {len(final_code)} characters of Python code")
            
            return final_code
            
        except Exception as e:
            print(f"❌ 编排失败: {str(e)}")
            raise RuntimeError(f"QuantumOrchestrator处理失败: {str(e)}")
    
    async def generate_quantum_code_parallel(self, query: str, registry_data: List[Dict[str, Any]], 
                                           helper_sources: Dict[str, str], component_imports: List[str]) -> List[Dict[str, Any]]:
        """
        并行优化的量子代码生成流程
        
        Args:
            query: 用户自然语言查询
            registry_data: 组件注册表
            helper_sources: 辅助函数源码
            component_imports: 组件导入列表
            
        Returns:
            CodeCells列表
        """
        try:
            print(f"🎯 开始并行处理查询: {query}")
            
            # 步骤1: 语义解析
            print("📋 步骤1: 语义解析...")
            task_card = self.semantic_agent.process(query)
            print(f"✅ TaskCard: {task_card}")
            
            # 步骤2&3: 并行组件发现和初步参数标准化
            print("🔍⚡ 步骤2&3: 并行执行...")
            discovery_task = self.discovery_agent.process_async(task_card, registry_data)
            param_map_task = self.param_processor_agent.process_async(query, task_card, components)
            
            components, initial_param_map = await asyncio.gather(
                discovery_task, param_norm_task, return_exceptions=True
            )
            
            if isinstance(components, Exception):
                raise RuntimeError(f"组件发现并行执行失败: {components}")
            if isinstance(initial_param_map, Exception):
                raise RuntimeError(f"参数归一化并行执行失败: {initial_param_map}")
            
            print(f"✅ Parallel: {len(components)} components, initial params normalized")
            
            # 步骤4: 完整参数标准化（基于组件）
            print("🔧 步骤4: 完整参数标准化...")
            param_map = await param_map_task
            print(f"✅ Normalized {len(param_map.get('normalized_params', {}))} parameters")
            
            # 步骤5: 流水线计划
            print("⚙️ 步骤5: 流水线计划...")
            pipeline_plan = self.pipeline_agent.process(task_card, components, param_map)
            print(f"✅ Pipeline order: {pipeline_plan.get('execution_order', [])}")
            
            # 步骤6: 代码生成
            print("🏗️ 步骤6: 代码生成...")
            code_cells = self.codegen_agent.process(
                pipeline_plan, components, param_map, helper_sources, component_imports
            )
            print(f"✅ Generated {len(code_cells)} CodeCells")
            
            return code_cells
            
        except Exception as e:
            print(f"❌ 并行编排失败: {str(e)}")
            raise RuntimeError(f"QuantumOrchestrator并行处理失败: {str(e)}")
    
    def get_agent_stats(self) -> Dict[str, Any]:
        """获取所有Agent统计信息"""
        return {
            "api_key_configured": bool(self.api_key),
            "max_retries": self.max_retries,
            "parallel_support": True,
            "agents": {
                "semantic": "SemanticAgent",
                "discovery": "DiscoveryAgent",
                "param_processor": "ParamProcessorAgent",
                "pipeline": "PipelineAgent",
                "codegen": "CodegenAgent"
            },
            "memory_stats": self.agent_memory.get_memory_stats(),
            "code_memory_cells": len(self.code_memory._cells) if self.code_memory else 0
        }
    
    def clear_session_memory(self) -> None:
        """清空会话内存"""
        self.agent_memory.clear()
        self.code_memory = Memory()  # 重新创建空的CodeCell存储
        print("🧹 Session memory cleared")
    
    # =============================================================================
    # 兼容原LLMEngine接口的方法
    # =============================================================================
    
    def complete_parameters(self, query: str, task_card: Dict[str, Any], required_params: Dict[str, Any]) -> Dict[str, Any]:
        """
        参数补全（兼容原LLMEngine接口）
        
        Args:
            query: 原始查询
            task_card: 任务卡
            required_params: 所需参数规格
            
        Returns:
            补全后的任务卡
        """
        # 转换required_params为components格式用于ParamCompletionAgent
        mock_components = [{"params_schema": required_params}]
        
        param_map = self.param_processor_agent.process(query, task_card, mock_components)
        return {"completed_params": param_map.get("normalized_params", {})}
    
    def generate_codecells(self, pipeline_plan: Dict[str, Any], components: List[Dict[str, Any]], param_map: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        代码生成（兼容原LLMEngine接口）
        
        Args:
            pipeline_plan: 管道计划
            components: 组件列表
            param_map: 参数映射
            
        Returns:
            CodeCells列表
        """
        # 需要helper_sources和component_imports，从现有数据推断
        helper_sources = {}
        component_imports = []
        
        # 加载helper函数源码
        try:
            from .helper_loader import load_helpers_for_components
            helper_sources = load_helpers_for_components(components)
        except ImportError:
            print("⚠️ helper_loader不可用，helper_sources为空")
        
        # 从组件中提取导入信息
        for component in components:
            if "imports" in component:
                if isinstance(component["imports"], list):
                    component_imports.extend(component["imports"])
                else:
                    component_imports.append(component["imports"])
        
        return self.codegen_agent.process(
            pipeline_plan, components, param_map, helper_sources, component_imports
        )


def create_engine(api_key: Optional[str] = None, max_retries: int = 3) -> QuantumOrchestrator:
    """
    创建量子编排器实例（兼容原LLMEngine接口）
    
    Args:
        api_key: OpenAI API密钥（可选，会从环境变量读取）
        max_retries: 最大重试次数
        
    Returns:
        QuantumOrchestrator实例
    """
    if api_key:
        # 如果提供了api_key，临时设置环境变量
        import os
        os.environ['OPENAI_API_KEY'] = api_key
    
    return QuantumOrchestrator(max_retries=max_retries)