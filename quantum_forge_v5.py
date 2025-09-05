"""
QuantumForge vNext - 主入口

量子算法代码生成框架的统一入口点。
基于5-Agent架构，将自然语言查询转换为完整的Python量子计算代码。
"""

import time
from typing import Dict, Any
from core.quantum_orchestrator import create_engine
from core.registry_loader import load_registry
from core.performance_monitor import get_monitor


def run(query: str, debug=False, max_retries: int = 3, experiment_config: Dict[str, Any] = None) -> str:
    """
    QuantumForge vNext主入口 - 自然语言查询到Python代码的完整转换
    
    Args:
        query: 用户自然语言查询（中文/英文）
        debug: 调试配置 - bool(开关) 或 dict{"steps": bool, "agents": bool, "performance": bool}
        max_retries: Agent重试次数（默认3次）
        experiment_config: 实验配置（用于消融实验）
        
    Returns:
        完整的Python量子计算源码字符串
        
    Raises:
        ValueError: 查询格式无效
        RuntimeError: Agent处理失败
    """
    start_time = time.time()
    
    # 处理调试配置
    if isinstance(debug, bool):
        debug_config = {"steps": debug, "agents": False, "performance": debug}
    else:
        debug_config = {
            "steps": debug.get("steps", False),
            "agents": debug.get("agents", False),
            "performance": debug.get("performance", False)
        }
    
    # 初始化性能监控
    monitor = get_monitor()
    monitor.start_query(query)
    
    if debug_config["steps"]:
        print("🚀 QuantumForge vNext 启动")
        print(f"📝 查询: {query}")
    
    try:
        # 创建QuantumOrchestrator并直接使用其完整流程
        engine = create_engine(max_retries=max_retries)
        
        # 加载组件注册表和helper源码
        registry_data = load_registry()
        
        # 使用QuantumOrchestrator的统一接口（包含所有步骤1-7）
        if debug_config["steps"]:
            print("\n🎯 执行完整代码生成流程...")
        
        final_code = engine.generate_quantum_code(query, registry_data)
        
        # 计算执行时间
        execution_time = time.time() - start_time
        
        # 结束性能监控
        monitor.end_query()
        
        if debug_config["steps"]:
            print(f"\n✅ 代码生成完成!")
            print(f"⏱️ 执行时间: {execution_time:.2f}秒")
            print(f"📏 代码长度: {len(final_code)}字符")
            
        if debug_config["performance"]:
            # 显示Agent性能统计
            metrics = monitor.export_metrics()
            print(f"\n📊 Agent性能统计:")
            for agent_name, agent_metrics in metrics["agents"].items():
                print(f"  {agent_name}: {agent_metrics['input_tokens']}+{agent_metrics['output_tokens']}={agent_metrics['total_tokens']}tokens, {agent_metrics['call_time']}s")
            totals = metrics["totals"]
            print(f"  总计: {totals['total_tokens']}tokens, {totals['total_agent_time']}s")
        
        return final_code
    
    except Exception as e:
        execution_time = time.time() - start_time
        error_msg = f"QuantumForge处理失败 (耗时{execution_time:.2f}s): {str(e)}"
        
        if debug_config["steps"]:
            print(f"❌ {error_msg}")
        
        raise RuntimeError(error_msg) from e


def run_and_save(query: str, output_file: str = None, debug=True, max_retries: int = 3) -> str:
    """
    运行查询并保存结果到文件
    
    Args:
        query: 用户查询
        output_file: 输出文件名（可选，默认自动生成）
        debug: 调试配置 - bool(开关) 或 dict{"steps": bool, "agents": bool, "performance": bool}
        max_retries: Agent重试次数（默认3次）
        
    Returns:
        生成的代码内容
    """
    # 处理调试配置
    if isinstance(debug, bool):
        debug_config = {"steps": debug, "agents": False, "performance": debug}
    else:
        debug_config = debug
    
    # 生成代码
    code = run(query, debug=debug, max_retries=max_retries)
    
    # 确定输出文件名
    if not output_file:
        import re
        from datetime import datetime
        
        # 从查询中提取关键词作为文件名
        clean_query = re.sub(r'[^\w\s]', '', query)
        words = clean_query.split()[:3]  # 取前3个词
        filename_base = "_".join(words).lower()
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"generated_{filename_base}_{timestamp}.py"
    
    # 保存到文件
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(code)
    
    if debug_config["steps"]:
        print(f"💾 代码已保存到: {output_file}")
    
    return code


