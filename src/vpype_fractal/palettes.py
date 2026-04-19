"""Built-in gradient palettes for fractal coloring.

Each palette is a list of (R, G, B) anchor points.  The rendering code
interpolates smoothly between these anchors to produce continuous
gradients.  Palettes are designed to highlight fractal structure with
perceptually balanced color transitions.
"""

from __future__ import annotations

import numpy as np

# ---------------------------------------------------------------------------
# Palette definitions — each is a list of (R, G, B) anchor tuples.
# The coloring code interpolates linearly between anchors.
# ---------------------------------------------------------------------------

PALETTES: dict[str, list[tuple[int, int, int]]] = {
    # Classic fractal "fire" gradient: black → red → orange → yellow → white
    "fire": [
        (0, 0, 0),
        (128, 0, 0),
        (200, 50, 0),
        (255, 150, 0),
        (255, 220, 50),
        (255, 255, 200),
    ],
    # Deep ocean: black → dark blue → teal → cyan → white
    "ocean": [
        (0, 0, 0),
        (0, 10, 60),
        (0, 50, 130),
        (0, 120, 160),
        (40, 200, 220),
        (180, 240, 255),
    ],
    # Electric: black → indigo → purple → magenta → pink → white
    "electric": [
        (0, 0, 0),
        (30, 0, 80),
        (80, 0, 160),
        (160, 0, 200),
        (220, 50, 180),
        (255, 150, 220),
        (255, 220, 255),
    ],
    # Inferno-inspired: black → dark magenta → red → orange → yellow
    "inferno": [
        (0, 0, 4),
        (40, 11, 84),
        (101, 21, 110),
        (159, 42, 99),
        (212, 72, 66),
        (245, 125, 21),
        (252, 193, 57),
        (252, 255, 164),
    ],
    # Viridis-inspired: dark purple → blue → teal → green → yellow
    "viridis": [
        (68, 1, 84),
        (72, 36, 117),
        (56, 88, 140),
        (39, 130, 142),
        (31, 158, 137),
        (78, 195, 107),
        (158, 217, 58),
        (253, 231, 37),
    ],
    # Ice: black → deep blue → blue → light blue → white
    "ice": [
        (0, 0, 0),
        (0, 0, 40),
        (20, 40, 120),
        (60, 100, 180),
        (120, 170, 220),
        (200, 230, 250),
        (240, 248, 255),
    ],
    # Ember: dark → deep red → orange-red → gold
    "ember": [
        (0, 0, 0),
        (60, 0, 0),
        (140, 20, 0),
        (200, 60, 10),
        (240, 120, 20),
        (255, 180, 40),
        (255, 220, 100),
    ],
    # Aurora: dark → green → cyan → blue → purple
    "aurora": [
        (0, 0, 0),
        (0, 60, 20),
        (0, 150, 80),
        (20, 200, 160),
        (60, 180, 220),
        (100, 120, 240),
        (160, 80, 200),
        (200, 140, 255),
    ],
    # Grayscale: simple black to white
    "grayscale": [
        (0, 0, 0),
        (255, 255, 255),
    ],
    # Cosmic: deep black → dark blue → gold → white (high contrast)
    "cosmic": [
        (0, 0, 0),
        (0, 0, 0),
        (5, 5, 30),
        (20, 30, 100),
        (60, 80, 160),
        (180, 150, 60),
        (255, 220, 80),
        (255, 255, 220),
    ],
    # Plasma: black → deep magenta → hot pink → white
    "plasma": [
        (0, 0, 0),
        (0, 0, 0),
        (30, 0, 50),
        (80, 0, 110),
        (150, 20, 150),
        (220, 60, 120),
        (255, 130, 100),
        (255, 200, 150),
        (255, 240, 220),
    ],
}

# Default palette when none specified
DEFAULT_PALETTE = "inferno"

# Names for CLI help text
PALETTE_NAMES = sorted(PALETTES.keys())


def get_palette(name: str) -> np.ndarray:
    """Return a palette as an (N, 3) uint8 numpy array.

    Raises ``KeyError`` if the palette name is not found.
    """
    anchors = PALETTES[name]
    return np.array(anchors, dtype=np.uint8)


def expand_palette(name: str, n_colors: int = 256) -> np.ndarray:
    """Expand a palette to *n_colors* evenly interpolated RGB values.

    Returns an (n_colors, 3) uint8 array suitable for direct indexing.
    """
    anchors = np.array(PALETTES[name], dtype=np.float64)
    n_anchors = len(anchors)

    # Parameter along the palette [0, 1]
    t_anchors = np.linspace(0.0, 1.0, n_anchors)
    t_output = np.linspace(0.0, 1.0, n_colors)

    result = np.zeros((n_colors, 3), dtype=np.float64)
    for ch in range(3):
        result[:, ch] = np.interp(t_output, t_anchors, anchors[:, ch])

    return np.clip(result, 0, 255).astype(np.uint8)
