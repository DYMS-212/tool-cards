#!/usr/bin/env python3
"""
QuantumForge vNext Simple Demo
Tests all three quantum systems: TFIM, Heisenberg, and Molecular
"""

from quantum_forge_v5 import run_and_save

# TFIM System
# tfim_query = """I would like to compute the ground state energy of a 12-qubit transverse-field Ising model (TFIM) with coupling strength J=1.2, transverse field h=0.8, using periodic boundary conditions. Please implement a VQE algorithm with a Hamiltonian-informed ansatz that incorporates ZZ interactions and X field layers, with 4 repetitions for the ansatz depth. Use COBYLA optimizer with maximum 2000 iterations for high-precision results. Please provide complete, ready-to-run Python code using the latest Qiskit API."""

# print("=== TESTING TFIM SYSTEM ===")
# code = run_and_save(tfim_query, "test_tfim.py", debug=True)

# Heisenberg System  
# heisenberg_query = """I would like to compute the ground state energy of a 10-qubit Heisenberg spin chain model with anisotropic coupling parameters: Jx=1.0, Jy=1.0, Jz=1.5 (favoring Z interactions), and an external magnetic field hz=0.3 in the Z direction. Use open boundary conditions for this finite chain. Please implement VQE with a Heisenberg-specific ansatz that respects the model's symmetries, using 3 layers for sufficient expressivity. Apply COBYLA optimizer with maximum 1500 iterations for convergence. Please provide complete, ready-to-run Python code using the latest Qiskit API."""

# print("=== TESTING HEISENBERG SYSTEM ===")
# code2 = run_and_save(heisenberg_query, "test_heisenberg.py", debug=True)

# Molecular System
molecular_query = """I would like to compute the ground state energy of H4 molecule using VQE methods. The molecule has basis set STO-3G and geometry with layout: linear, spacing: 0.74.\nPlease provide complete, ready-to-run Python code for molecular electronic structure calculation. Please use the lateset Qiskit and other relevant packages. with the latest API."""

print("=== TESTING MOLECULAR SYSTEM ===")
code3 = run_and_save(molecular_query, "test_molecular.py", debug=True)