def run_with_metrics(query: str, debug=False, max_retries: int = 3, save_metrics: str = None) -> tuple[str, Dict[str, Any]]:
    """
    运行查询并返回代码和性能指标
    
    Args:
        query: 用户查询
        debug: 调试配置 - bool(开关) 或 dict{"steps": bool, "agents": bool, "performance": bool}
        max_retries: Agent重试次数
        save_metrics: 保存指标的文件路径（可选）
        
    Returns:
        (生成的代码, 性能指标字典)
    """
    # 处理调试配置
    if isinstance(debug, bool):
        debug_config = {"steps": debug, "agents": False, "performance": debug}
    else:
        debug_config = debug
    
    # 运行主函数
    code = run(query, debug=debug, max_retries=max_retries)
    
    # 获取性能指标
    monitor = get_monitor()
    metrics = monitor.export_metrics()
    
    # 保存指标到文件（可选）
    if save_metrics:
        import json
        with open(save_metrics, 'w', encoding='utf-8') as f:
            json.dump(metrics, f, ensure_ascii=False, indent=2)
        if debug_config["steps"]:
            print(f"📊 性能指标已保存到: {save_metrics}")
    
    return code, metrics


def get_system_info() -> Dict[str, Any]:
    """
    获取系统信息和组件统计
    
    Returns:
        系统信息字典
    """
    try:
        engine_stats = create_engine().get_agent_stats()
        registry_data = load_registry()
        
        return {
            "version": "vNext",
            "architecture": "7-Agent Pipeline",
            "components": {"total_components": len(registry_data)},
            "agents": engine_stats,
            "pipeline_stages": [
                "SemanticAgent → TaskCard",
                "DiscoveryAgent → Components",
                "ParamCompletionAgent → Parameters",
                "ParamNormAgent → NormalizedParams",
                "PipelineAgent → ExecutionPlan",
                "CodegenAgent → CodeCells",
                "AssemblyAgent → PythonCode"
            ]
        }
    
    except Exception as e:
        return {"error": str(e)}


