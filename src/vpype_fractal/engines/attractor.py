"""Strange attractor engines — Clifford, De Jong, and Lorenz."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

import numpy as np
import vpype as vp

from .paths import points_to_lines


@dataclass(frozen=True)
class AttractorDef:
    """Named attractor preset with fixed parameters."""

    kind: str  # "clifford", "dejong", or "lorenz"
    params: dict[str, float]


ATTRACTOR_PRESETS: dict[str, AttractorDef] = {
    # Clifford presets
    "butterfly": AttractorDef(kind="clifford", params={"a": -1.4, "b": 1.6, "c": 1.0, "d": 0.7}),
    "ribbon": AttractorDef(kind="clifford", params={"a": 1.7, "b": 1.7, "c": 0.6, "d": 1.2}),
    "swirl": AttractorDef(kind="clifford", params={"a": -1.7, "b": 1.3, "c": -0.1, "d": -1.21}),
    # De Jong presets
    "orbit": AttractorDef(kind="dejong", params={"a": 1.4, "b": -2.3, "c": 2.4, "d": -2.1}),
    "tangle": AttractorDef(kind="dejong", params={"a": -2.7, "b": -0.09, "c": -0.86, "d": -2.2}),
    "wings": AttractorDef(kind="dejong", params={"a": 0.97, "b": -1.9, "c": 1.38, "d": -1.5}),
    # Lorenz presets
    "lorenz-classic": AttractorDef(
        kind="lorenz",
        params={"sigma": 10.0, "rho": 28.0, "beta": 8.0 / 3.0, "dt": 0.005},
    ),
    "lorenz-tight": AttractorDef(
        kind="lorenz",
        params={"sigma": 10.0, "rho": 15.0, "beta": 8.0 / 3.0, "dt": 0.005},
    ),
}


def run_clifford(
    a: float,
    b: float,
    c: float,
    d: float,
    num_points: int,
    seed: int | None = None,
) -> np.ndarray:
    """Iterate the Clifford attractor.

    x_{n+1} = sin(a * y_n) + c * cos(a * x_n)
    y_{n+1} = sin(b * x_n) + d * cos(b * y_n)

    Args:
        a, b, c, d: Attractor parameters.
        num_points: Number of points to generate.
        seed: Random seed for initial position jitter.

    Returns:
        Array of complex numbers representing (x, y) points.
    """
    rng = np.random.default_rng(seed)
    x, y = rng.uniform(-0.1, 0.1), rng.uniform(-0.1, 0.1)
    points = np.empty(num_points, dtype=complex)

    # Transient
    for _ in range(100):
        x, y = np.sin(a * y) + c * np.cos(a * x), np.sin(b * x) + d * np.cos(b * y)

    for i in range(num_points):
        x, y = np.sin(a * y) + c * np.cos(a * x), np.sin(b * x) + d * np.cos(b * y)
        points[i] = complex(x, y)

    return points


def run_dejong(
    a: float,
    b: float,
    c: float,
    d: float,
    num_points: int,
    seed: int | None = None,
) -> np.ndarray:
    """Iterate the De Jong attractor.

    x_{n+1} = sin(a * y_n) - cos(b * x_n)
    y_{n+1} = sin(c * x_n) - cos(d * y_n)

    Args:
        a, b, c, d: Attractor parameters.
        num_points: Number of points to generate.
        seed: Random seed for initial position jitter.

    Returns:
        Array of complex numbers representing (x, y) points.
    """
    rng = np.random.default_rng(seed)
    x, y = rng.uniform(-0.1, 0.1), rng.uniform(-0.1, 0.1)
    points = np.empty(num_points, dtype=complex)

    for _ in range(100):
        x, y = np.sin(a * y) - np.cos(b * x), np.sin(c * x) - np.cos(d * y)

    for i in range(num_points):
        x, y = np.sin(a * y) - np.cos(b * x), np.sin(c * x) - np.cos(d * y)
        points[i] = complex(x, y)

    return points


def run_lorenz(
    sigma: float,
    rho: float,
    beta: float,
    dt: float,
    num_points: int,
    seed: int | None = None,
) -> np.ndarray:
    """Integrate the Lorenz system using RK4, projected to the XZ plane.

    dx/dt = sigma * (y - x)
    dy/dt = x * (rho - z) - y
    dz/dt = x * y - beta * z

    Args:
        sigma, rho, beta: Lorenz system parameters.
        dt: Integration time step.
        num_points: Number of points to output.
        seed: Random seed for initial position jitter.

    Returns:
        Array of complex numbers representing (x, z) points.
    """
    rng = np.random.default_rng(seed)
    x = rng.uniform(-0.1, 0.1) + 1.0
    y = rng.uniform(-0.1, 0.1) + 1.0
    z = rng.uniform(-0.1, 0.1) + 1.0

    def deriv(x: float, y: float, z: float) -> tuple[float, float, float]:
        return (
            sigma * (y - x),
            x * (rho - z) - y,
            x * y - beta * z,
        )

    def rk4_step(x: float, y: float, z: float) -> tuple[float, float, float]:
        dx1, dy1, dz1 = deriv(x, y, z)
        dx2, dy2, dz2 = deriv(x + dt / 2 * dx1, y + dt / 2 * dy1, z + dt / 2 * dz1)
        dx3, dy3, dz3 = deriv(x + dt / 2 * dx2, y + dt / 2 * dy2, z + dt / 2 * dz2)
        dx4, dy4, dz4 = deriv(x + dt * dx3, y + dt * dy3, z + dt * dz3)
        return (
            x + dt / 6 * (dx1 + 2 * dx2 + 2 * dx3 + dx4),
            y + dt / 6 * (dy1 + 2 * dy2 + 2 * dy3 + dy4),
            z + dt / 6 * (dz1 + 2 * dz2 + 2 * dz3 + dz4),
        )

    # Transient
    for _ in range(500):
        x, y, z = rk4_step(x, y, z)

    points = np.empty(num_points, dtype=complex)
    for i in range(num_points):
        x, y, z = rk4_step(x, y, z)
        points[i] = complex(x, z)

    return points


def smooth_trajectory(points: np.ndarray, samples_per_segment: int = 10) -> np.ndarray:
    """Interpolate a discrete trajectory with a cubic spline.

    Fits a parametric cubic spline through the trajectory points and
    resamples at higher resolution, converting sharp angles between
    discrete map iterations into smooth flowing curves.

    Args:
        points: Array of complex trajectory points.
        samples_per_segment: Interpolated points per original segment.

    Returns:
        Smoothed trajectory as a complex array.
    """
    from scipy.interpolate import CubicSpline

    n = len(points)
    if n < 4:
        return points

    t = np.arange(n)
    t_fine = np.linspace(0, n - 1, (n - 1) * samples_per_segment + 1)

    cs_x = CubicSpline(t, points.real)
    cs_y = CubicSpline(t, points.imag)

    return cs_x(t_fine) + 1j * cs_y(t_fine)


_RUNNERS: dict[str, Callable[..., np.ndarray]] = {
    "clifford": lambda p, n, s: run_clifford(p["a"], p["b"], p["c"], p["d"], n, s),
    "dejong": lambda p, n, s: run_dejong(p["a"], p["b"], p["c"], p["d"], n, s),
    "lorenz": lambda p, n, s: run_lorenz(p["sigma"], p["rho"], p["beta"], p.get("dt", 0.005), n, s),
}


def attractor_to_lines(
    kind: str,
    params: dict[str, float],
    num_points: int,
    seed: int | None = None,
    segment_length: int = 500,
) -> vp.LineCollection:
    """Generate attractor as plotter-friendly line segments.

    Args:
        kind: Attractor type ("clifford", "dejong", or "lorenz").
        params: Parameter dict for the chosen attractor.
        num_points: Total points to generate.
        seed: Random seed for reproducibility.
        segment_length: Maximum points per path segment.

    Returns:
        A LineCollection of path segments.
    """
    runner = _RUNNERS[kind]
    points = runner(params, num_points, seed)
    # Discrete maps use nearest-neighbor sort for density-based rendering;
    # continuous ODEs keep trajectory order.
    use_sort = kind in ("clifford", "dejong")
    return points_to_lines(points, segment_length=segment_length, sort=use_sort)
