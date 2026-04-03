"""Geometric fractal engines — recursive subdivision algorithms."""

import math

import numpy as np


def build_tree(
    depth: int,
    branch_angle: float,
    shrink: float = 0.7,
    trunk_length: float = 10.0,
) -> list[np.ndarray]:
    """Generate a fractal branching tree.

    Args:
        depth: Recursion depth (0 produces no lines).
        branch_angle: Branch angle in radians.
        shrink: Branch length shrink factor per level.
        trunk_length: Length of the initial trunk segment.

    Returns:
        List of complex arrays, each a 2-point line segment.
    """
    lines: list[np.ndarray] = []
    _tree_recurse(0, 0, trunk_length, -math.pi / 2, branch_angle, shrink, depth, lines)
    return lines


def _tree_recurse(
    x: float,
    y: float,
    length: float,
    heading: float,
    branch_angle: float,
    shrink: float,
    depth: int,
    lines: list[np.ndarray],
) -> None:
    if depth == 0 or length < 0.1:
        return

    x2 = x + length * math.cos(heading)
    y2 = y + length * math.sin(heading)
    lines.append(np.array([complex(x, y), complex(x2, y2)]))

    new_length = length * shrink
    _tree_recurse(
        x2, y2, new_length, heading + branch_angle, branch_angle, shrink, depth - 1, lines
    )
    _tree_recurse(
        x2, y2, new_length, heading - branch_angle, branch_angle, shrink, depth - 1, lines
    )


def build_carpet(depth: int) -> list[np.ndarray]:
    """Generate a Sierpinski carpet.

    Args:
        depth: Recursion depth (0 produces a single square).

    Returns:
        List of complex arrays, each a closed square outline.
    """
    lines: list[np.ndarray] = []
    _carpet_recurse(0, 0, 1.0, depth, lines)
    return lines


def _carpet_recurse(
    x: float,
    y: float,
    size: float,
    depth: int,
    lines: list[np.ndarray],
) -> None:
    if depth == 0:
        lines.append(
            np.array(
                [
                    complex(x, y),
                    complex(x + size, y),
                    complex(x + size, y + size),
                    complex(x, y + size),
                    complex(x, y),
                ]
            )
        )
        return

    sub = size / 3.0
    for row in range(3):
        for col in range(3):
            if row == 1 and col == 1:
                continue
            _carpet_recurse(x + col * sub, y + row * sub, sub, depth - 1, lines)


def build_sierpinski_triangle(depth: int) -> list[np.ndarray]:
    """Generate a Sierpinski triangle by recursive subdivision.

    Args:
        depth: Recursion depth (0 produces a single triangle).

    Returns:
        List of complex arrays, each a closed triangle outline.
    """
    lines: list[np.ndarray] = []
    h = math.sqrt(3) / 2
    _triangle_recurse(0, 0, 1, 0, 0.5, h, depth, lines)
    return lines


def _triangle_recurse(
    ax: float,
    ay: float,
    bx: float,
    by: float,
    cx: float,
    cy: float,
    depth: int,
    lines: list[np.ndarray],
) -> None:
    if depth == 0:
        lines.append(
            np.array(
                [
                    complex(ax, ay),
                    complex(bx, by),
                    complex(cx, cy),
                    complex(ax, ay),
                ]
            )
        )
        return

    abx, aby = (ax + bx) / 2, (ay + by) / 2
    bcx, bcy = (bx + cx) / 2, (by + cy) / 2
    acx, acy = (ax + cx) / 2, (ay + cy) / 2

    _triangle_recurse(ax, ay, abx, aby, acx, acy, depth - 1, lines)
    _triangle_recurse(abx, aby, bx, by, bcx, bcy, depth - 1, lines)
    _triangle_recurse(acx, acy, bcx, bcy, cx, cy, depth - 1, lines)
