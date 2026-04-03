"""Turtle graphics interpreter that produces vpype LineCollections."""

import math

import numpy as np
import vpype as vp


def turtle_to_lines(
    instructions: str,
    angle: float,
    step: float = 1.0,
    origin: complex = 0 + 0j,
    heading: float = 0.0,
    draw_chars: str = "FABG",
    move_chars: str = "fg",
) -> vp.LineCollection:
    """Interpret a turtle graphics instruction string into line segments.

    Standard commands:
        F, A, B, G  - move forward and draw
        f, g        - move forward without drawing
        +           - turn left by angle
        -           - turn right by angle
        [           - push state (position + heading)
        ]           - pop state

    Args:
        instructions: The instruction string to interpret.
        angle: Turn angle in degrees.
        step: Step length per move.
        origin: Starting position as complex number.
        heading: Initial heading in degrees (0 = right, 90 = up).
        draw_chars: Characters that cause forward movement with drawing.
        move_chars: Characters that cause forward movement without drawing.

    Returns:
        A LineCollection containing all drawn paths.
    """
    lc = vp.LineCollection()
    angle_rad = math.radians(angle)
    heading_rad = math.radians(heading)

    x, y = origin.real, origin.imag
    current_path: list[complex] = [complex(x, y)]
    stack: list[tuple[float, float, float, list[complex]]] = []

    for char in instructions:
        if char in draw_chars:
            x += step * math.cos(heading_rad)
            y += step * math.sin(heading_rad)
            current_path.append(complex(x, y))

        elif char in move_chars:
            # Pen-up move: save current path and start a new one
            if len(current_path) >= 2:
                lc.append(np.array(current_path))
            x += step * math.cos(heading_rad)
            y += step * math.sin(heading_rad)
            current_path = [complex(x, y)]

        elif char == "+":
            heading_rad += angle_rad

        elif char == "-":
            heading_rad -= angle_rad

        elif char == "[":
            stack.append((x, y, heading_rad, current_path[:]))

        elif char == "]":
            if stack:
                # Save current path before restoring
                if len(current_path) >= 2:
                    lc.append(np.array(current_path))
                x, y, heading_rad, current_path = stack.pop()

    # Flush the final path
    if len(current_path) >= 2:
        lc.append(np.array(current_path))

    return lc
