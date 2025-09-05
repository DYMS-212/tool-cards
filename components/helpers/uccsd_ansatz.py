"""
UCCSD Ansatz Builder - QuantumForge vNext

Unitary Coupled Cluster Singles and Doubles ansatz for molecular systems.
"""

from qiskit_nature.second_q.circuit.library import UCCSD, HartreeFock


def build_uccsd_ansatz(es_problem, mapper):
    """
    Build UCCSD ansatz with Hartree-Fock initial state
    
    Args:
        es_problem: Electronic structure problem from driver
        mapper: Fermion-to-qubit mapper (e.g. JordanWignerMapper)
        
    Returns:
        QuantumCircuit: UCCSD ansatz circuit
    """
    # Create Hartree-Fock initial state
    hf_state = HartreeFock(
        es_problem.num_spatial_orbitals,
        es_problem.num_particles,
        mapper,
    )
    
    # Build UCCSD ansatz
    ansatz = UCCSD(
        es_problem.num_spatial_orbitals,
        es_problem.num_particles,
        mapper,
        initial_state=hf_state,
    )
    
    return ansatz


if __name__ == "__main__":
    # Test requires molecular data - see molecular_hamiltonian.py
    print("UCCSD ansatz builder ready")