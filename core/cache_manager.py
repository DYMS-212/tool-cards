"""
缓存管理器 - QuantumForge vNext

提供智能缓存功能，包括组件注册表缓存、Agent响应缓存和查询结果缓存。
支持可配置的缓存开关和TTL设置。
"""

import json
import time
import hashlib
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, asdict
from pathlib import Path


@dataclass
class CacheConfig:
    """缓存配置"""
    enable_cache: bool = True           # 总缓存开关
    registry_cache: bool = True         # 组件注册表缓存（加速文件读取）
    query_cache: bool = False          # 查询结果缓存（已禁用）
    agent_cache: bool = False          # Agent响应缓存（已禁用）
    helper_cache: bool = True          # Helper函数源码缓存（加速文件读取）
    ttl: int = 3600                    # 缓存过期时间(秒)
    max_entries: int = 1000            # 最大缓存条目数


class CacheManager:
    """
    智能缓存管理器
    
    功能：
    - 组件注册表缓存（避免重复文件读取，不影响Agent评测）
    - Helper函数源码缓存（加速文件读取，不影响Agent评测）
    - 自动过期和LRU清理
    
    注：Agent响应缓存和查询结果缓存已禁用，确保Agent每次真实表现
    """
    
    def __init__(self, config: Optional[CacheConfig] = None):
        """
        初始化缓存管理器
        
        Args:
            config: 缓存配置，默认使用标准配置
        """
        self.config = config or CacheConfig()
        
        # 缓存存储
        self._registry_cache: Dict[str, Any] = {}
        self._query_cache: Dict[str, Any] = {}
        self._agent_cache: Dict[str, Any] = {}
        self._helper_cache: Dict[str, str] = {}  # Helper函数源码缓存
        
        # 缓存元数据（用于TTL和LRU）
        self._cache_timestamps: Dict[str, float] = {}
        self._cache_access_times: Dict[str, float] = {}
    
    def _generate_key(self, data: Union[str, Dict, List]) -> str:
        """生成缓存键"""
        if isinstance(data, str):
            content = data
        else:
            content = json.dumps(data, sort_keys=True, ensure_ascii=False)
        
        return hashlib.md5(content.encode('utf-8')).hexdigest()
    
    def _is_expired(self, key: str) -> bool:
        """检查缓存是否过期"""
        if key not in self._cache_timestamps:
            return True
        
        return time.time() - self._cache_timestamps[key] > self.config.ttl
    
    def _cleanup_expired(self, cache_dict: Dict[str, Any]) -> None:
        """清理过期缓存"""
        current_time = time.time()
        expired_keys = [
            key for key, timestamp in self._cache_timestamps.items()
            if current_time - timestamp > self.config.ttl and key in cache_dict
        ]
        
        for key in expired_keys:
            cache_dict.pop(key, None)
            self._cache_timestamps.pop(key, None)
            self._cache_access_times.pop(key, None)
    
    def _enforce_max_entries(self, cache_dict: Dict[str, Any]) -> None:
        """强制执行最大条目数限制（LRU清理）"""
        if len(cache_dict) <= self.config.max_entries:
            return
        
        # 按访问时间排序，删除最久未访问的条目
        sorted_keys = sorted(
            cache_dict.keys(),
            key=lambda k: self._cache_access_times.get(k, 0)
        )
        
        # 删除最旧的条目直到满足限制
        to_remove = len(cache_dict) - self.config.max_entries
        for key in sorted_keys[:to_remove]:
            cache_dict.pop(key, None)
            self._cache_timestamps.pop(key, None)
            self._cache_access_times.pop(key, None)
    
    def cache_registry(self, registry_path: str, registry_data: List[Dict[str, Any]]) -> None:
        """缓存组件注册表"""
        if not self.config.enable_cache or not self.config.registry_cache:
            return
        
        key = f"registry_{self._generate_key(registry_path)}"
        current_time = time.time()
        
        self._registry_cache[key] = registry_data
        self._cache_timestamps[key] = current_time
        self._cache_access_times[key] = current_time
        
        self._cleanup_expired(self._registry_cache)
        self._enforce_max_entries(self._registry_cache)
    
    def get_cached_registry(self, registry_path: str) -> Optional[List[Dict[str, Any]]]:
        """获取缓存的组件注册表"""
        if not self.config.enable_cache or not self.config.registry_cache:
            return None
        
        key = f"registry_{self._generate_key(registry_path)}"
        
        if key not in self._registry_cache or self._is_expired(key):
            return None
        
        # 更新访问时间
        self._cache_access_times[key] = time.time()
        return self._registry_cache[key]
    
    def cache_agent_response(self, agent_name: str, input_data: Dict[str, Any], response: Any) -> None:
        """缓存Agent响应"""
        if not self.config.enable_cache or not self.config.agent_cache:
            return
        
        input_key = self._generate_key(input_data)
        key = f"agent_{agent_name}_{input_key}"
        current_time = time.time()
        
        self._agent_cache[key] = response
        self._cache_timestamps[key] = current_time
        self._cache_access_times[key] = current_time
        
        self._cleanup_expired(self._agent_cache)
        self._enforce_max_entries(self._agent_cache)
    
    def get_cached_agent_response(self, agent_name: str, input_data: Dict[str, Any]) -> Optional[Any]:
        """获取缓存的Agent响应"""
        if not self.config.enable_cache or not self.config.agent_cache:
            return None
        
        input_key = self._generate_key(input_data)
        key = f"agent_{agent_name}_{input_key}"
        
        if key not in self._agent_cache or self._is_expired(key):
            return None
        
        # 更新访问时间
        self._cache_access_times[key] = time.time()
        return self._agent_cache[key]
    
    def cache_query_result(self, query: str, task_card: Dict[str, Any], result_code: str) -> None:
        """缓存完整查询结果"""
        if not self.config.enable_cache or not self.config.query_cache:
            return
        
        query_data = {"query": query, "task_card": task_card}
        key = f"query_{self._generate_key(query_data)}"
        current_time = time.time()
        
        self._query_cache[key] = {
            "query": query,
            "task_card": task_card,
            "result_code": result_code,
            "generated_at": current_time
        }
        self._cache_timestamps[key] = current_time
        self._cache_access_times[key] = current_time
        
        self._cleanup_expired(self._query_cache)
        self._enforce_max_entries(self._query_cache)
    
    def get_cached_query_result(self, query: str, task_card: Dict[str, Any]) -> Optional[str]:
        """获取缓存的查询结果"""
        if not self.config.enable_cache or not self.config.query_cache:
            return None
        
        query_data = {"query": query, "task_card": task_card}
        key = f"query_{self._generate_key(query_data)}"
        
        if key not in self._query_cache or self._is_expired(key):
            return None
        
        # 更新访问时间
        self._cache_access_times[key] = time.time()
        return self._query_cache[key]["result_code"]
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        current_time = time.time()
        
        def count_active(cache_dict):
            return len([
                key for key in cache_dict.keys()
                if not self._is_expired(key)
            ])
        
        return {
            "config": asdict(self.config),
            "registry_cache": {
                "total_entries": len(self._registry_cache),
                "active_entries": count_active(self._registry_cache)
            },
            "agent_cache": {
                "total_entries": len(self._agent_cache),
                "active_entries": count_active(self._agent_cache)
            },
            "query_cache": {
                "total_entries": len(self._query_cache),
                "active_entries": count_active(self._query_cache)
            },
            "helper_cache": {
                "total_entries": len(self._helper_cache),
                "active_entries": count_active(self._helper_cache)
            }
        }
    
    def clear_cache(self, cache_type: Optional[str] = None) -> None:
        """清理缓存"""
        if cache_type == "registry" or cache_type is None:
            self._registry_cache.clear()
        
        if cache_type == "agent" or cache_type is None:
            self._agent_cache.clear()
        
        if cache_type == "query" or cache_type is None:
            self._query_cache.clear()
        
        if cache_type == "helper" or cache_type is None:
            self._helper_cache.clear()
        
        if cache_type is None:
            self._cache_timestamps.clear()
            self._cache_access_times.clear()
    
    def find_similar_queries(self, query: str, similarity_threshold: float = 0.8) -> List[Dict[str, Any]]:
        """查找相似的查询（基于字符串相似度）"""
        if not self.config.enable_cache or not self.config.query_cache:
            return []
        
        similar_queries = []
        query_lower = query.lower()
        
        for cached_data in self._query_cache.values():
            cached_query = cached_data["query"].lower()
            
            # 简单的字符串相似度计算
            similarity = self._calculate_similarity(query_lower, cached_query)
            
            if similarity >= similarity_threshold:
                similar_queries.append({
                    "similarity": similarity,
                    "query": cached_data["query"],
                    "task_card": cached_data["task_card"],
                    "generated_at": cached_data["generated_at"]
                })
        
        # 按相似度降序排序
        return sorted(similar_queries, key=lambda x: x["similarity"], reverse=True)
    
    def _calculate_similarity(self, s1: str, s2: str) -> float:
        """计算两个字符串的相似度（简单实现）"""
        if s1 == s2:
            return 1.0
        
        # 使用最长公共子序列的简化版本
        words1 = set(s1.split())
        words2 = set(s2.split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union)
    
    def cache_helper_source(self, helper_name: str, source_code: str) -> None:
        """缓存Helper函数源码"""
        if not self.config.enable_cache or not self.config.helper_cache:
            return
        
        key = f"helper_{helper_name}"
        current_time = time.time()
        
        self._helper_cache[key] = source_code
        self._cache_timestamps[key] = current_time
        self._cache_access_times[key] = current_time
        
        self._cleanup_expired(self._helper_cache)
        self._enforce_max_entries(self._helper_cache)
    
    def get_cached_helper_source(self, helper_name: str) -> Optional[str]:
        """获取缓存的Helper函数源码"""
        if not self.config.enable_cache or not self.config.helper_cache:
            return None
        
        key = f"helper_{helper_name}"
        
        if key not in self._helper_cache or self._is_expired(key):
            return None
        
        # 更新访问时间
        self._cache_access_times[key] = time.time()
        return self._helper_cache[key]
    
    def preload_all_helpers(self, helpers_dir: str) -> None:
        """预加载所有Helper函数源码"""
        if not self.config.enable_cache or not self.config.helper_cache:
            return
        
        helpers_path = Path(helpers_dir)
        for py_file in helpers_path.rglob("*.py"):
            if py_file.name.startswith("__"):
                continue
                
            try:
                source_code = py_file.read_text(encoding='utf-8')
                
                # 分析文件内容提取实际函数名
                import re
                function_matches = re.findall(r'^def\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(', source_code, re.MULTILINE)
                
                if function_matches:
                    # 对于每个函数，以函数名为key缓存整个文件内容
                    for func_name in function_matches:
                        self.cache_helper_source(func_name, source_code)
                else:
                    # 如果没找到函数，使用文件名
                    helper_name = py_file.stem
                    self.cache_helper_source(helper_name, source_code)
            except Exception as e:
                print(f"⚠️ 无法加载helper文件 {py_file}: {e}")
    
    def get_all_helper_names(self) -> List[str]:
        """获取所有已缓存的Helper函数名"""
        return [key.replace("helper_", "") for key in self._helper_cache.keys()]


