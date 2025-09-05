"""
VQE模板函数 - QuantumForge vNext

实现VQE算法的基础模板功能。
"""

from qiskit_algorithms import VQE
from qiskit_algorithms.optimizers import COBYLA, L_BFGS_B
from qiskit.primitives import Estimator


def create_cobyla_optimizer(maxiter=1000):
    """创建COBYLA优化器"""
    return COBYLA(maxiter=maxiter)


def create_l_bfgs_b_optimizer(maxiter=1000):
    """创建L-BFGS-B优化器"""
    return L_BFGS_B(maxiter=maxiter)


def create_estimator():
    """创建Estimator原语"""
    return Estimator()

def run_vqe(hamiltonian, ansatz, optimizer, estimator):
    """
    运行VQE算法计算基态能量
    
    Args:
        hamiltonian: 量子哈密顿量
        ansatz: 变分电路ansatz
        optimizer: 优化器实例
        estimator: Estimator原语实例
    """
    # 运行VQE
    vqe = VQE(estimator, ansatz, optimizer)
    result = vqe.compute_minimum_eigenvalue(hamiltonian)
    energy = float(result.eigenvalue.real)
    print(f"VQE ground state energy: {energy:.6f}")
    return energy





if __name__ == "__main__":
    # 简单测试
    opt = create_cobyla_optimizer()
    est = create_estimator()
    print(f"VQE components: optimizer={type(opt).__name__}, estimator={type(est).__name__}")