"""Named L-system fractal presets."""

from dataclasses import dataclass


@dataclass(frozen=True)
class LSystemDef:
    """Definition of an L-system fractal."""

    axiom: str
    rules: dict[str, str]
    angle: float
    heading: float = 0.0


PRESETS: dict[str, LSystemDef] = {
    "koch": LSystemDef(
        axiom="F--F--F",
        rules={"F": "F+F--F+F"},
        angle=60.0,
    ),
    "sierpinski": LSystemDef(
        axiom="A",
        rules={"A": "B-A-B", "B": "A+B+A"},
        angle=60.0,
    ),
    "dragon": LSystemDef(
        axiom="FX",
        rules={"X": "X+YF+", "Y": "-FX-Y"},
        angle=90.0,
    ),
    "hilbert": LSystemDef(
        axiom="A",
        rules={"A": "-BF+AFA+FB-", "B": "+AF-BFB-FA+"},
        angle=90.0,
    ),
    "levy": LSystemDef(
        axiom="F",
        rules={"F": "+F--F+"},
        angle=45.0,
    ),
    "gosper": LSystemDef(
        axiom="A",
        rules={"A": "A-B--B+A++AA+B-", "B": "+A-BB--B-A++A+B"},
        angle=60.0,
    ),
    "peano": LSystemDef(
        axiom="X",
        rules={
            "X": "XFYFX+F+YFXFY-F-XFYFX",
            "Y": "YFXFY-F-XFYFX+F+YFXFY",
        },
        angle=90.0,
    ),
    "koch_island": LSystemDef(
        axiom="F+F+F+F",
        rules={"F": "F+F-F-FF+F+F-F"},
        angle=90.0,
    ),
    "minkowski": LSystemDef(
        axiom="F+F+F+F",
        rules={"F": "F-F+F+FF-F-F+F"},
        angle=90.0,
    ),
}
