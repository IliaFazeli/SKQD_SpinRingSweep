# XXZ Spin Chain: SKQD Phase Sweep

I study a 15-site XXZ antiferromagnetic spin-1/2 chain with the following Hamiltonian:

$$H = \sum_{\langle i,j \rangle} J_{xy}(X_iX_j + Y_iY_j) + J_z Z_iZ_j$$

where the sum runs over nearest-neighbor pairs on a periodic ring. The $Z_iZ_j$ term enforces antiferromagnetic ordering (neighboring spins prefer opposite alignment), while the $X_iX_j + Y_iY_j$ terms introduce quantum fluctuations that cause spins to flip cooperatively, driving the system away from a classical Néel state into a genuine quantum superposition. 

The system is solved using Sample-based Krylov Quantum Diagonalization (SKQD) on IBM Quantum hardware (ibm_fez), with $J_z = 1.0$ fixed and $J_{xy}$ swept from 0 to 0.8 to assess hardware performance as entanglement increases. Ground state energies are compared against exact classical diagonalization of the full $2^{15} = 32{,}768$ dimensional Hilbert space.

Note: this project is an extension of the IBM Quantum notebook on SKQD and is highly similar to their setup: https://quantum.cloud.ibm.com/learning/en/courses/quantum-diagonalization-algorithms/skqd


**Physical significance of $J_{xy}$:** At $J_{xy} = 0$ the model reduces to the classical Ising chain, whose ground state is exactly the Néel state $|\uparrow\downarrow\uparrow\downarrow...\rangle$ — a simple, sparse, unentangled configuration that SKQD handles trivially. As $J_{xy}$ increases, quantum fluctuations grow stronger, the ground state becomes a broad superposition of many spin configurations, and the wave function loses the sparsity that SKQD relies on. At $J_{xy} = J_z = 1.0$ the system reaches the isotropic **Heisenberg point** — a quantum critical point with maximum entanglement and no simple classical description. Sweeping $J_{xy}$ therefore traces a path from a regime where quantum hardware has every advantage, to one where it is most severely tested.

Note: the 15-site ring has an **odd number of sites**, which introduces geometric frustration — the antiferromagnetic ordering cannot tile perfectly around the ring, forcing one bond to be ferromagnetically aligned. This raises the ground state energy relative to an even chain (observed: $E_0 = -13.0$ at $J_{xy} = 0$ rather than $-15.0$) and is physically interesting in its own right.

## Results

![XXZ Sweep Results](xxz_sweep.png)

SKQD tracks exact diagonalization well for $J_{xy} < 0.3$, with increasing error as quantum fluctuations broaden the ground state wave function toward the Heisenberg point. 

Interestingly, the error plot shows a reproducible spike at $J_{xy} = 0.5 - 0.6$ regardless of shot count and even when using statevector simulator (which will not be included in this repo). A plausible explanation is that $J_{xy}/J_z = 0.5$ sits near a crossover in the structure of the ground state wave function — the Néel-state reference $|\psi_0\rangle$ loses overlap with the true ground state non-smoothly at this ratio, causing the sampled bitstrings to miss a significant portion of the ground state support in a single step. This deserves further investigation, for example by checking whether the spike persists with a larger Krylov dimension or a different reference state.

## Known Limitations & Future Work

This experiment samples only the highest-order Krylov vector $U^{r-1}|\psi\rangle$ rather than aggregating all $r$ vectors as full SKQD prescribes, due to QPU allocation constraints. This means:

- The subspace is less rich than true SKQD
- Accuracy at high $J_{xy}$ is likely underestimated
- Full Krylov loop results would be expected to show lower error across the sweep

The degradation trend observed is nonetheless physically meaningful and consistent with theoretical predictions about wave function sparsity breaking down near the Heisenberg point ($J_{xy} \rightarrow J_z$).

**Future work:**
- Rerun with full Krylov aggregation on a noise-free simulator to isolate algorithmic vs hardware error
- Extend sweep to $J_{xy} = 1.0$ to capture the full Heisenberg point
- Investigate the anomalous error spike at $J_{xy} = 0.5$ with varying Krylov dimension and reference states
- Apply dynamical decoupling and readout error mitigation to improve QPU accuracy
- Scale to larger system sizes (N = 20+) where classical exact diagonalization becomes intractable

## Requirements

```bash
pip install qiskit qiskit-ibm-runtime qiskit-addon-sqd qiskit-addon-utils scipy matplotlib
```

## Usage

Save your IBM Quantum credentials once:
```python
from qiskit_ibm_runtime import QiskitRuntimeService
QiskitRuntimeService.save_account(token="your_token_here", overwrite=True)
```

Then run:
```bash
python SKQD_experiment.py
```

Results are saved to `xxz_sweep.png`.

## References

- Yu et al., "Quantum-Centric Algorithm for Sample-Based Krylov Diagonalization" (2025). [arXiv:2501.09702](https://arxiv.org/abs/2501.09702)
- Epperly, Lin, Nakatsukasa, "A theory of quantum subspace diagonalization", SIAM Journal on Matrix Analysis and Applications (2022)
- IBM Quantum Learning: [Quantum Diagonalization Algorithms](https://quantum.cloud.ibm.com/learning/courses/quantum-diagonalization-algorithms)
