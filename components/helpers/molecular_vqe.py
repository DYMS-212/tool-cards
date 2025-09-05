"""
Molecular VQE Runner - QuantumForge vNext

VQE algorithm specifically for molecular electronic structure problems.
"""

from qiskit.primitives import Estimator
from qiskit_algorithms import VQE
from qiskit_algorithms.optimizers import L_BFGS_B


def run_molecular_vqe(qubit_hamiltonian, ansatz, maxiter=3000):
    """
    Run VQE calculation for molecular ground state energy
    
    Args:
        qubit_hamiltonian: Mapped molecular Hamiltonian
        ansatz: UCCSD ansatz circuit
        maxiter: Maximum optimization iterations
        
    Returns:
        tuple: (vqe_result, ground_state_energy)
    """
    # Setup estimator and optimizer
    estimator = Estimator()
    optimizer = L_BFGS_B(maxiter=maxiter)
    
    # Create and run VQE
    vqe = VQE(estimator, ansatz, optimizer)
    vqe_result = vqe.compute_minimum_eigenvalue(qubit_hamiltonian)
    
    # Extract ground state energy  
    energy = float(vqe_result.eigenvalue.real)
    
    print(f"VQE ground state energy: {energy:.6f} Ha")
    
    return vqe_result, energy


if __name__ == "__main__":
    print("Molecular VQE runner ready")