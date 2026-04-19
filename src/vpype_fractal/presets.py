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
    # --- Botanical presets (Prusinkiewicz & Lindenmayer) ---
    "tree-realistic": LSystemDef(
        axiom="X",
        rules={"X": "F[+X]F[-X]+X", "F": "FF"},
        angle=20.0,
        heading=90.0,
    ),
    "bush": LSystemDef(
        axiom="F",
        rules={"F": "FF+[+F-F-F]-[-F+F+F]"},
        angle=22.5,
        heading=90.0,
    ),
    "flower": LSystemDef(
        axiom="F[+F+F][-F-F][++F][--F]F",
        rules={"F": "FF[++F][+F][F][-F][--F]"},
        angle=15.0,
        heading=90.0,
    ),
    "seaweed": LSystemDef(
        axiom="F",
        rules={"F": "FF-[-F+F+F]+[+F-F-F]"},
        angle=22.5,
        heading=90.0,
    ),
    "vine": LSystemDef(
        axiom="X",
        rules={"X": "F+[[X]-X]-F[-FX]+X", "F": "FF"},
        angle=25.0,
        heading=90.0,
    ),
    # --- Additional botanical presets ---
    "herb": LSystemDef(
        axiom="X",
        rules={"X": "F[-X][+X]FX", "F": "FF"},
        angle=25.7,
        heading=90.0,
    ),
    "kelp": LSystemDef(
        axiom="F",
        rules={"F": "F[+F]F[-F]F"},
        angle=25.7,
        heading=90.0,
    ),
    "branching-y": LSystemDef(
        axiom="X",
        rules={"X": "F[+X][-X]FX", "F": "FF"},
        angle=30.0,
        heading=90.0,
    ),
    "moss": LSystemDef(
        axiom="F",
        rules={"F": "F[-F]F[+F][F]"},
        angle=20.0,
        heading=90.0,
    ),
    "sapling": LSystemDef(
        axiom="X",
        rules={"X": "F-[[X]+X]+F[+FX]-X", "F": "FF"},
        angle=22.5,
        heading=90.0,
    ),
    "fern-frond": LSystemDef(
        axiom="X",
        rules={"X": "F[+X]F[-X]+X", "F": "FF"},
        angle=20.0,
        heading=90.0,
    ),
    "willow": LSystemDef(
        axiom="F",
        rules={"F": "FF[++F][-FF][+F][-F]"},
        angle=18.0,
        heading=90.0,
    ),
}
