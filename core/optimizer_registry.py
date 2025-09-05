"""
动态Optimizer注册表 - QuantumForge vNext

基于注册表驱动的optimizer管理系统，支持动态扩展和自动组件生成。
替代硬编码的optimizer列表和重复的helper函数。
"""

from typing import Dict, Any, List, Optional, Union
import importlib
import inspect
# ComponentCard直接使用Dict替代


# =============================================================================
# Optimizer注册表 - 核心配置
# =============================================================================

OPTIMIZER_REGISTRY = {
    "COBYLA": {
        "module": "qiskit_algorithms.optimizers",
        "class_name": "COBYLA", 
        "tags": ["gradient_free", "classical", "derivative_free"],
        "description": "Constrained Optimization BY Linear Approximation",
        "params": {
            "maxiter": {"type": "int", "default": 1000, "description": "Maximum iterations"},
            "rhobeg": {"type": "float", "default": 1.0, "description": "Initial trust region radius"},
            "rhoend": {"type": "float", "default": 1e-4, "description": "Final trust region radius"},
            "disp": {"type": "bool", "default": False, "description": "Display convergence info"}
        },
        "supports_bounds": False,
        "supports_constraints": True
    },
    
    "L_BFGS_B": {
        "module": "qiskit_algorithms.optimizers",
        "class_name": "L_BFGS_B",
        "tags": ["gradient_based", "classical", "quasi_newton"], 
        "description": "L-BFGS-B optimizer for bounded optimization",
        "params": {
            "maxiter": {"type": "int", "default": 1000, "description": "Maximum iterations"},
            "ftol": {"type": "float", "default": 1e-9, "description": "Function tolerance"},
            "gtol": {"type": "float", "default": 1e-5, "description": "Gradient tolerance"},
            "eps": {"type": "float", "default": 1e-8, "description": "Step size for gradient approximation"}
        },
        "supports_bounds": True,
        "supports_constraints": False
    },
    
    "SPSA": {
        "module": "qiskit_algorithms.optimizers",
        "class_name": "SPSA",
        "tags": ["stochastic", "gradient_free", "simultaneous_perturbation"],
        "description": "Simultaneous Perturbation Stochastic Approximation",
        "params": {
            "maxiter": {"type": "int", "default": 1000, "description": "Maximum iterations"},
            "learning_rate": {"type": "float", "default": None, "description": "Learning rate"},
            "perturbation": {"type": "float", "default": None, "description": "Perturbation factor"},
            "resamplings": {"type": "int", "default": 1, "description": "Number of resamplings"}
        },
        "supports_bounds": False,
        "supports_constraints": False
    },
    
    "SLSQP": {
        "module": "qiskit_algorithms.optimizers", 
        "class_name": "SLSQP",
        "tags": ["gradient_based", "classical", "sequential"],
        "description": "Sequential Least SQuares Programming",
        "params": {
            "maxiter": {"type": "int", "default": 100, "description": "Maximum iterations"},
            "ftol": {"type": "float", "default": 1e-9, "description": "Function tolerance"},
            "eps": {"type": "float", "default": 1.49e-8, "description": "Step size for gradient approximation"}
        },
        "supports_bounds": True,
        "supports_constraints": True
    },
    
    "POWELL": {
        "module": "qiskit_algorithms.optimizers",
        "class_name": "POWELL", 
        "tags": ["gradient_free", "classical", "powell_method"],
        "description": "Powell's conjugate direction method",
        "params": {
            "maxiter": {"type": "int", "default": 1000, "description": "Maximum iterations"},
            "maxfev": {"type": "int", "default": None, "description": "Maximum function evaluations"},
            "xtol": {"type": "float", "default": 1e-4, "description": "Relative tolerance"},
            "ftol": {"type": "float", "default": 1e-4, "description": "Relative function tolerance"}
        },
        "supports_bounds": True,
        "supports_constraints": False
    },
    
    "TNC": {
        "module": "qiskit_algorithms.optimizers",
        "class_name": "TNC",
        "tags": ["gradient_based", "classical", "truncated_newton"],
        "description": "Truncated Newton method for bounded optimization",
        "params": {
            "maxiter": {"type": "int", "default": 100, "description": "Maximum iterations"},
            "ftol": {"type": "float", "default": -1, "description": "Function tolerance"},
            "xtol": {"type": "float", "default": -1, "description": "Parameter tolerance"},
            "gtol": {"type": "float", "default": -1, "description": "Gradient tolerance"}
        },
        "supports_bounds": True,
        "supports_constraints": False
    }
}


