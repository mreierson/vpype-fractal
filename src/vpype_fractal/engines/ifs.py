"""Iterated Function System (IFS) engine."""

from dataclasses import dataclass

import numpy as np
import vpype as vp

from .paths import points_to_lines


@dataclass(frozen=True)
class AffineTransform:
    """A 2D affine transform with associated probability weight."""

    a: float
    b: float
    c: float
    d: float
    e: float
    f: float
    weight: float


@dataclass(frozen=True)
class IFSDef:
    """Definition of an IFS fractal."""

    transforms: list[AffineTransform]


IFS_PRESETS: dict[str, IFSDef] = {
    "fern": IFSDef(
        transforms=[
            AffineTransform(a=0.0, b=0.0, c=0.0, d=0.16, e=0.0, f=0.0, weight=0.01),
            AffineTransform(a=0.85, b=0.04, c=-0.04, d=0.85, e=0.0, f=1.6, weight=0.85),
            AffineTransform(a=0.2, b=-0.26, c=0.23, d=0.22, e=0.0, f=1.6, weight=0.07),
            AffineTransform(a=-0.15, b=0.28, c=0.26, d=0.24, e=0.0, f=0.44, weight=0.07),
        ]
    ),
    "sierpinski-ifs": IFSDef(
        transforms=[
            AffineTransform(a=0.5, b=0.0, c=0.0, d=0.5, e=0.0, f=0.0, weight=1.0),
            AffineTransform(a=0.5, b=0.0, c=0.0, d=0.5, e=0.5, f=0.0, weight=1.0),
            AffineTransform(a=0.5, b=0.0, c=0.0, d=0.5, e=0.25, f=0.433, weight=1.0),
        ]
    ),
    "maple": IFSDef(
        transforms=[
            AffineTransform(a=0.14, b=0.01, c=0.0, d=0.51, e=-0.08, f=-1.31, weight=0.10),
            AffineTransform(a=0.43, b=0.52, c=-0.45, d=0.50, e=1.49, f=-0.75, weight=0.35),
            AffineTransform(a=0.45, b=-0.49, c=0.47, d=0.47, e=-1.62, f=-0.74, weight=0.35),
            AffineTransform(a=0.49, b=0.0, c=0.0, d=0.51, e=0.02, f=1.62, weight=0.20),
        ]
    ),
    "crystal": IFSDef(
        transforms=[
            AffineTransform(a=0.35, b=0.0, c=0.0, d=0.35, e=0.0, f=-0.5, weight=1.0),
            AffineTransform(a=0.35, b=0.0, c=0.0, d=0.35, e=0.4755, f=-0.1545, weight=1.0),
            AffineTransform(a=0.35, b=0.0, c=0.0, d=0.35, e=0.2939, f=0.4045, weight=1.0),
            AffineTransform(a=0.35, b=0.0, c=0.0, d=0.35, e=-0.2939, f=0.4045, weight=1.0),
            AffineTransform(a=0.35, b=0.0, c=0.0, d=0.35, e=-0.4755, f=-0.1545, weight=1.0),
            AffineTransform(a=0.35, b=0.0, c=0.0, d=0.35, e=0.0, f=0.0, weight=1.0),
        ]
    ),
}


def run_ifs(
    transforms: list[AffineTransform],
    num_points: int,
    seed: int | None = None,
) -> np.ndarray:
    """Run the chaos game for an IFS, returning an array of 2D points.

    Args:
        transforms: List of affine transforms with probability weights.
        num_points: Number of points to generate.
        seed: Random seed for reproducibility.

    Returns:
        Array of complex numbers representing (x, y) points.

    Raises:
        ValueError: If any weight is negative or all weights are zero.
    """
    weights = np.array([t.weight for t in transforms])
    if np.any(weights < 0):
        raise ValueError("Transform weights must not be negative.")
    if weights.sum() == 0:
        raise ValueError("At least one transform weight must be positive.")

    rng = np.random.default_rng(seed)

    probs = weights / weights.sum()

    total = num_points + 20
    indices = rng.choice(len(transforms), size=total, p=probs)

    a = np.array([t.a for t in transforms])
    b = np.array([t.b for t in transforms])
    c = np.array([t.c for t in transforms])
    d = np.array([t.d for t in transforms])
    e = np.array([t.e for t in transforms])
    f = np.array([t.f for t in transforms])

    x, y = 0.0, 0.0
    points = np.empty(num_points, dtype=complex)

    for j in range(20):
        idx = indices[j]
        x, y = a[idx] * x + b[idx] * y + e[idx], c[idx] * x + d[idx] * y + f[idx]

    for i in range(num_points):
        idx = indices[i + 20]
        x, y = a[idx] * x + b[idx] * y + e[idx], c[idx] * x + d[idx] * y + f[idx]
        points[i] = complex(x, y)

    return points


def ifs_to_lines(
    transforms: list[AffineTransform],
    num_points: int,
    seed: int | None = None,
    segment_length: int = 500,
) -> vp.LineCollection:
    """Generate IFS fractal as line segments for plotter output.

    Runs the chaos game, then sorts points via nearest-neighbor traversal
    so the pen traces spatially coherent paths that reveal the fractal
    structure. Paths are broken at large spatial gaps.

    Args:
        transforms: List of affine transforms with probability weights.
        num_points: Total number of points to generate.
        seed: Random seed for reproducibility.
        segment_length: Maximum points per path segment.

    Returns:
        A LineCollection of path segments.
    """
    points = run_ifs(transforms, num_points, seed)
    return points_to_lines(points, segment_length=segment_length)
