"""
海森堡哈密顿量构建器 - QuantumForge vNext

实现海森堡自旋链模型的哈密顿量构建功能。
"""

from qiskit.quantum_info import SparsePauliOp


def build_heisenberg_h(
    n: int,  # 适配框架参数名
    Jx: float = 1.0,
    Jy: float = 1.0,
    Jz: float = 1.0,
    hz: float = 0.0,
    boundary: str = 'periodic'  # 适配框架参数名：'periodic'/'open'
) -> SparsePauliOp:
    """
    通用自旋链哈密顿量:
    H = Σᵢ (Jx σₓⁱ σₓⁱ⁺¹ + Jy σᵧⁱ σᵧⁱ⁺¹ + Jz σ𝓏ⁱ σ𝓏ⁱ⁺¹) + hz Σᵢ σ𝓏ⁱ

    Args:
        n: 自旋个数 (链长)
        Jx, Jy, Jz: X, Y, Z 方向的相互作用强度
        hz: Z 方向均匀外磁场
        boundary: 边界条件 ('periodic' 或 'open')
    
    Returns:
        SparsePauliOp: Qiskit 稀疏泡利哈密顿量
    """
    H_list = []
    pbc = (boundary == 'periodic')

    # 相互作用项
    for i in range(n):
        if (not pbc) and (i == n - 1):  # 开边界时跳过最后一个
            continue
        j = (i + 1) % n

        # X-X
        if abs(Jx) > 1e-12:
            pauli_str = ['I'] * n
            pauli_str[i] = 'X'
            pauli_str[j] = 'X'
            H_list.append((''.join(pauli_str), Jx))

        # Y-Y
        if abs(Jy) > 1e-12:
            pauli_str = ['I'] * n
            pauli_str[i] = 'Y'
            pauli_str[j] = 'Y'
            H_list.append((''.join(pauli_str), Jy))

        # Z-Z
        if abs(Jz) > 1e-12:
            pauli_str = ['I'] * n
            pauli_str[i] = 'Z'
            pauli_str[j] = 'Z'
            H_list.append((''.join(pauli_str), Jz))

    # 磁场项
    if abs(hz) > 1e-12:
        for i in range(n):
            pauli_str = ['I'] * n
            pauli_str[i] = 'Z'
            H_list.append((''.join(pauli_str), hz))

    return SparsePauliOp.from_list(H_list)


if __name__ == "__main__":
    # 简单测试
    H = create_spin_chain_hamiltonian(4, 1.0, 1.0, 1.0, 0.5)
    print(f"Heisenberg(4): {len(H)} terms")