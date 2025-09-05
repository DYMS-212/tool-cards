"""
Molecular Hamiltonian Builder - QuantumForge vNext

Electronic structure calculation and qubit mapping for molecular systems.
"""

from qiskit_nature.units import DistanceUnit
from qiskit_nature.second_q.drivers import PySCFDriver
from qiskit_nature.second_q.mappers import JordanWignerMapper


def build_molecular_hamiltonian(molecule, basis_set, atom_string, charge=0, spin=0):
    """
    Build molecular Hamiltonian using electronic structure calculation
    
    Args:
        molecule: Molecule name (e.g. "LiH", "BeH2")
        basis_set: Basis set (e.g. "sto3g", "6-31g")
        atom_string: Atomic coordinates (e.g. "Li 0 0 0; H 0 0 0.735")
        charge: Molecular charge (default: 0)
        spin: Spin multiplicity (default: 0)
        
    Returns:
        tuple: (qubit_hamiltonian, es_problem, mapper)
    """
    # Create PySCF driver
    driver = PySCFDriver(
        atom=atom_string,
        basis=basis_set,
        charge=charge,
        spin=spin,
        unit=DistanceUnit.ANGSTROM,
    )
    
    # Run electronic structure calculation
    es_problem = driver.run()
    
    # Setup Jordan-Wigner mapper
    mapper = JordanWignerMapper()
    
    # Get second quantized Hamiltonian and map to qubits
    second_q_hamiltonian = es_problem.hamiltonian.second_q_op()
    qubit_hamiltonian = mapper.map(second_q_hamiltonian)
    
    return qubit_hamiltonian, es_problem, mapper


if __name__ == "__main__":
    # Simple test
    H, problem, mapper = build_molecular_hamiltonian("LiH", "sto3g", "Li 0 0 0; H 0 0 0.735")
    print(f"LiH: {H.num_qubits} qubits, {len(H)} terms")