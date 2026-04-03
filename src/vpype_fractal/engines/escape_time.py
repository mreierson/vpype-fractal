"""Escape-time computation for Mandelbrot and Julia set fractals."""

import numpy as np


def mandelbrot_grid(
    x_min: float,
    x_max: float,
    y_min: float,
    y_max: float,
    resolution: int,
    max_iter: int,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Compute escape-time values for the Mandelbrot set on a grid.

    Args:
        x_min, x_max: Real axis bounds.
        y_min, y_max: Imaginary axis bounds.
        resolution: Number of grid points along the longest axis.
        max_iter: Maximum iteration count.

    Returns:
        Tuple of (x_coords, y_coords, escape_times) where escape_times
        is a 2D array of shape (ny, nx) with smooth iteration counts.
    """
    x, y, c = _make_grid(x_min, x_max, y_min, y_max, resolution)
    z = np.zeros_like(c)
    escape = _iterate(z, c, max_iter)
    return x, y, escape


def julia_grid(
    cx: float,
    cy: float,
    x_min: float,
    x_max: float,
    y_min: float,
    y_max: float,
    resolution: int,
    max_iter: int,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Compute escape-time values for a Julia set on a grid.

    Args:
        cx, cy: Real and imaginary parts of the Julia constant c.
        x_min, x_max: Real axis bounds of the z-plane.
        y_min, y_max: Imaginary axis bounds of the z-plane.
        resolution: Number of grid points along the longest axis.
        max_iter: Maximum iteration count.

    Returns:
        Tuple of (x_coords, y_coords, escape_times).
    """
    x, y, z = _make_grid(x_min, x_max, y_min, y_max, resolution)
    c = np.full_like(z, complex(cx, cy))
    escape = _iterate(z, c, max_iter)
    return x, y, escape


def _make_grid(
    x_min: float,
    x_max: float,
    y_min: float,
    y_max: float,
    resolution: int,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Build the complex plane grid, returning (x, y, grid)."""
    if x_min >= x_max or y_min >= y_max:
        raise ValueError(
            f"Bounds must satisfy min < max, got x=[{x_min}, {x_max}], y=[{y_min}, {y_max}]"
        )

    aspect = (y_max - y_min) / (x_max - x_min)
    nx = resolution
    ny = max(1, int(resolution * aspect))

    x = np.linspace(x_min, x_max, nx)
    y = np.linspace(y_min, y_max, ny)
    gx, gy = np.meshgrid(x, y)
    return x, y, gx + 1j * gy


def _iterate(
    z: np.ndarray,
    c: np.ndarray,
    max_iter: int,
) -> np.ndarray:
    """Run z = z^2 + c iteration with smooth escape-time coloring."""
    escape = np.full(z.shape, float(max_iter), dtype=np.float64)

    for i in range(max_iter):
        abs_z = np.abs(z)
        mask = abs_z <= 2.0
        if not np.any(mask):
            break
        z[mask] = z[mask] ** 2 + c[mask]

        # Detect newly escaped points using updated z
        abs_z_new = np.abs(z)
        newly_escaped = (abs_z_new > 2.0) & (escape == max_iter)
        if np.any(newly_escaped):
            # Smooth iteration count — clamp log inputs to avoid NaN
            log_zn = np.log(np.maximum(abs_z_new[newly_escaped], 2.0)) / 2.0
            nu = np.log(np.maximum(log_zn / np.log(2.0), 1e-10)) / np.log(2.0)
            escape[newly_escaped] = i + 1 - np.clip(nu, 0.0, 1.0)

    return escape
