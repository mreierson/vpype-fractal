"""Shared utilities for fractal commands."""

from __future__ import annotations

import numpy as np
import vpype as vp

from vpype_fractal.engines import expand, turtle_to_lines
from vpype_fractal.engines.contour import extract_contours_by_level
from vpype_fractal.presets import PRESETS


def generate_lsystem_fractal(
    preset_name: str,
    depth: int,
    size: float,
) -> vp.LineCollection:
    """Generate an L-system fractal from a named preset, scaled to fit size.

    Args:
        preset_name: Key in the PRESETS dictionary.
        depth: Number of L-system expansion iterations.
        size: Target bounding dimension in vpype units.

    Returns:
        A LineCollection containing the fractal paths.
    """
    preset = PRESETS[preset_name]
    instructions = expand(preset.axiom, preset.rules, depth)
    lc = turtle_to_lines(
        instructions,
        angle=preset.angle,
        step=1.0,
        heading=preset.heading,
    )
    return scale_to_size(lc, size)


def scale_to_size(lc: vp.LineCollection, size: float) -> vp.LineCollection:
    """Scale a LineCollection to fit within the given size, placed at origin."""
    if len(lc) == 0:
        return lc

    bounds = lc.bounds()
    if bounds is None:
        return lc

    x_min, y_min, x_max, y_max = bounds
    width = x_max - x_min
    height = y_max - y_min
    max_dim = max(width, height)

    if max_dim == 0:
        return lc

    scale = size / max_dim
    lc.scale(scale)

    # Translate so bounding box starts at origin
    bounds = lc.bounds()
    if bounds is not None:
        lc.translate(-bounds[0], -bounds[1])

    return lc


def scale_all_to_size(
    collections: list[vp.LineCollection],
    size: float,
) -> list[vp.LineCollection]:
    """Scale multiple LineCollections uniformly to fit within size.

    Computes a single bounding box across all collections and applies
    the same scale/translate to each, preserving relative positions.
    """
    # Find global bounds
    all_bounds = [lc.bounds() for lc in collections if len(lc) > 0]
    valid = [b for b in all_bounds if b is not None]
    if not valid:
        return collections

    x_min = min(b[0] for b in valid)
    y_min = min(b[1] for b in valid)
    x_max = max(b[2] for b in valid)
    y_max = max(b[3] for b in valid)

    width = x_max - x_min
    height = y_max - y_min
    max_dim = max(width, height)
    if max_dim == 0:
        return collections

    factor = size / max_dim
    for lc in collections:
        if len(lc) > 0:
            lc.scale(factor)
            lc.translate(-x_min * factor, -y_min * factor)

    return collections


def generate_escape_time_fractal(
    doc: vp.Document,
    x: np.ndarray,
    y: np.ndarray,
    escape: np.ndarray,
    max_iter: int,
    levels: int,
    size: float,
) -> vp.Document:
    """Build contour layers from escape-time data and add them to a document.

    Creates one layer per contour level. Use ``penset ... colorize`` in the
    vpype pipeline to assign colors.

    Args:
        doc: Target vpype Document.
        x: 1D array of x coordinates.
        y: 1D array of y coordinates.
        escape: 2D escape-time array.
        max_iter: Maximum iteration count used during computation.
        levels: Number of contour levels to extract.
        size: Target bounding dimension in vpype units.

    Returns:
        The document with contour layers added.
    """
    level_values = np.linspace(1, max_iter * 0.8, levels).tolist()

    # Skip ~5% of boundary cells to prevent edge artifacts from
    # incomplete contour lines at the viewport border
    grid_margin = max(2, escape.shape[1] // 20)

    level_lcs = extract_contours_by_level(x, y, escape, level_values, margin=grid_margin)
    non_empty = [lc for lc in level_lcs if len(lc) > 0]
    if non_empty:
        scale_all_to_size(non_empty, size)
        for lc in non_empty:
            doc[doc.free_id()] = lc

    return doc


def generate_density_contours(
    doc: vp.Document,
    points: np.ndarray,
    resolution: int,
    levels: int,
    size: float,
) -> vp.Document:
    """Build density contours from a point cloud and add to document.

    Bins points into a 2D histogram, applies Gaussian smoothing, then
    extracts iso-density contour lines — the same approach as escape-time
    fractals but using point density as the scalar field.

    Args:
        doc: Target vpype Document.
        points: Array of complex numbers from an attractor.
        resolution: Grid resolution for the density histogram.
        levels: Number of contour levels to extract.
        size: Target bounding dimension in vpype units.

    Returns:
        The document with density contour layers added.
    """
    from scipy.ndimage import gaussian_filter

    x_vals = points.real
    y_vals = points.imag

    # Build 2D histogram
    aspect = (y_vals.max() - y_vals.min()) / (x_vals.max() - x_vals.min())
    nx = resolution
    ny = max(1, int(resolution * aspect))

    density, x_edges, y_edges = np.histogram2d(x_vals, y_vals, bins=[nx, ny])
    density = density.T  # histogram2d returns (nx, ny), contour expects (ny, nx)

    # Smooth to produce clean contour lines
    density = gaussian_filter(density, sigma=1.5)

    # Build coordinate arrays (bin centers)
    x = (x_edges[:-1] + x_edges[1:]) / 2
    y = (y_edges[:-1] + y_edges[1:]) / 2

    # Extract contours at evenly spaced density levels, skipping zero
    max_density = density.max()
    if max_density <= 0:
        return doc

    level_values = np.linspace(max_density * 0.02, max_density * 0.8, levels).tolist()

    grid_margin = max(2, nx // 20)
    level_lcs = extract_contours_by_level(x, y, density, level_values, margin=grid_margin)
    non_empty = [lc for lc in level_lcs if len(lc) > 0]
    if non_empty:
        scale_all_to_size(non_empty, size)
        for lc in non_empty:
            doc[doc.free_id()] = lc

    return doc


def generate_attractor_layers(
    doc: vp.Document,
    points: np.ndarray,
    layers: int,
    size: float,
    smooth: int = 0,
) -> vp.Document:
    """Split attractor trajectory into layers and add to document.

    Divides the point sequence into ``layers`` equal chunks. Each chunk
    is drawn as a continuous trajectory. When ``smooth`` > 0, a cubic
    spline is fitted through each chunk to produce flowing curves.
    Use ``penset ... colorize`` to assign a color gradient along the orbit.

    Args:
        doc: Target vpype Document.
        points: Trajectory points in sequential order.
        layers: Number of layers to split into.
        size: Target bounding dimension in vpype units.
        smooth: Interpolated samples per segment (0 = no smoothing).

    Returns:
        The document with trajectory layers added.
    """
    from vpype_fractal.engines.attractor import smooth_trajectory

    max_polyline = 5000
    chunks = np.array_split(points, layers)
    lcs: list[vp.LineCollection] = []
    for chunk in chunks:
        if len(chunk) < 2:
            continue
        if smooth > 0:
            chunk = smooth_trajectory(chunk, samples_per_segment=smooth)
        lc = vp.LineCollection()
        for start in range(0, len(chunk), max_polyline - 1):
            seg = chunk[start : start + max_polyline]
            if len(seg) >= 2:
                lc.append(seg)
        lcs.append(lc)

    if lcs:
        scale_all_to_size(lcs, size)
        for lc in lcs:
            doc[doc.free_id()] = lc

    return doc
