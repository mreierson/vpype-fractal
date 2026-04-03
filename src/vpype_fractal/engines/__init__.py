"""Fractal generation engines."""

from .attractor import (
    ATTRACTOR_PRESETS,
    AttractorDef,
    attractor_to_lines,
    run_clifford,
    run_dejong,
    run_lorenz,
    smooth_trajectory,
)
from .contour import extract_contours, extract_contours_by_level
from .escape_time import julia_grid, mandelbrot_grid
from .geometric import build_carpet, build_sierpinski_triangle, build_tree
from .ifs import IFS_PRESETS, AffineTransform, IFSDef, ifs_to_lines, run_ifs
from .lsystem import expand
from .paths import nearest_neighbor_sort, points_to_lines
from .turtle import turtle_to_lines

__all__ = [
    "ATTRACTOR_PRESETS",
    "AffineTransform",
    "AttractorDef",
    "IFSDef",
    "IFS_PRESETS",
    "attractor_to_lines",
    "smooth_trajectory",
    "build_carpet",
    "build_sierpinski_triangle",
    "build_tree",
    "expand",
    "extract_contours",
    "extract_contours_by_level",
    "ifs_to_lines",
    "julia_grid",
    "mandelbrot_grid",
    "nearest_neighbor_sort",
    "points_to_lines",
    "run_clifford",
    "run_dejong",
    "run_ifs",
    "run_lorenz",
    "turtle_to_lines",
]