# =============================================================================
# 动态组件生成器
# =============================================================================

def generate_optimizer_components() -> List[Dict[str, Any]]:
    """
    基于注册表动态生成所有optimizer组件定义
    
    Returns:
        组件字典列表，可直接用于组件发现系统
    """
    components = []
    
    for optimizer_name, config in OPTIMIZER_REGISTRY.items():
        component = {
            "name": f"Optimizer.{optimizer_name}",
            "kind": "optimizer",
            "tags": config["tags"] + ["optimizer"],
            "needs": [],
            "provides": ["optimizer"],
            "params_schema": _build_params_schema(config["params"]),
            "yields": {
                "optimizer": f"{optimizer_name} optimizer instance"
            },
            "codegen_hint": {
                "helper": f"create_{optimizer_name.lower()}_optimizer",
                "import": f"from {config['module']} import {config['class_name']}"
            },
            "metadata": {
                "description": config["description"],
                "supports_bounds": config["supports_bounds"],
                "supports_constraints": config["supports_constraints"]
            }
        }
        components.append(component)
    
    return components


def _build_params_schema(params_config: Dict[str, Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """构建参数Schema"""
    schema = {}
    for param_name, param_info in params_config.items():
        schema[param_name] = {
            "type": param_info["type"],
            "description": param_info["description"]
        }
        if param_info.get("default") is not None:
            schema[param_name]["default"] = param_info["default"]
    return schema


# =============================================================================
# 统一Optimizer工厂
# =============================================================================

def create_optimizer_factory(optimizer_name: str, **kwargs) -> Any:
    """
    统一的optimizer创建工厂
    
    Args:
        optimizer_name: optimizer名称 (如 "COBYLA", "L_BFGS_B")
        **kwargs: optimizer参数
        
    Returns:
        配置好的optimizer实例
        
    Raises:
        ValueError: 不支持的optimizer类型
        ImportError: optimizer类导入失败
    """
    if optimizer_name not in OPTIMIZER_REGISTRY:
        raise ValueError(f"不支持的optimizer: {optimizer_name}")
    
    config = OPTIMIZER_REGISTRY[optimizer_name]
    
    try:
        # 动态导入optimizer类
        module = importlib.import_module(config["module"])
        optimizer_class = getattr(module, config["class_name"])
        
        # 应用默认参数
        final_params = {}
        for param_name, param_config in config["params"].items():
            if param_name in kwargs:
                final_params[param_name] = kwargs[param_name]
            elif param_config.get("default") is not None:
                final_params[param_name] = param_config["default"]
        
        # 创建optimizer实例
        return optimizer_class(**final_params)
        
    except ImportError as e:
        raise ImportError(f"无法导入optimizer {optimizer_name}: {e}")
    except Exception as e:
        raise RuntimeError(f"创建optimizer {optimizer_name}失败: {e}")


def get_available_optimizers() -> List[str]:
    """获取所有可用的optimizer名称"""
    return list(OPTIMIZER_REGISTRY.keys())


def get_optimizer_info(optimizer_name: str) -> Optional[Dict[str, Any]]:
    """获取特定optimizer的详细信息"""
    return OPTIMIZER_REGISTRY.get(optimizer_name)


def get_optimizers_by_tag(tag: str) -> List[str]:
    """根据标签获取optimizer列表"""
    result = []
    for name, config in OPTIMIZER_REGISTRY.items():
        if tag in config["tags"]:
            result.append(name)
    return result


def register_optimizer(name: str, config: Dict[str, Any]) -> None:
    """
    注册新的optimizer
    
    Args:
        name: optimizer名称
        config: optimizer配置 (格式同OPTIMIZER_REGISTRY)
    """
    OPTIMIZER_REGISTRY[name] = config


def validate_optimizer_availability() -> Dict[str, bool]:
    """
    验证所有注册的optimizer是否可用
    
    Returns:
        {optimizer_name: is_available}
    """
    availability = {}
    
    for optimizer_name, config in OPTIMIZER_REGISTRY.items():
        try:
            module = importlib.import_module(config["module"])
            optimizer_class = getattr(module, config["class_name"])
            availability[optimizer_name] = True
        except (ImportError, AttributeError):
            availability[optimizer_name] = False
    
    return availability


# =============================================================================
# Helper函数动态生成器
# =============================================================================

def generate_optimizer_helper_code() -> str:
    """
    生成所有optimizer的helper函数代码
    
    Returns:
        完整的helper函数Python代码
    """
    import_lines = []
    function_lines = []
    
    for optimizer_name, config in OPTIMIZER_REGISTRY.items():
        # 生成import
        import_line = f"from {config['module']} import {config['class_name']}"
        if import_line not in import_lines:
            import_lines.append(import_line)
        
        # 生成helper函数
        func_name = f"create_{optimizer_name.lower()}_optimizer"
        params = config["params"]
        
        # 构建函数签名
        param_list = []
        for param_name, param_config in params.items():
            default = param_config.get("default")
            if default is not None:
                if isinstance(default, str):
                    param_list.append(f'{param_name}="{default}"')
                else:
                    param_list.append(f'{param_name}={default}')
            else:
                param_list.append(f'{param_name}=None')
        
        param_signature = ", ".join(param_list)
        
        # 构建函数参数过滤
        filtered_params = []
        for param_name in params.keys():
            filtered_params.append(f'        if {param_name} is not None: kwargs["{param_name}"] = {param_name}')
        
        function_code = f'''def {func_name}({param_signature}):
    """{config["description"]}"""
    kwargs = {{}}
{chr(10).join(filtered_params)}
    return {config["class_name"]}(**kwargs)'''
        
        function_lines.append(function_code)
    
    # 组合完整代码
    full_code = f'''"""
动态生成的Optimizer Helper函数
自动从optimizer_registry.py生成，请勿手动编辑
"""

{chr(10).join(import_lines)}


{chr(10).join(function_lines)}
'''
    
    return full_code


# =============================================================================
# 测试和验证函数
# =============================================================================

if __name__ == "__main__":
    print("🧪 测试Optimizer注册表...")
    
    # 1. 测试可用性
    print("\\n📋 可用Optimizer:")
    availability = validate_optimizer_availability()
    for name, available in availability.items():
        status = "✅" if available else "❌"
        print(f"  {status} {name}")
    
    # 2. 测试工厂函数
    print("\\n🏭 测试工厂创建:")
    try:
        cobyla = create_optimizer_factory("COBYLA", maxiter=500)
        print(f"  ✅ COBYLA创建成功: {type(cobyla).__name__}")
        
        lbfgs = create_optimizer_factory("L_BFGS_B", maxiter=200, ftol=1e-8)
        print(f"  ✅ L_BFGS_B创建成功: {type(lbfgs).__name__}")
    except Exception as e:
        print(f"  ❌ 创建失败: {e}")
    
    # 3. 测试标签查询
    print("\\n🏷️ 按标签查询:")
    gradient_free = get_optimizers_by_tag("gradient_free")
    print(f"  gradient_free: {gradient_free}")
    
    # 4. 测试组件生成
    print("\\n🧱 测试组件生成:")
    components = generate_optimizer_components()
    print(f"  生成了{len(components)}个optimizer组件")
    for comp in components[:2]:
        print(f"    - {comp['name']}: {comp['metadata']['description']}")
    
    # 5. 生成helper代码示例
    print("\\n📝 Helper函数代码预览:")
    helper_code = generate_optimizer_helper_code()
    preview = helper_code.split('\n')[:15]
    for line in preview:
        print(f"    {line}")
    print("    ...")
    
    print("\\n🎉 注册表测试完成!")