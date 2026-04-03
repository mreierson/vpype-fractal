"""Marching squares contour extraction from 2D scalar fields."""

from collections import deque

import numpy as np
import vpype as vp


def extract_contours(
    x: np.ndarray,
    y: np.ndarray,
    field: np.ndarray,
    levels: list[float],
    margin: int = 0,
) -> vp.LineCollection:
    """Extract iso-contour lines from a 2D scalar field using marching squares.

    Args:
        x: 1D array of x coordinates (length nx).
        y: 1D array of y coordinates (length ny).
        field: 2D array of shape (ny, nx).
        levels: List of threshold values at which to extract contours.
        margin: Number of boundary cells to skip on each edge.

    Returns:
        A LineCollection containing all contour line segments.
    """
    lc = vp.LineCollection()
    for level_lc in extract_contours_by_level(x, y, field, levels, margin=margin):
        for line in level_lc:
            lc.append(line)
    return lc


def extract_contours_by_level(
    x: np.ndarray,
    y: np.ndarray,
    field: np.ndarray,
    levels: list[float],
    margin: int = 0,
) -> list[vp.LineCollection]:
    """Extract contours per level, returning one LineCollection per level.

    Args:
        x: 1D array of x coordinates (length nx).
        y: 1D array of y coordinates (length ny).
        field: 2D array of shape (ny, nx).
        levels: List of threshold values at which to extract contours.
        margin: Number of boundary cells to skip on each edge.

    Returns:
        A list of LineCollections, one per level.
    """
    ny, nx = field.shape
    result: list[vp.LineCollection] = []

    for level in levels:
        lc = vp.LineCollection()
        segments = _march(field, x, y, nx, ny, level, margin=margin)
        chains = _chain_segments(segments)
        for chain in chains:
            if len(chain) >= 2:
                lc.append(np.array(chain))
        result.append(lc)

    return result


