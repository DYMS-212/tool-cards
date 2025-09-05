"""
组件注册表加载器 - QuantumForge vNext

从components目录加载所有模块化的JSON组件定义。
"""

import json
import os
from typing import List, Dict, Any


def load_registry() -> List[Dict[str, Any]]:
    """
    加载组件注册表（支持模块化和单文件两种格式）
    
    Returns:
        组件注册表数据列表
    """
    current_dir = os.path.dirname(os.path.dirname(__file__))
    
    # 优先尝试模块化结构
    modules_dir = os.path.join(current_dir, "components", "modules")
    if os.path.exists(modules_dir):
        all_components = []
        
        # 递归加载所有模块的JSON文件
        for root, dirs, files in os.walk(modules_dir):
            for file in files:
                if file.endswith('.json'):
                    json_path = os.path.join(root, file)
                    try:
                        with open(json_path, 'r', encoding='utf-8') as f:
                            components = json.load(f)
                            if isinstance(components, list):
                                all_components.extend(components)
                            elif isinstance(components, dict):
                                all_components.append(components)
                    except Exception as e:
                        print(f"⚠️ 加载组件文件 {json_path} 失败: {e}")
                        continue
        
        print(f"📦 从modules目录加载了 {len(all_components)} 个组件")
        return all_components
    
    # 回退到单文件格式
    registry_path = os.path.join(current_dir, "components", "registry.json")
    if os.path.exists(registry_path):
        with open(registry_path, 'r', encoding='utf-8') as f:
            registry = json.load(f)
            if isinstance(registry, list):
                return registry
            elif isinstance(registry, dict) and 'components' in registry:
                return registry['components']
    
    print("⚠️ 未找到组件注册表")
    return []


def get_registry_stats() -> Dict[str, Any]:
    """获取注册表统计信息"""
    components = load_registry()
    
    kinds = {}
    domains = {}
    tags = set()
    
    for comp in components:
        # 统计kind
        kind = comp.get("kind", "unknown")
        kinds[kind] = kinds.get(kind, 0) + 1
        
        # 统计domain（从name中提取）
        name = comp.get("name", "")
        if "." in name:
            domain = name.split(".")[0]
            domains[domain] = domains.get(domain, 0) + 1
        
        # 收集tags
        comp_tags = comp.get("tags", [])
        tags.update(comp_tags)
    
    return {
        "total_components": len(components),
        "component_kinds": kinds,
        "domains": domains, 
        "total_tags": len(tags),
        "sample_tags": list(tags)[:10]
    }