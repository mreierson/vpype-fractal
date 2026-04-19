"""Escape-time computation for Mandelbrot and Julia set fractals."""

import numpy as np

# Large escape radius for smooth iteration counting — the log-log
# interpolation needs |z| >> R to produce smooth gradients.
_ESCAPE_RADIUS = 256.0
_LOG_ESCAPE_RADIUS = np.log(_ESCAPE_RADIUS)


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
    """Run z = z^2 + c iteration with smooth escape-time coloring.

    Uses a large escape radius so the log-log interpolation produces
    continuous (band-free) iteration counts.
    """
    escape = np.full(z.shape, float(max_iter), dtype=np.float64)

    for i in range(max_iter):
        abs_z = np.abs(z)
        mask = abs_z <= _ESCAPE_RADIUS
        if not np.any(mask):
            break
        z[mask] = z[mask] ** 2 + c[mask]

        # Detect newly escaped points using updated z
        abs_z_new = np.abs(z)
        newly_escaped = (abs_z_new > _ESCAPE_RADIUS) & (escape == max_iter)
        if np.any(newly_escaped):
            # Continuous (smooth) iteration count:
            #   mu = n + 1 - log(log|z_n|) / log(2)
            # normalised against the escape radius so mu stays in [0, max_iter].
            log_zn = np.log(abs_z_new[newly_escaped])
            nu = np.log(log_zn / _LOG_ESCAPE_RADIUS) / np.log(2.0)
            escape[newly_escaped] = i + 1 - nu

    return escape