def _march(
    field: np.ndarray,
    x: np.ndarray,
    y: np.ndarray,
    nx: int,
    ny: int,
    level: float,
    margin: int = 0,
) -> list[tuple[complex, complex]]:
    """Run marching squares on the field, returning raw line segments.

    Skips ``margin`` cells at each grid edge to prevent boundary artifacts
    from incomplete contour lines at the viewport border.

    Uses vectorized numpy operations to compute case indices and edge
    interpolations for all cells simultaneously.
    """
    m = margin
    j0, j1 = m, ny - 1 - m
    i0, i1 = m, nx - 1 - m

    if j1 <= j0 or i1 <= i0:
        return []

    # Extract corner values for all cells at once: shape (nj, ni)
    v0 = field[j0:j1, i0:i1]  # top-left
    v1 = field[j0:j1, i0 + 1 : i1 + 1]  # top-right
    v2 = field[j0 + 1 : j1 + 1, i0 + 1 : i1 + 1]  # bottom-right
    v3 = field[j0 + 1 : j1 + 1, i0:i1]  # bottom-left

    # Compute 4-bit case index for every cell
    cases = (
        ((v0 >= level).astype(np.uint8))
        | ((v1 >= level).astype(np.uint8) << 1)
        | ((v2 >= level).astype(np.uint8) << 2)
        | ((v3 >= level).astype(np.uint8) << 3)
    )

    # Precompute interpolation parameters for all four edges (clipped to [0,1])
    def _safe_interp(va: np.ndarray, vb: np.ndarray) -> np.ndarray:
        diff = vb - va
        safe = np.where(np.abs(diff) < 1e-12, 1.0, diff)
        t = (level - va) / safe
        t = np.where(np.abs(diff) < 1e-12, 0.5, t)
        return t

    t0 = _safe_interp(v0, v1)  # edge 0: top
    t1 = _safe_interp(v1, v2)  # edge 1: right
    t2 = _safe_interp(v3, v2)  # edge 2: bottom
    t3 = _safe_interp(v0, v3)  # edge 3: left

    # Precompute coordinate arrays for cell corners
    xi = x[i0:i1]  # left x for each column
    xi1 = x[i0 + 1 : i1 + 1]  # right x for each column
    yj = y[j0:j1]  # top y for each row
    yj1 = y[j0 + 1 : j1 + 1]  # bottom y for each row

    # Broadcast to 2D: xi[ni] -> (1, ni), yj[nj] -> (nj, 1)
    xi_2d = xi[np.newaxis, :]
    xi1_2d = xi1[np.newaxis, :]
    yj_2d = yj[:, np.newaxis]
    yj1_2d = yj1[:, np.newaxis]

    # Compute edge crossing points as complex numbers
    # Edge 0: top (v0->v1), y = yj
    edge0 = (xi_2d + t0 * (xi1_2d - xi_2d)) + 1j * yj_2d
    # Edge 1: right (v1->v2), x = xi1
    edge1 = xi1_2d + 1j * (yj_2d + t1 * (yj1_2d - yj_2d))
    # Edge 2: bottom (v3->v2), y = yj1
    edge2 = (xi_2d + t2 * (xi1_2d - xi_2d)) + 1j * yj1_2d
    # Edge 3: left (v0->v3), x = xi
    edge3 = xi_2d + 1j * (yj_2d + t3 * (yj1_2d - yj_2d))

    edges_all = [edge0, edge1, edge2, edge3]

    # Build segment lookup: case -> list of (edge_a, edge_b) pairs
    # For saddle cases we have two variants depending on center value.
    # _CASE_SEGS[case] = [(ea, eb), ...] for non-saddle cases
    # For cases 5 and 10 we handle separately.
    _CASE_SEGS: dict[int, list[tuple[int, int]]] = {
        1: [(0, 3)],
        2: [(0, 1)],
        3: [(1, 3)],
        4: [(1, 2)],
        6: [(0, 2)],
        7: [(2, 3)],
        8: [(2, 3)],
        9: [(0, 2)],
        11: [(1, 2)],
        12: [(1, 3)],
        13: [(0, 1)],
        14: [(0, 3)],
    }

    segments: list[tuple[complex, complex]] = []

    # Process non-saddle cases (1-4, 6-9, 11-14)
    for case_val, seg_pairs in _CASE_SEGS.items():
        mask = cases == case_val
        if not np.any(mask):
            continue
        for ea, eb in seg_pairs:
            pts_a = edges_all[ea][mask]
            pts_b = edges_all[eb][mask]
            for k in range(len(pts_a)):
                segments.append((pts_a[k], pts_b[k]))

    # Process saddle case 5
    mask5 = cases == 5
    if np.any(mask5):
        center5 = (v0[mask5] + v1[mask5] + v2[mask5] + v3[mask5]) / 4.0
        above = center5 >= level

        # Center above: connect across -> (0,1), (2,3)
        if np.any(above):
            e0a = edge0[mask5][above]
            e1a = edge1[mask5][above]
            e2a = edge2[mask5][above]
            e3a = edge3[mask5][above]
            for k in range(len(e0a)):
                segments.append((e0a[k], e1a[k]))
                segments.append((e2a[k], e3a[k]))

        # Center below: connect same-side -> (0,3), (1,2)
        below = ~above
        if np.any(below):
            e0b = edge0[mask5][below]
            e1b = edge1[mask5][below]
            e2b = edge2[mask5][below]
            e3b = edge3[mask5][below]
            for k in range(len(e0b)):
                segments.append((e0b[k], e3b[k]))
                segments.append((e1b[k], e2b[k]))

    # Process saddle case 10
    mask10 = cases == 10
    if np.any(mask10):
        center10 = (v0[mask10] + v1[mask10] + v2[mask10] + v3[mask10]) / 4.0
        above = center10 >= level

        # Center above: connect across -> (0,3), (1,2)
        if np.any(above):
            e0a = edge0[mask10][above]
            e1a = edge1[mask10][above]
            e2a = edge2[mask10][above]
            e3a = edge3[mask10][above]
            for k in range(len(e0a)):
                segments.append((e0a[k], e3a[k]))
                segments.append((e1a[k], e2a[k]))

        # Center below: connect same-side -> (0,1), (2,3)
        below = ~above
        if np.any(below):
            e0b = edge0[mask10][below]
            e1b = edge1[mask10][below]
            e2b = edge2[mask10][below]
            e3b = edge3[mask10][below]
            for k in range(len(e0b)):
                segments.append((e0b[k], e1b[k]))
                segments.append((e2b[k], e3b[k]))

    return segments


def _chain_segments(
    segments: list[tuple[complex, complex]],
) -> list[list[complex]]:
    """Chain individual line segments into connected polylines.

    Uses an endpoint index for O(n) chaining instead of brute-force search.
    """
    if not segments:
        return []

    tolerance = 1e-10

    def _key(pt: complex) -> tuple[float, float]:
        """Quantize a point to a grid key for endpoint matching."""
        return (round(pt.real / tolerance), round(pt.imag / tolerance))

    # Build endpoint index: key -> list of (segment_index, which_end)
    endpoint_idx: dict[tuple[float, float], list[tuple[int, int]]] = {}
    for si, (p0, p1) in enumerate(segments):
        for end, pt in enumerate((p0, p1)):
            k = _key(pt)
            endpoint_idx.setdefault(k, []).append((si, end))

    used = [False] * len(segments)
    chains: list[list[complex]] = []

    for start_si in range(len(segments)):
        if used[start_si]:
            continue
        used[start_si] = True

        chain: deque[complex] = deque(segments[start_si])

        # Extend forward from chain[-1]
        while True:
            k = _key(chain[-1])
            found = False
            for si, end in endpoint_idx.get(k, []):
                if used[si]:
                    continue
                used[si] = True
                s = segments[si]
                if end == 0:
                    chain.append(s[1])
                else:
                    chain.append(s[0])
                found = True
                break
            if not found:
                break

        # Extend backward from chain[0]
        while True:
            k = _key(chain[0])
            found = False
            for si, end in endpoint_idx.get(k, []):
                if used[si]:
                    continue
                used[si] = True
                s = segments[si]
                if end == 0:
                    chain.appendleft(s[1])
                else:
                    chain.appendleft(s[0])
                found = True
                break
            if not found:
                break

        chains.append(list(chain))

    return chains
