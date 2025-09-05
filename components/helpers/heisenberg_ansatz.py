"""
海森堡模型Ansatz构建器 - QuantumForge vNext

实现海森堡模型的哈密顿量激发ansatz。
"""

import numpy as np
from qiskit import QuantumCircuit
from qiskit.circuit import ParameterVector


def heisenberg_ansatz(n: int, reps: int) -> QuantumCircuit:
    """
    构建海森堡模型的哈密顿量激发ansatz
    
    使用RXX、RYY、RZZ门模拟各向同性海森堡相互作用
    
    Args:
        n: 量子比特数
        reps: ansatz层数
        
    Returns:
        QuantumCircuit: 海森堡ansatz电路
    """
    qc = QuantumCircuit(n)
    
    # 初始状态: Neel态加小扰动
    for i in range(n):
        if i % 2 == 0:
            qc.x(i)  # 创建 |101010...⟩
    
    # 添加小的横向场打破对称性
    for i in range(n):
        qc.ry(np.pi/8, i)
    
    # 参数：每层2n个 (n个用于交换，n个用于场)
    num_params_per_layer = 2 * n
    total_params = reps * num_params_per_layer
    params = ParameterVector('θ', total_params)
    param_idx = 0
    
    for layer in range(reps):
        # 海森堡交换层 (XX + YY + ZZ用相同参数)
        for i in range(n):
            next_i = (i + 1) % n
            theta = params[param_idx]
            
            # 各向同性：所有三个旋转用相同角度
            qc.rxx(theta, i, next_i)
            qc.ryy(theta, i, next_i)
            qc.rzz(theta, i, next_i)
            param_idx += 1
        
        # 局域场层
        for i in range(n):
            qc.rz(params[param_idx], i)
            param_idx += 1
    
    return qc


if __name__ == "__main__":
    # 简单测试
    ansatz = heisenberg_ansatz(4, 2)
    print(f"Heisenberg_Ansatz(4,2): {ansatz.num_parameters} params")