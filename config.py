"""
QuantumForge vNext 配置文件

集中管理系统配置，包括缓存设置、默认参数、别名映射等。
"""

from typing import Dict, Any, List


# =============================================================================
# 缓存配置
# =============================================================================

class CacheSettings:
    """缓存设置"""
    
    # 缓存总开关 - 用户可以通过这里控制
    ENABLE_CACHE = True
    
    # 分类缓存开关
    REGISTRY_CACHE = True       # 组件注册表缓存
    QUERY_CACHE = True          # 查询结果缓存
    AGENT_CACHE = True          # Agent响应缓存
    
    # 缓存参数
    CACHE_TTL = 3600           # 缓存过期时间（秒）
    MAX_CACHE_ENTRIES = 1000   # 最大缓存条目数
    
    @classmethod
    def get_config_dict(cls) -> Dict[str, Any]:
        """获取配置字典"""
        return {
            "enable_cache": cls.ENABLE_CACHE,
            "registry_cache": cls.REGISTRY_CACHE,
            "query_cache": cls.QUERY_CACHE,
            "agent_cache": cls.AGENT_CACHE,
            "ttl": cls.CACHE_TTL,
            "max_entries": cls.MAX_CACHE_ENTRIES
        }


# =============================================================================
# 参数配置
# =============================================================================

# 参数别名映射
ALIASES = {
    "num_qubits": "n",
    "qubits": "n",
    "h_x": "hx",
    "hx_field": "hx",
    "transverse_field": "hx",
    "layers": "depth", 
    "repetitions": "depth",
    "circuit_depth": "depth",
    "coupling": "j",
    "j_coupling": "j",
    "max_iterations": "maxiter",
    "max_iter": "maxiter"
}

# 默认参数值
DEFAULTS = {
    "optimizer": "COBYLA",
    "depth": 2,
    "shots": None,
    "boundary": "periodic",
    "seed": 42,
    "maxiter": 200,
    "hx": 1.0,
    "j": 1.0
}

# 参数取值范围
VALID_ENUMS = {
    "boundary": ["periodic", "open"],
    # optimizer列表现在从optimizer_registry动态获取
    "domain": ["spin", "chemistry", "optimization", "custom"],
    "algorithm": ["vqe", "qaoa", "qpe", "vqd", "vqls"],
    "backend": ["qiskit"]
}

# 参数类型定义
PARAM_TYPES = {
    "n": int,
    "hx": float,
    "j": float,
    "depth": int,
    "maxiter": int,
    "shots": (int, type(None)),
    "seed": int,
    "boundary": str,
    "optimizer": str
}


# =============================================================================
# Agent配置
# =============================================================================

class AgentSettings:
    """Agent设置"""
    
    # OpenAI配置
    DEFAULT_MODEL = "gpt-4"
    MAX_RETRIES = 3
    RETRY_DELAY = 0.5  # 秒
    
    # 并行执行配置
    ENABLE_PARALLEL = True
    MAX_PARALLEL_AGENTS = 2  # 同时运行的Agent数量
    
    # Agent超时配置
    AGENT_TIMEOUT = 30  # 秒


# =============================================================================
# 优化器配置
# =============================================================================

class OptimizerSettings:
    """代码优化器设置"""
    
    # 优化功能开关
    ENABLE_OPTIMIZATION = True
    DEDUPLICATE_FUNCTIONS = True
    OPTIMIZE_IMPORTS = True
    REMOVE_UNUSED = True
    OPTIMIZE_MAIN_SIGNATURE = True
    
    # 优化阈值
    SIMILARITY_THRESHOLD = 0.9  # 函数相似度阈值
    MIN_PARAMS_TO_OPTIMIZE = 3  # 最少参数数量才进行优化


# =============================================================================
# 参数处理配置
# =============================================================================

class ParameterSettings:
    """参数处理设置"""
    
    # 新架构功能开关
    USE_COMPONENT_DRIVEN_PARAMS = True   # 组件驱动参数发现
    ENABLE_AI_COMPLETION = True          # AI智能参数补全  
    FALLBACK_TO_LEGACY = True           # 向后兼容legacy方式
    
    # 参数补全配置
    AI_COMPLETION_TIMEOUT = 30           # AI补全超时时间（秒）
    REQUIRE_ALL_PARAMS = False           # 是否要求所有参数都必须提供
    

# =============================================================================
# 系统配置
# =============================================================================

class SystemSettings:
    """系统设置"""
    
    # 调试模式
    DEFAULT_DEBUG = False
    
    # 性能配置
    DEFAULT_TIMEOUT = 60  # 秒
    
    # 文件路径
    HELPERS_PATH = "components/helpers"
    
    # 输出配置
    AUTO_SAVE = True
    OUTPUT_ENCODING = "utf-8"


# =============================================================================
# 实验配置 - 消融实验和鲁棒性测试
# =============================================================================

