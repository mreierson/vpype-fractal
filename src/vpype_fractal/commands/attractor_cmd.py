"""Generic attractor command — access all attractor presets from one command."""

import click
import vpype as vp
import vpype_cli

from vpype_fractal.engines.attractor import _RUNNERS, ATTRACTOR_PRESETS

from ._shared import generate_attractor_layers


@click.command()
@click.option(
    "--preset",
    type=click.Choice(sorted(ATTRACTOR_PRESETS.keys())),
    required=True,
    help="Named attractor preset.",
)
@click.option("-s", "--size", type=vpype_cli.LengthType(), default="100mm", help="Overall size.")
@click.option(
    "-p",
    "--points",
    type=click.IntRange(min=100),
    default=None,
    help="Number of points (default depends on attractor type).",
)
@click.option(
    "-n",
    "--layers",
    type=click.IntRange(min=1),
    default=1,
    help="Split trajectory into N layers for color gradients.",
)
@click.option("--seed", type=int, default=None, help="Random seed for reproducibility.")
@vpype_cli.global_processor
def attractor(
    doc: vp.Document,
    preset: str,
    size: float,
    points: int | None,
    layers: int,
    seed: int | None,
) -> vp.Document:
    """Generate a strange attractor from a named preset.

    \b
    Clifford presets:  butterfly, ribbon, swirl
    De Jong presets:   orbit, tangle, wings
    Lorenz presets:    lorenz-classic, lorenz-tight

    \b
    Examples:
        vpype attractor --preset butterfly show
        vpype penset warm attractor --preset ribbon -n 6 colorize write out.svg
        vpype attractor --preset lorenz-classic -p 100000 -n 10 show
    """
    preset_def = ATTRACTOR_PRESETS[preset]
    kind = preset_def.kind
    params = preset_def.params

    # Default point counts per type
    if points is None:
        points = 50000 if kind == "lorenz" else 3000

    runner = _RUNNERS[kind]
    raw = runner(params, points, seed)

    smooth = 10 if kind in ("clifford", "dejong") else 0
    return generate_attractor_layers(doc, raw, layers, size, smooth=smooth)


attractor.help_group = "Fractals"  # type: ignore[attr-defined]