def run_ablation_experiment(query: str, experiment_type: str = "ai_completion", debug: bool = True) -> Dict[str, Any]:
    """
    运行消融实验，比较不同配置下的系统表现
    
    Args:
        query: 测试查询
        experiment_type: 实验类型 "ai_completion" | "agent_robustness"
        debug: 是否显示调试信息
        
    Returns:
        实验结果字典
    """
    from config import ExperimentSettings
    
    results = {"experiment_type": experiment_type, "query": query, "results": {}}
    
    if experiment_type == "ai_completion":
        print(f"🧪 AI参数补全消融实验")
        print(f"📝 查询: {query}\n")
        
        # 对照组: 禁用AI参数补全
        control_config = {"ai_completion": {"enabled": False}}
        print("📊 对照组 (无AI补全):")
        try:
            start_time = time.time()
            control_code = run(query, debug=debug, experiment_config=control_config)
            control_time = time.time() - start_time
            
            results["results"]["control"] = {
                "success": True,
                "execution_time": control_time,
                "code_length": len(control_code),
                "param_count": control_code.count("=") # 简单参数计数
            }
            print(f"✅ 对照组完成: {control_time:.2f}s, {len(control_code)}字符\n")
            
        except Exception as e:
            results["results"]["control"] = {"success": False, "error": str(e)}
            print(f"❌ 对照组失败: {e}\n")
        
        # 实验组: 启用AI参数补全  
        experiment_config = {"ai_completion": {"enabled": True}}
        print("📊 实验组 (有AI补全):")
        try:
            start_time = time.time()
            experiment_code = run(query, debug=debug, experiment_config=experiment_config)
            experiment_time = time.time() - start_time
            
            results["results"]["experiment"] = {
                "success": True,
                "execution_time": experiment_time,
                "code_length": len(experiment_code),
                "param_count": experiment_code.count("=")
            }
            print(f"✅ 实验组完成: {experiment_time:.2f}s, {len(experiment_code)}字符")
            
        except Exception as e:
            results["results"]["experiment"] = {"success": False, "error": str(e)}
            print(f"❌ 实验组失败: {e}")
    
    elif experiment_type == "agent_robustness":
        print(f"🧪 Agent鲁棒性实验")
        print(f"📝 查询: {query}\n")
        
        # 对照组: 正常运行所有Agent
        control_config = {"robustness": {"simulate_failure": False, "failed_agent": None}}
        print("📊 对照组 (所有Agent正常):")
        try:
            start_time = time.time()
            control_code = run(query, debug=debug, experiment_config=control_config)
            control_time = time.time() - start_time
            
            results["results"]["control"] = {
                "success": True,
                "execution_time": control_time,
                "code_length": len(control_code),
                "failed_agent": None
            }
            print(f"✅ 对照组完成: {control_time:.2f}s, {len(control_code)}字符\n")
            
        except Exception as e:
            results["results"]["control"] = {"success": False, "error": str(e), "failed_agent": None}
            print(f"❌ 对照组失败: {e}\n")
        
        # 实验组: 模拟不同Agent失效
        failed_agents = ["discovery", "param_norm", "pipeline"]
        
        for failed_agent in failed_agents:
            experiment_config = {
                "robustness": {
                    "simulate_failure": True,
                    "failed_agent": failed_agent,
                    "baseline_components": ExperimentSettings.BASELINE_COMPONENTS
                }
            }
            
            print(f"📊 实验组 ({failed_agent}Agent失效):")
            try:
                start_time = time.time()
                experiment_code = run(query, debug=debug, experiment_config=experiment_config)
                experiment_time = time.time() - start_time
                
                results["results"][f"failed_{failed_agent}"] = {
                    "success": True,
                    "execution_time": experiment_time,
                    "code_length": len(experiment_code),
                    "failed_agent": failed_agent
                }
                print(f"✅ 实验组完成: {experiment_time:.2f}s, {len(experiment_code)}字符")
                
            except Exception as e:
                results["results"][f"failed_{failed_agent}"] = {
                    "success": False, 
                    "error": str(e),
                    "failed_agent": failed_agent
                }
                print(f"❌ 实验组失败: {e}")
            
            print()  # 空行分隔
    
    return results


# =============================================================================
# 测试代码
# =============================================================================

if __name__ == "__main__":
    print("🚀 QuantumForge vNext 端到端测试")
    
    # 测试查询
    test_queries = [
        "帮我计算8比特TFIM的基态能量",
        "使用VQE算法计算10比特TFIM基态，横向场强度1.5"
    ]
    
    for query in test_queries:
        print(f"\n" + "="*60)
        print(f"🔍 测试查询: {query}")
        print("="*60)
        
        try:
            # 运行完整管道
            generated_code = run(query, debug=True)
            
            # 显示生成的代码片段
            lines = generated_code.split('\n')
            print(f"\n📄 生成的代码预览 (前20行):")
            print("-" * 50)
            for i, line in enumerate(lines[:20]):
                print(f"{i+1:2d}: {line}")
            if len(lines) > 20:
                print(f"... (还有{len(lines)-20}行)")
            print("-" * 50)
            
            print(f"🎉 查询处理成功！")
            
        except Exception as e:
            print(f"❌ 查询处理失败: {str(e)}")
    
    # 显示系统信息
    print(f"\n📊 系统信息:")
    system_info = get_system_info()
    for key, value in system_info.items():
        if isinstance(value, dict):
            print(f"  {key}: {len(value) if 'components' in key else value}")
        elif isinstance(value, list):
            print(f"  {key}: {len(value)}项")
        else:
            print(f"  {key}: {value}")