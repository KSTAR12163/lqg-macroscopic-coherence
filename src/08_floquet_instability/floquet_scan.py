import numpy as np
from scipy.linalg import expm, eig
from dataclasses import dataclass
from typing import Tuple, Dict, Any, List


@dataclass
class FloquetScanConfig:
    # Base two-level Hamiltonian parameters (in energy units)
    delta: float  # detuning between levels (E2 - E1)
    g0: float     # static coupling

    # Drive: g(t) = g0 * (1 + A * cos(omega t))
    amplitude: float
    omega: float

    # Optional PT-symmetric gain/loss: Gamma(t) on levels ±i*Gamma/2
    # If gamma_gain > 0, non-Hermitian terms are added to test instability
    gamma_gain: float = 0.0

    # Integration controls
    steps_per_period: int = 200
    periods: int = 50


def two_level_hamiltonian(delta: float, g: float, gamma_gain: float = 0.0) -> np.ndarray:
    """
    Construct an effective two-level Hamiltonian:
    H = [[-delta/2, g], [g, +delta/2]] - i * diag([+gamma/2, -gamma/2])

    gamma_gain models PT-symmetric gain/loss; gamma=0 recovers Hermitian case.
    """
    H = np.array([[-0.5 * delta, g], [g, 0.5 * delta]], dtype=complex)
    if gamma_gain != 0.0:
        # PT-symmetric gain/loss: level 1 has +i*gamma/2, level 2 has -i*gamma/2
        nonherm = -1j * np.array([[+0.5 * gamma_gain, 0.0], [0.0, -0.5 * gamma_gain]])
        H = H + nonherm
    return H


def floquet_monodromy(config: FloquetScanConfig) -> np.ndarray:
    """
    Compute the monodromy (one-period evolution operator) for a driven two-level system
    with optional PT gain/loss.
    """
    T = 2 * np.pi / config.omega
    dt = T / config.steps_per_period
    U = np.eye(2, dtype=complex)
    t = 0.0
    for _ in range(config.steps_per_period):
        g_t = config.g0 * (1.0 + config.amplitude * np.cos(config.omega * t))
        H_t = two_level_hamiltonian(config.delta, g_t, config.gamma_gain)
        U = expm(-1j * H_t * dt) @ U
        t += dt
    return U


def floquet_growth_rate(config: FloquetScanConfig) -> Tuple[float, Dict[str, Any]]:
    """
    Return the maximal growth rate per period:
    growth = max(log |lambda_i|) where lambda_i are eigenvalues of monodromy U_T.

    For Hermitian systems, |lambda_i|=1 → growth=0. Positive growth implies instability.
    """
    U = floquet_monodromy(config)
    vals, _ = eig(U)
    mags = np.abs(vals)
    growth = float(np.max(np.log(mags + 1e-300)))
    return growth, {"eigs": vals, "mags": mags}


def floquet_scan_two_level(
    delta_grid: np.ndarray,
    omega_grid: np.ndarray,
    amplitude_grid: np.ndarray,
    g0: float,
    gamma_gain: float = 0.0,
    steps_per_period: int = 200,
    periods: int = 50,
) -> Dict[str, Any]:
    """
    Scan parameter grids and return a dictionary with growth map and best point.
    """
    growth_map = np.zeros((len(delta_grid), len(omega_grid), len(amplitude_grid)))

    best = {
        "growth": -np.inf,
        "delta": None,
        "omega": None,
        "amplitude": None,
        "details": None,
    }

    for i, delta in enumerate(delta_grid):
        for j, omega in enumerate(omega_grid):
            for k, amp in enumerate(amplitude_grid):
                cfg = FloquetScanConfig(
                    delta=delta,
                    g0=g0,
                    amplitude=amp,
                    omega=omega,
                    gamma_gain=gamma_gain,
                    steps_per_period=steps_per_period,
                    periods=periods,
                )
                growth, details = floquet_growth_rate(cfg)
                growth_map[i, j, k] = growth
                if growth > best["growth"]:
                    best = {
                        "growth": growth,
                        "delta": delta,
                        "omega": omega,
                        "amplitude": amp,
                        "details": details,
                    }

    return {"growth_map": growth_map, "best": best}
