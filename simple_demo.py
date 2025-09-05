#!/usr/bin/env python3
"""
QuantumForge vNext 简单Demo
输入查询 → 自动运行 → 显示结果
"""

from quantum_forge_v5 import run_and_save

def demo():
    # 你的英文查询
    query = "I would like to compute the ground state energy of a 8-qubit Heisenberg model .\nPlease provide complete, ready-to-run Python code. Please use the lateset Qiskit and other relevant packages. with the latest API."
    
    print("🚀 QuantumForge vNext Demo")
    print(f"📝 查询: {query}")
    print()
    
    # 自动运行
    print("🤖 运行中...")
    code = run_and_save(query, "demo_output.py", debug=True)
    
    print("✅ 完成!")
    print(f"📄 生成代码: demo_output.py ({len(code)}字符)")

if __name__ == "__main__":
    demo()