# =============================================================================
# 便利函数
# =============================================================================

def create_cache_manager(
    enable_cache: bool = True,
    registry_cache: bool = True,
    query_cache: bool = True, 
    agent_cache: bool = True,
    helper_cache: bool = True,
    ttl: int = 3600
) -> CacheManager:
    """
    创建缓存管理器实例
    
    Args:
        enable_cache: 总缓存开关
        registry_cache: 组件注册表缓存开关
        query_cache: 查询结果缓存开关
        agent_cache: Agent响应缓存开关
        helper_cache: Helper函数源码缓存开关
        ttl: 缓存过期时间（秒）
        
    Returns:
        CacheManager实例
    """
    config = CacheConfig(
        enable_cache=enable_cache,
        registry_cache=registry_cache,
        query_cache=query_cache,
        agent_cache=agent_cache,
        helper_cache=helper_cache,
        ttl=ttl
    )
    
    return CacheManager(config)


# =============================================================================
# 测试代码
# =============================================================================

if __name__ == "__main__":
    print("🧪 Testing CacheManager...")
    
    # 创建缓存管理器
    cache = create_cache_manager()
    
    # 测试组件注册表缓存
    print("\n📋 测试组件注册表缓存")
    test_registry = [{"name": "Test.Component", "kind": "test"}]
    cache.cache_registry("test_path", test_registry)
    
    cached_registry = cache.get_cached_registry("test_path")
    if cached_registry == test_registry:
        print("✅ 组件注册表缓存工作正常")
    else:
        print("❌ 组件注册表缓存失败")
    
    # 测试Agent响应缓存
    print("\n🤖 测试Agent响应缓存")
    test_input = {"test": "data"}
    test_response = {"result": "success"}
    cache.cache_agent_response("TestAgent", test_input, test_response)
    
    cached_response = cache.get_cached_agent_response("TestAgent", test_input)
    if cached_response == test_response:
        print("✅ Agent响应缓存工作正常")
    else:
        print("❌ Agent响应缓存失败")
    
    # 测试查询结果缓存
    print("\n🔍 测试查询结果缓存")
    test_query = "计算系统基态"
    test_task_card = {"domain": "spin", "algorithm": "test_algorithm"}
    test_code = "print('test')"
    
    cache.cache_query_result(test_query, test_task_card, test_code)
    cached_code = cache.get_cached_query_result(test_query, test_task_card)
    
    if cached_code == test_code:
        print("✅ 查询结果缓存工作正常")
    else:
        print("❌ 查询结果缓存失败")
    
    # 显示缓存统计
    print("\n📊 缓存统计:")
    stats = cache.get_cache_stats()
    print(json.dumps(stats, ensure_ascii=False, indent=2))
    
    print("\n🎉 CacheManager测试完成！")