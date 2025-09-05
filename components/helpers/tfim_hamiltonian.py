"""
TFIM哈密顿量构建器 - QuantumForge vNext

实现横向场伊辛模型(TFIM)的哈密顿量构建功能。
"""

from qiskit.quantum_info import SparsePauliOp


def build_tfim_h(n, hx, j, boundary='periodic'):
    """
    构建TFIM哈密顿量
    
    H = -J * sum(Z_i * Z_{i+1}) - hx * sum(X_i)
    """
    pauli_list = []
    
    # 横向场项: -hx * sum(X_i)
    for i in range(n):
        pauli_str = ['I'] * n
        pauli_str[i] = 'X'
        pauli_list.append((''.join(pauli_str), -hx))
    
    # 耦合项: -J * sum(Z_i * Z_{i+1})
    for i in range(n):
        next_i = (i + 1) % n if boundary == 'periodic' else i + 1
        if boundary == 'open' and next_i >= n:
            continue
        pauli_str = ['I'] * n
        pauli_str[i] = 'Z'
        pauli_str[next_i] = 'Z'
        pauli_list.append((''.join(pauli_str), -j))
    
    return SparsePauliOp.from_list(pauli_list)


if __name__ == "__main__":
    # 简单测试
    H = build_tfim_h(4, 1.0, 1.0)
    print(f"TFIM(4,1,1): {len(H)} terms")