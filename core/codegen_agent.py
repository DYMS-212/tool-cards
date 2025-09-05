"""
Code Generation Agent - QuantumForge vNext

代码生成Agent，负责将组件和参数转换为可执行的Python代码。
从 llm_engine.py 重构而来，具备学习和记忆能力。
"""

import json
import time
from typing import Dict, Any, List
from openai import OpenAI, AsyncOpenAI
from .base_agent import AgentWithMemory


class CodegenAgent(AgentWithMemory):
    """
    代码生成Agent
    
    功能：
    - 生成CodeCell列表
    - 学习和记忆代码生成模式
    - 需要访问Memory存储CodeCell
    """
    
    def __init__(self, client: OpenAI, async_client: AsyncOpenAI = None, max_retries: int = 3, agent_memory=None, code_memory=None, cache_manager=None):
        """
        初始化CodegenAgent
        
        Args:
            client: OpenAI客户端
            async_client: 异步客户端
            max_retries: 最大重试次数
            agent_memory: Agent学习记忆
            code_memory: CodeCell存储Memory
        """
        super().__init__(client, async_client, max_retries, agent_memory)
        self.code_memory = code_memory
        self.cache_manager = cache_manager
    
    def _get_prompt(self) -> str:
        """获取CodegenAgent的prompt模板"""
        return """You are a professional Python code generation agent. Transform PipelinePlan, ComponentCards, and ParamMap into clean, well-structured Python source code.

RESPONSE FORMAT: Return ONLY pure Python source code with no markdown code blocks, explanations, or additional text.

REQUIRED OUTPUT STRUCTURE:
1. All import statements (merged and deduplicated)
2. All helper function definitions (complete source code)
3. Main function with proper structure:
   - Parameter definitions
   - Component creation calls
   - Final execution and output
   - Return statement
4. if __name__ == "__main__": main() pattern

CRITICAL FORMATTING RULES:
- NO duplicate imports or function calls
- NO scattered imports between functions
- NO parameter redefinitions
- Proper main() function structure with clear sections
- Clean separation: imports → functions → main → entry point

IMPORT RULES - CRITICAL:
- Use ONLY imports from ComponentImports list provided in user message
- Do NOT add any other imports, even if they seem related to quantum computing
- Do NOT add qiskit_nature imports unless they appear in ComponentImports
- ComponentImports contains the complete and exclusive import list

HELPER FUNCTION RULES:
- Use complete helper function source code from HelperSources
- Use the exact helper_function name from each component's schema
- Copy the complete function implementation, not just signatures

COMPONENT CREATION RULES:
- Use normalized_params from ParamMap as actual parameter names
- Create component instances using helper functions
- Follow execution_order from PipelinePlan
- CRITICAL: Use ALL created component instances in algorithm execution
- NEVER skip or omit required parameters from component APIs

COMPONENT DEPENDENCY RULES - CRITICAL:
- Algorithm components depend on ALL previously created components
- Use ALL created component instances in algorithm execution
- Follow this pattern: Hamiltonian → Optimizer → Circuit → Backend → Algorithm
- Algorithm component receives instances: algorithm_instance = Algorithm(component1, component2, ...)
- Never omit required component dependencies

COMPONENT TYPE MAPPING:
- Hamiltonian → Variable assignment (H = build_hamiltonian(...))  
- Optimizer → Instance creation (optimizer = OptimizerClass(...))
- Circuit/Ansatz → Instance creation (ansatz = create_circuit(...))
- Backend/Estimator → Instance creation (estimator = BackendClass(...))
- Algorithm → Uses ALL above components as arguments

COMPONENT USAGE PATTERNS BY TYPE:

HAMILTONIAN COMPONENTS:
- Create variable: `variable_name = helper_function(params...)`
- Use in algorithm: Pass as first argument to algorithm component

CIRCUIT/ANSATZ COMPONENTS:
- Create variable: `variable_name = helper_function(params...)`
- Use in algorithm: Pass as ansatz/circuit parameter to algorithm component

OPTIMIZER COMPONENTS:
- Create instance: `variable_name = OptimizerClass(params...)`
- Use in algorithm: Pass as optimizer parameter to algorithm component

BACKEND/ESTIMATOR COMPONENTS:
- Create instance: `variable_name = BackendClass(params...)`
- Use in algorithm: Pass as estimator/backend parameter to algorithm component

ALGORITHM COMPONENTS:
- Must use ALL previous components as dependencies
- Call pattern: `result = algorithm_helper_function(all_required_components, algorithm_params)`
- Follow component's invoke_template exactly as specified

UNIVERSAL COMPONENT INTEGRATION RULE:
- Algorithm components MUST use ALL created component instances
- Never skip any component created in the pipeline
- Follow the execution_order from PipelinePlan
- Use component.invoke_template for correct parameter passing pattern

CRITICAL: You must respond with ONLY the complete Python source code, no explanatory text before or after."""
    
    def process(self, pipeline_plan: Dict[str, Any], components: List[Dict[str, Any]], 
                param_map: Dict[str, Any], helper_sources: Dict[str, str], component_imports: List[str]) -> str:
        """
        生成完整Python源码
        
        Args:
            pipeline_plan: 执行计划
            components: 组件列表
            param_map: 参数映射
            helper_sources: 辅助函数源码
            component_imports: 组件导入列表
            
        Returns:
            完整的Python源码字符串
        """
        # 检查是否有相似的代码生成案例
        if self._has_memory():
            similar_case = self._find_similar_case({
                "components": [comp.get("name", "") for comp in components],
                "algorithm": param_map.get("algorithm")
            })
            if similar_case:
                print("🧠 Found similar code generation case")
        
        # 分析组件依赖关系
        component_dependencies = self._analyze_component_dependencies(components, pipeline_plan)
        
        # 准备用户消息
        user_message = f"""
PipelinePlan: {json.dumps(pipeline_plan, ensure_ascii=False)}

ComponentCards: {json.dumps(components, ensure_ascii=False)}

ParamMap: {json.dumps(param_map, ensure_ascii=False)}

HelperSources:
{json.dumps(helper_sources, ensure_ascii=False)}

ComponentImports: {json.dumps(component_imports, ensure_ascii=False)}

ComponentDependencies: {json.dumps(component_dependencies, ensure_ascii=False)}

Please generate complete Python source code following the execution order.
CRITICAL: Algorithm components must use ALL previously created component instances.
Use ComponentDependencies to ensure correct component usage patterns.
Copy complete helper function implementations from HelperSources."""
        
        try:
            result = self._call_with_retry(user_message, "CodegenAgent")
            
            # CodegenAgent现在返回Python代码字符串，不是JSON
            if isinstance(result, str) and result.strip():
                # 记录成功的代码生成案例
                if self._has_memory():
                    self._record_success(
                        input_data={
                            "components": [comp.get("name", "") for comp in components],
                            "algorithm": param_map.get("normalized_params", {}).get("algorithm")
                        },
                        output_data={"code": result}
                    )
                
                return result
            else:
                raise ValueError("CodegenAgent返回的格式不正确")
                
        except Exception as e:
            raise RuntimeError(f"CodegenAgent处理失败: {str(e)}")
    
    def process_with_cache(self, pipeline_plan: Dict[str, Any], components: List[Dict[str, Any]], 
                          param_map: Dict[str, Any], helper_names: List[str], component_imports: List[str]) -> str:
        """
        使用invoke_template生成代码 (Token优化版本)
        
        Args:
            pipeline_plan: 执行计划
            components: 组件列表
            param_map: 参数映射
            helper_names: Helper函数名列表
            component_imports: 组件导入列表
            
        Returns:
            完整的Python源码字符串
        """
        # 提取invoke_template信息，而不是完整源码
        invoke_templates = {}
        function_descriptions = {}
        
        for comp in components:
            if "helper_function" in comp and "invoke_template" in comp:
                func_name = comp["helper_function"]
                invoke_templates[func_name] = comp["invoke_template"]
                function_descriptions[func_name] = comp.get("description", "")
        
        # 使用轻量级的template-based生成
        return self._pipeline_driven_assembly(pipeline_plan, components, param_map, helper_names, component_imports)
    
    def _pipeline_driven_assembly(self, pipeline_plan: Dict[str, Any], components: List[Dict[str, Any]], 
                                 param_map: Dict[str, Any], helper_names: List[str], component_imports: List[str]) -> str:
        """
        基于Pipeline的动态代码组装 - 完全数据驱动，无硬编码
        """
        execution_order = pipeline_plan.get("execution_order", [])
        normalized_params = param_map.get("normalized_params", {})
        
        # 第一步：从缓存获取需要的helper函数
        helper_sources_from_cache = {}
        for helper_name in helper_names:
            if self.cache_manager:
                source = self.cache_manager.get_cached_helper_source(helper_name)
                if source:
                    helper_sources_from_cache[helper_name] = source
        
        # 第二步：让LLM基于pipeline动态组装，但传递轻量级数据
        lightweight_prompt = self._get_lightweight_assembly_prompt()
        
        user_message = f"""
PipelinePlan: {json.dumps(pipeline_plan, ensure_ascii=False)}

Components: {json.dumps(components, ensure_ascii=False)}

ParamMap: {json.dumps(param_map, ensure_ascii=False)}

AvailableHelperFunctions: {json.dumps(list(helper_sources_from_cache.keys()), ensure_ascii=False)}

ComponentImports: {json.dumps(component_imports, ensure_ascii=False)}

Please generate complete Python code by following the pipeline execution order and using invoke_template patterns."""
        
        try:
            response = self._call_openai(lightweight_prompt, user_message, "CodegenAgent-Assembly")
            result = response.strip()
            if result.startswith("```python"):
                result = result.replace("```python", "").replace("```", "").strip()
            
            # 后处理：添加需要的helper函数定义
            final_code = self._post_process_with_helpers(result, helper_sources_from_cache)
            
            return final_code
            
        except Exception as e:
            raise RuntimeError(f"CodegenAgent动态组装失败: {str(e)}")
    
    def _get_lightweight_assembly_prompt(self) -> str:
        """轻量级动态组装prompt - 无硬编码"""
        return """You are a quantum code assembler. Generate complete Python code using pipeline execution order and invoke templates.

DYNAMIC ASSEMBLY STRATEGY:
1. Follow PipelinePlan.execution_order EXACTLY for component creation sequence
2. Use each component's invoke_template to generate the correct function call
3. Create appropriate variable names based on component context and dependencies
4. Generate a main() function that executes the pipeline in correct order
5. Include necessary imports and ensure code is ready-to-run

TEMPLATE USAGE:
- Each component has an invoke_template showing exact usage pattern
- Replace template variables with appropriate names and parameter values
- Ensure dependencies between components are properly handled
- Generate variable names that reflect component purpose and pipeline flow

OUTPUT: Complete Python source code with main() function that executes the full pipeline."""
    
    def _post_process_with_helpers(self, generated_code: str, helper_sources: Dict[str, str]) -> str:
        """后处理：动态添加需要的helper函数定义"""
        import re
        
        # 分析生成代码中调用的函数
        function_calls = re.findall(r'([a-zA-Z_][a-zA-Z0-9_]*)\s*\(', generated_code)
        used_helpers = set(function_calls) & set(helper_sources.keys())
        
        # 提取需要的helper函数定义
        helper_definitions = []
        for helper_name in used_helpers:
            if helper_name in helper_sources:
                source = helper_sources[helper_name]
                # 提取函数定义（去除imports和其他内容）
                function_defs = self._extract_function_definitions(source)
                helper_definitions.extend(function_defs)
        
        if helper_definitions:
            # 在imports后添加helper函数定义
            lines = generated_code.split('\n')
            import_end = 0
            for i, line in enumerate(lines):
                if line.strip() and not line.startswith('import ') and not line.startswith('from '):
                    import_end = i
                    break
            
            # 插入helper函数定义
            final_lines = (
                lines[:import_end] +
                [''] + 
                helper_definitions + 
                [''] + 
                lines[import_end:]
            )
            return '\n'.join(final_lines)
        
        return generated_code
    
    def _extract_function_definitions(self, source_code: str) -> List[str]:
        """从源码中提取函数定义"""
        import re
        
        # 匹配函数定义
        function_pattern = r'^def\s+[a-zA-Z_][a-zA-Z0-9_]*\s*\([^)]*\):.*?(?=^def\s|^class\s|^$|\Z)'
        matches = re.findall(function_pattern, source_code, re.MULTILINE | re.DOTALL)
        
        cleaned_functions = []
        for match in matches:
            # 清理函数定义
            lines = match.strip().split('\n')
            cleaned_lines = [line for line in lines if not line.strip().startswith('#') or 'def ' in line]
            if cleaned_lines:
                cleaned_functions.append('\n'.join(cleaned_lines))
        
        return cleaned_functions
    
    def _generate_imports(self, components: List[Dict[str, Any]], component_imports: List[str]) -> str:
        """生成导入语句"""
        imports = set(component_imports)
        
        # 添加基础导入
        imports.add("import numpy as np")
        
        return "\\n".join(sorted(imports))
    
    def _process_with_templates(self, pipeline_plan: Dict[str, Any], components: List[Dict[str, Any]],
                               param_map: Dict[str, Any], invoke_templates: Dict[str, str], 
                               function_descriptions: Dict[str, str], component_imports: List[str]) -> str:
        """
        基于invoke_template生成代码 (Token优化版本)
        """
        # 检查是否有相似的代码生成案例
        if self._has_memory():
            similar_case = self._find_similar_case({
                "components": [comp.get("name", "") for comp in components],
                "algorithm": pipeline_plan.get("execution_order", [])
            })
            if similar_case:
                print("🧠 Found similar code generation case")

        # 优化的prompt - 使用invoke_template而不是完整源码
        template_prompt = self._get_template_prompt()
        
        user_message = f"""
PipelinePlan: {json.dumps(pipeline_plan, ensure_ascii=False)}

Components: {json.dumps(components, ensure_ascii=False)}

ParamMap: {json.dumps(param_map, ensure_ascii=False)}

Function Templates: {json.dumps(invoke_templates, ensure_ascii=False)}

Function Descriptions: {json.dumps(function_descriptions, ensure_ascii=False)}

Component Imports: {json.dumps(component_imports, ensure_ascii=False)}

Generate complete Python code using the provided templates and component information."""

        try:
            # 使用template-specific prompt
            response = self._call_openai(template_prompt, user_message, "CodegenAgent-Template")
            result = response.strip()
            if result.startswith("```python"):
                result = result.replace("```python", "").replace("```", "").strip()
            
            # 记录成功的代码生成案例
            if self._has_memory():
                self._record_success({
                    "pipeline_plan": pipeline_plan,
                    "components": [comp.get("name", "") for comp in components],
                    "param_count": len(param_map.get("normalized_params", {}))
                }, result)

            return result
            
        except Exception as e:
            raise RuntimeError(f"CodegenAgent模板处理失败: {str(e)}")
    
    def _get_template_prompt(self) -> str:
        """获取基于template的优化prompt"""
        return """You are a Python code generator. Use provided invoke templates and component information to generate clean, executable Python code.

INPUT DATA:
- PipelinePlan: Execution sequence and component dependencies
- Components: Component specifications with metadata
- ParamMap: Normalized parameters with proper types
- Function Templates: Exact usage patterns for each helper function
- Function Descriptions: Brief descriptions of helper function purposes  
- Component Imports: Required import statements

GENERATION STRATEGY:
1. Use invoke templates EXACTLY as provided - they show correct function usage patterns
2. Replace template variables ({var}, {params}) with appropriate values from ParamMap
3. Follow pipeline execution order for component creation sequence
4. Ensure all components are properly connected and used

TEMPLATE USAGE:
- invoke_template: "{var}_H = build_heisenberg_h(n, Jx, Jy, Jz)" 
- Replace {var} with appropriate variable name
- Replace parameters with values from ParamMap.normalized_params
- Generate: "hamiltonian = build_heisenberg_h(8, 1.0, 1.0, 1.0)"

OUTPUT: Complete Python source code ready for execution."""
    
    def _call_with_retry(self, user_message: str, agent_name: str) -> str:
        """
        重写父类方法，因为CodegenAgent现在返回字符串而不是JSON
        """
        for attempt in range(self.max_retries):
            try:
                response = self._call_openai(self.prompt, user_message, agent_name)
                # CodegenAgent返回Python代码字符串，清理markdown代码块
                cleaned_response = response.strip()
                if cleaned_response.startswith("```python"):
                    cleaned_response = cleaned_response.replace("```python", "").replace("```", "").strip()
                return cleaned_response
            except Exception as e:
                if attempt == self.max_retries - 1:
                    raise RuntimeError(f"{agent_name} failed after {self.max_retries} retries: {str(e)}")
                
                print(f"⚠️ {agent_name} retry {attempt + 1}/{self.max_retries}: {str(e)}")
                time.sleep(0.5)
    
    def _analyze_component_dependencies(self, components: List[Dict[str, Any]], pipeline_plan: Dict[str, Any]) -> Dict[str, Any]:
        """
        分析组件间的依赖关系
        
        Args:
            components: 组件列表
            pipeline_plan: 执行计划
            
        Returns:
            组件依赖关系映射
        """
        execution_order = pipeline_plan.get("execution_order", [])
        dependencies = {}
        component_types = {}
        
        # 分析每个组件的类型
        for component in components:
            name = component.get("name", "")
            if "Hamiltonian" in name:
                component_types[name] = "hamiltonian"
            elif "Optimizer" in name:
                component_types[name] = "optimizer"
            elif "Circuit" in name or "Ansatz" in name:
                component_types[name] = "circuit"
            elif "Backend" in name or "Estimator" in name:
                component_types[name] = "backend"
            elif "Algorithm" in name:
                component_types[name] = "algorithm"
        
        # 为Algorithm组件建立依赖关系
        algorithm_components = [name for name, type_ in component_types.items() if type_ == "algorithm"]
        
        for algo_name in algorithm_components:
            # Algorithm依赖所有非Algorithm组件
            algo_deps = []
            for comp_name in execution_order:
                if comp_name != algo_name and comp_name in component_types:
                    comp_type = component_types[comp_name]
                    algo_deps.append({
                        "name": comp_name,
                        "type": comp_type,
                        "variable": self._get_variable_name(comp_name, comp_type)
                    })
            
            dependencies[algo_name] = {
                "type": "algorithm",
                "requires": algo_deps,
                "usage_pattern": f"algorithm = {algo_name.split('.')[-1]}({', '.join([f'{dep['type']}={dep['variable']}' for dep in algo_deps])})"
            }
        
        return {
            "component_types": component_types,
            "algorithm_dependencies": dependencies,
            "execution_order": execution_order
        }
    
    def _get_variable_name(self, component_name: str, component_type: str) -> str:
        """根据组件类型生成变量名"""
        type_mapping = {
            "hamiltonian": "H",
            "optimizer": "optimizer", 
            "circuit": "ansatz",
            "backend": "estimator",
            "algorithm": "algorithm"
        }
        return type_mapping.get(component_type, component_name.lower())