class ExperimentSettings:
    """实验配置 - 支持消融实验和鲁棒性测试"""
    
    # AI参数补全消融实验
    ENABLE_AI_COMPLETION = True          # 启用AI参数补全
    AI_COMPLETION_FALLBACK = "skip"      # 禁用时的fallback策略: "skip" | "defaults"
    
    # Agent鲁棒性实验
    SIMULATE_AGENT_FAILURE = False       # 是否模拟Agent失效
    FAILED_AGENT = None                  # 要模拟失效的Agent: "discovery" | "param_norm" | "pipeline"
    
    # 实验度量配置
    COLLECT_METRICS = True               # 是否收集实验指标
    RECORD_EXECUTION_TIME = True         # 记录执行时间
    RECORD_PARAMETER_COVERAGE = True     # 记录参数覆盖率
    RECORD_CODE_QUALITY = True           # 记录代码质量指标
    
    # 对照实验配置
    BASELINE_COMPONENTS = [              # Agent失效时的备用组件列表
        "Hamiltonian.TFIM",
        "Circuit.TFIM_HEA", 
        "Algorithm.VQE",
        "Optimizer.COBYLA",
        "Backend.Estimator"
    ]
    
    @classmethod
    def get_experiment_config(cls) -> Dict[str, Any]:
        """获取实验配置"""
        return {
            "ai_completion": {
                "enabled": cls.ENABLE_AI_COMPLETION,
                "fallback": cls.AI_COMPLETION_FALLBACK
            },
            "robustness": {
                "simulate_failure": cls.SIMULATE_AGENT_FAILURE,
                "failed_agent": cls.FAILED_AGENT,
                "baseline_components": cls.BASELINE_COMPONENTS
            },
            "metrics": {
                "collect": cls.COLLECT_METRICS,
                "execution_time": cls.RECORD_EXECUTION_TIME,
                "param_coverage": cls.RECORD_PARAMETER_COVERAGE,
                "code_quality": cls.RECORD_CODE_QUALITY
            }
        }


# =============================================================================
# 便利函数
# =============================================================================

def get_cache_config() -> Dict[str, Any]:
    """获取缓存配置"""
    return CacheSettings.get_config_dict()


def get_aliases() -> Dict[str, str]:
    """获取参数别名映射"""
    return ALIASES.copy()


def get_defaults() -> Dict[str, Any]:
    """获取默认参数值"""
    return DEFAULTS.copy()


def get_valid_enums() -> Dict[str, List[str]]:
    """获取有效枚举值（optimizer列表动态加载）"""
    enums = VALID_ENUMS.copy()
    
    # 动态加载optimizer列表
    try:
        from core.optimizer_registry import get_available_optimizers
        enums["optimizer"] = get_available_optimizers()
    except ImportError:
        # 兜底使用基础optimizer
        enums["optimizer"] = ["COBYLA", "L_BFGS_B"]
    
    return enums


def validate_param_value(param_name: str, value: Any) -> bool:
    """验证参数值是否有效"""
    # 检查枚举值
    if param_name in VALID_ENUMS:
        return value in VALID_ENUMS[param_name]
    
    # 检查类型
    if param_name in PARAM_TYPES:
        expected_type = PARAM_TYPES[param_name]
        if isinstance(expected_type, tuple):
            return isinstance(value, expected_type)
        else:
            return isinstance(value, expected_type)
    
    return True  # 未知参数允许通过


def get_system_config() -> Dict[str, Any]:
    """获取完整系统配置"""
    return {
        "cache": get_cache_config(),
        "aliases": get_aliases(),
        "defaults": get_defaults(),
        "valid_enums": get_valid_enums(),
        "parameters": {
            "use_component_driven": ParameterSettings.USE_COMPONENT_DRIVEN_PARAMS,
            "enable_ai_completion": ParameterSettings.ENABLE_AI_COMPLETION,
            "fallback_to_legacy": ParameterSettings.FALLBACK_TO_LEGACY,
            "ai_timeout": ParameterSettings.AI_COMPLETION_TIMEOUT,
            "require_all_params": ParameterSettings.REQUIRE_ALL_PARAMS
        },
        "agent": {
            "model": AgentSettings.DEFAULT_MODEL,
            "max_retries": AgentSettings.MAX_RETRIES,
            "enable_parallel": AgentSettings.ENABLE_PARALLEL,
            "max_parallel": AgentSettings.MAX_PARALLEL_AGENTS,
            "timeout": AgentSettings.AGENT_TIMEOUT
        },
        "optimizer": {
            "enable": OptimizerSettings.ENABLE_OPTIMIZATION,
            "dedupe_functions": OptimizerSettings.DEDUPLICATE_FUNCTIONS,
            "optimize_imports": OptimizerSettings.OPTIMIZE_IMPORTS,
            "remove_unused": OptimizerSettings.REMOVE_UNUSED,
            "optimize_signature": OptimizerSettings.OPTIMIZE_MAIN_SIGNATURE
        },
        "system": {
            "debug": SystemSettings.DEFAULT_DEBUG,
            "timeout": SystemSettings.DEFAULT_TIMEOUT,
            "auto_save": SystemSettings.AUTO_SAVE
        }
    }


# =============================================================================
# 测试代码
# =============================================================================

if __name__ == "__main__":
    print("🧪 测试配置系统...")
    
    # 测试缓存配置
    print("\n🚀 缓存配置:")
    cache_config = get_cache_config()
    for key, value in cache_config.items():
        print(f"  {key}: {value}")
    
    # 测试参数验证
    print("\n🔍 参数验证测试:")
    test_cases = [
        ("boundary", "periodic", True),
        ("boundary", "invalid", False),
        ("n", 4, True),
        ("n", "invalid", False),
        ("optimizer", "COBYLA", True),
        ("optimizer", "INVALID", False)
    ]
    
    for param, value, expected in test_cases:
        result = validate_param_value(param, value)
        status = "✅" if result == expected else "❌"
        print(f"  {status} {param}={value} → {result}")
    
    # 显示完整配置
    print("\n📊 完整系统配置:")
    import json
    config = get_system_config()
    print(json.dumps(config, ensure_ascii=False, indent=2))
    
    print("\n🎉 配置系统测试完成！")