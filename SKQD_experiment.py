# ─── Sweep parameters ───
from qiskit.transpiler import CouplingMap
from qiskit_addon_utils.problem_generators import generate_xyz_hamiltonian
import warnings
from qiskit import QuantumCircuit
from qiskit.circuit import QuantumRegister
from qiskit.circuit.library import PauliEvolutionGate
from qiskit.synthesis import LieTrotter
from qiskit import generate_preset_pass_manager
from qiskit_ibm_runtime import QiskitRuntimeService
from qiskit_ibm_runtime import SamplerV2 as Sampler
from qiskit_addon_sqd.counts import counts_to_arrays
from qiskit_addon_sqd.qubit import solve_qubit
from collections import Counter
from scipy.sparse.linalg import eigsh

import numpy as np
import matplotlib.pyplot as plt

num_spins   = 15
jxy_values  = np.linspace(0, 0.8, 9)  # 9 points from 0 to 0.8
jz          = 1.0

krylov_dim  = 5
dt          = 0.15
num_trotter = 5
shots       = 50_000  # reduce to save QPU credits, currently takes ~2 minutes


def exact_ground_state_energy(H_op, num_spins):
    """Classically diagonalize the full Hamiltonian - exact answer"""
    H_matrix = H_op.to_matrix(sparse=True)
    eigval, _ = eigsh(H_matrix, k=1, which='SA')
    return eigval[0]

service = QiskitRuntimeService()
backend = service.least_busy(operational=True, simulator=False)

# --------------------------
# Try with Fake backend first

# from qiskit_ibm_runtime.fake_provider import FakeBrisbane
# backend = FakeBrisbane()

pm = generate_preset_pass_manager(backend=backend, optimization_level=3)


skqd_energies = []
exact_energies = []

for jxy in jxy_values:
    print(f"\nRunning Jxy = {jxy:.3f}")

    # ── Coupling_constants sweeps Jxy ──
    coupling_map = CouplingMap.from_ring(num_spins)
    H_op = generate_xyz_hamiltonian(
        coupling_map,
        coupling_constants=(jxy, jxy, jz)  # <-- this is the key change
    )

    # ── Exact classical answer ──
    exact_en = exact_ground_state_energy(H_op, num_spins)
    exact_energies.append(exact_en)
    print(f"  Exact energy: {exact_en:.6f}")

    # ── Neel reference state ──
    qc_state_prep = QuantumCircuit(num_spins)
    for i in range(num_spins):
        if i % 2 == 0:
            qc_state_prep.x(i)

    # ── Build Krylov circuits ──
    evol_gate = PauliEvolutionGate(
        H_op,
        time=(dt / num_trotter),
        synthesis=LieTrotter(reps=num_trotter)
    )

    qr = QuantumRegister(num_spins)
    qc_evol = QuantumCircuit(qr)
    qc_evol.append(evol_gate, qargs=qr)

# I replaced the circuit-building loop with just the final Krylov vector to minimize QPU time
    circ = qc_state_prep.copy()
    for _ in range(krylov_dim - 1):      # apply U^(krylov_dim - 1) times
        circ.compose(other=qc_evol, inplace=True)
    circ.measure_all()

    isa_circuits = pm.run(circuits=[circ])   # list of 1
    sampler = Sampler(mode=backend)
    job = sampler.run([isa_circuits], shots=shots)

    counts = job.result()[0].data.meas.get_counts()   # single circuit result

    # ── Post-selection for 15 spins ──
    # 15 spins, ground state has 7 or 8 ones (odd system!)
    # Try both and take lower energy
    best_en = np.inf
    for num_ones in [7, 8]:  # <-- Change based on num_spins//2
        filtered = {
            b: c for b, c in counts.items()
            if b.count("1") == num_ones
        }
        if not filtered:
            continue
        bitstring_matrix, probs = counts_to_arrays(counts=filtered)
        eigenvals, _ = solve_qubit(
            bitstring_matrix, H_op,
            verbose=False, k=2, which='SA'
        )
        best_en = min(best_en, np.min(eigenvals))

    skqd_energies.append(best_en)
    print(f"  SKQD energy:  {best_en:.6f}")
    print(f"  Error:        {abs(best_en - exact_en)/abs(exact_en)*100:.2f}%")

errors = [
    abs(s - e) / abs(e) * 100
    for s, e in zip(skqd_energies, exact_energies)
]

fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(8, 8), sharex=True)

# Panel 1: Energies
ax1.plot(jxy_values, exact_energies, 'r-',  label='Exact (classical)')
ax1.plot(jxy_values, skqd_energies,  'b-.', label='SKQD (quantum)', marker='o')
ax1.set_ylabel('Ground State Energy')
ax1.set_title('XXZ Chain (N=15): SKQD vs Exact across Jxy')
ax1.legend()
ax1.grid(True)

# Panel 2: Error
ax2.plot(jxy_values, errors, 'g-', marker='s')
ax2.axvline(x=0.5, color='orange', linestyle='--', label='Jxy/Jz = 0.5')
ax2.set_xlabel('Jxy')
ax2.set_ylabel('Error (%)')
ax2.set_title('SKQD Error — expect degradation as Jxy → 1')
ax2.legend()
ax2.grid(True)

plt.tight_layout()
plt.savefig('xxz_sweep.png', dpi=150)
plt.show()