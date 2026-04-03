"""Shared utilities for converting point clouds to plotter-friendly paths."""

import numpy as np
import vpype as vp


def points_to_lines(
    points: np.ndarray,
    segment_length: int = 500,
    gap_percentile: float = 95.0,
    gap_factor: float = 3.0,
    sort: bool = True,
) -> vp.LineCollection:
    """Convert a complex point array to plotter-friendly path segments.

    When ``sort`` is True (default), points are reordered via nearest-neighbor
    traversal to create spatially coherent paths — appropriate for scattered
    point clouds like IFS output. When False, points are kept in their
    original order — appropriate for trajectory data like strange attractors
    where consecutive points are already sequential.

    Paths are broken at large spatial gaps and at ``segment_length``.

    Args:
        points: Array of complex numbers representing (x, y) points.
        segment_length: Maximum points per path segment.
        gap_percentile: Percentile of inter-point distances used to set
            the gap threshold. Higher values tolerate larger gaps.
        gap_factor: Multiplier applied to the percentile distance to
            determine where to break paths.
        sort: If True, apply nearest-neighbor sorting. If False, keep
            the original point order.

    Returns:
        A LineCollection of path segments.
    """
    if len(points) < 2:
        return vp.LineCollection()

    sorted_points = nearest_neighbor_sort(points) if sort else points

    diffs = np.abs(np.diff(sorted_points))
    max_gap = np.percentile(diffs, gap_percentile) * gap_factor

    lc = vp.LineCollection()
    path_start = 0
    for i, gap in enumerate(diffs):
        seg_len = i - path_start + 1
        if gap > max_gap or seg_len >= segment_length:
            chunk = sorted_points[path_start : i + 1]
            if len(chunk) >= 2:
                lc.append(chunk)
            path_start = i + 1

    chunk = sorted_points[path_start:]
    if len(chunk) >= 2:
        lc.append(chunk)

    return lc


def nearest_neighbor_sort(points: np.ndarray) -> np.ndarray:
    """Sort complex points via greedy nearest-neighbor traversal.

    Produces a traversal order where each point is followed by its closest
    unvisited neighbor, creating spatially coherent paths.
    """
    from scipy.spatial import cKDTree

    n = len(points)
    if n <= 1:
        return points

    coords = np.column_stack([points.real, points.imag])
    tree = cKDTree(coords)

    visited = np.zeros(n, dtype=bool)
    order = np.empty(n, dtype=int)
    current = 0

    for i in range(n):
        order[i] = current
        visited[current] = True

        if i == n - 1:
            break

        k = min(32, n)
        _, indices = tree.query(coords[current], k=k)

        next_idx = -1
        for idx in indices:
            if not visited[idx]:
                next_idx = idx
                break

        if next_idx == -1:
            remaining = np.where(~visited)[0]
            dists = np.sum((coords[remaining] - coords[current]) ** 2, axis=1)
            next_idx = remaining[np.argmin(dists)]

        current = next_idx

    return points[order]
