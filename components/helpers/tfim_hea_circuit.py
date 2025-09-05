"""
TFIM哈密顿量激发Ansatz构建器 - QuantumForge vNext

实现TFIM的哈密顿量激发ansatz电路，直接对应TFIM物理结构。
"""

import numpy as np
from qiskit import QuantumCircuit
from qiskit.circuit import ParameterVector


def tfim_hea(n, reps):
    """
    构建TFIM哈密顿量激发ansatz
    
    物理启发设计：
    - ZZ相互作用层：对应 -J*ΣZᵢZᵢ₊₁ 项
    - X场层：对应 -hx*ΣXᵢ 项
    - H门初始化：创建叠加态起点
    
    Args:
        n: 量子比特数
        reps: ansatz重复层数
        
    Returns:
        QuantumCircuit: TFIM激发ansatz电路
    """
    qc = QuantumCircuit(n)
    
    # 初始化为叠加态（所有比特处于|+⟩态）
    for i in range(n):
        qc.h(i)
    
    # 参数向量：每层2n个参数（n个ZZ + n个X）
    num_params_per_layer = 2 * n
    total_params = reps * num_params_per_layer
    params = ParameterVector('θ', total_params)
    param_idx = 0
    
    # 构建ansatz层
    for layer in range(reps):
        # ZZ相互作用层（模拟 -J*ΣZᵢZᵢ₊₁）
        for i in range(n):
            next_i = (i + 1) % n
            qc.cx(i, next_i)
            qc.rz(params[param_idx], next_i)
            qc.cx(i, next_i)
            param_idx += 1
        
        # X场层（模拟 -hx*ΣXᵢ）
        for i in range(n):
            qc.rx(params[param_idx], i)
            param_idx += 1
    
    return qc


if __name__ == "__main__":
    # 简单测试
    ansatz = tfim_hea(4, 2)
    print(f"TFIM_HEA(4,2): {ansatz.num_parameters} params")