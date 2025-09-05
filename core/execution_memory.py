"""
执行记忆系统 - QuantumForge vNext

重新设计的轻量级Memory系统，专注于CodeCell存储和管理。
去除了复杂的状态跟踪，简化为纯容器功能。
"""

from typing import Dict, List, Optional, Any


class Memory:
    """
    CodeCell存储容器
    
    vNext设计：简单的CodeCell容器，支持按ID存取和导出
    去除了复杂的状态管理和历史跟踪功能
    """
    
    def __init__(self):
        """初始化Memory容器"""
        self._cells: Dict[str, Dict[str, Any]] = {}  # 直接使用Dict替代CodeCell
        self._insertion_order: List[str] = []  # 维护插入顺序
    
    def add(self, cell: Dict[str, Any]) -> None:
        """
        添加CodeCell到容器
        
        Args:
            cell: 要添加的代码单元字典
        """
        if not isinstance(cell, dict) or 'id' not in cell:
            raise TypeError("Expected dict with 'id' field")
        
        cell_id = cell['id']
        
        # 如果是新Cell，记录插入顺序
        if cell_id not in self._cells:
            self._insertion_order.append(cell_id)
        
        # 存储（允许覆盖）
        self._cells[cell_id] = cell
    
    def get(self, cell_id: str) -> Optional[Dict[str, Any]]:
        """
        根据ID获取CodeCell
        
        Args:
            cell_id: Cell的唯一标识
            
        Returns:
            代码单元字典或None
        """
        return self._cells.get(cell_id)
    
    def export(self) -> List[Dict[str, Any]]:
        """
        按插入顺序导出所有CodeCell
        
        Returns:
            按插入顺序排列的代码单元字典列表
        """
        return [self._cells[cell_id] for cell_id in self._insertion_order if cell_id in self._cells]
    
    def size(self) -> int:
        """获取存储的Cell数量"""
        return len(self._cells)
    
    def contains(self, cell_id: str) -> bool:
        """检查是否包含指定ID的Cell"""
        return cell_id in self._cells
    
    def clear(self) -> None:
        """清空所有Cell"""
        self._cells.clear()
        self._insertion_order.clear()
    
    def get_all_ids(self) -> List[str]:
        """获取所有Cell ID（按插入顺序）"""
        return self._insertion_order.copy()
    
    def remove(self, cell_id: str) -> bool:
        """
        移除指定的Cell
        
        Args:
            cell_id: 要移除的Cell ID
            
        Returns:
            是否成功移除
        """
        if cell_id in self._cells:
            del self._cells[cell_id]
            self._insertion_order.remove(cell_id)
            return True
        return False
    
    def get_summary(self) -> Dict[str, int]:
        """获取Memory内容摘要"""
        summary = {
            "total_cells": len(self._cells),
            "total_imports": 0,
            "total_helpers": 0,
            "total_definitions": 0,
            "cells_with_exports": 0
        }
        
        for cell in self._cells.values():
            summary["total_imports"] += len(cell.imports)
            summary["total_helpers"] += len(cell.helpers)
            summary["total_definitions"] += len(cell.definitions)
            if cell.has_exports():
                summary["cells_with_exports"] += 1
        
        return summary


def create() -> Memory:
    """
    创建新的Memory实例
    
    工厂函数，保持与new.md规格一致
    """
    return Memory()


# =============================================================================
# 测试代码
# =============================================================================

if __name__ == "__main__":
    print("🧪 Testing Memory system...")
    
    # 创建Memory
    memory = create()
    assert memory.size() == 0
    
    # 创建测试CodeCell
    cell1 = CodeCell(
        id="test_cell_1",
        imports=["import numpy as np"],
        helpers=["def helper_func(): pass"],
        definitions=["CONSTANT = 42"],
        invoke="result = helper_func()",
        exports={"result": "result"}
    )
    
    cell2 = CodeCell(
        id="test_cell_2", 
        imports=["from qiskit import QuantumCircuit"],
        helpers=[],
        definitions=[],
        invoke="qc = QuantumCircuit(2)",
        exports={"circuit": "qc"}
    )
    
    # 测试添加
    memory.add(cell1)
    memory.add(cell2)
    assert memory.size() == 2
    assert memory.contains("test_cell_1")
    
    # 测试获取
    retrieved = memory.get("test_cell_1")
    assert retrieved is not None
    assert retrieved.id == "test_cell_1"
    
    # 测试导出（按插入顺序）
    exported = memory.export()
    assert len(exported) == 2
    assert exported[0].id == "test_cell_1"
    assert exported[1].id == "test_cell_2"
    
    # 测试摘要
    summary = memory.get_summary()
    assert summary["total_cells"] == 2
    assert summary["cells_with_exports"] == 2
    
    # 测试移除
    success = memory.remove("test_cell_1")
    assert success
    assert memory.size() == 1
    assert not memory.contains("test_cell_1")
    
    # 测试清空
    memory.clear()
    assert memory.size() == 0
    
    print("✅ Memory system 测试通过！")