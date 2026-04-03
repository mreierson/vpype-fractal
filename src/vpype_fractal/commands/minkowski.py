"""Minkowski Sausage command."""

import click
import vpype as vp
import vpype_cli

from ._shared import generate_lsystem_fractal


@click.command()
@click.option(
    "-d",
    "--depth",
    type=click.IntRange(min=0, max=5),
    default=3,
    help="Recursion depth.",
)
@click.option(
    "-s",
    "--size",
    type=vpype_cli.LengthType(),
    default="100mm",
    help="Overall size.",
)
@vpype_cli.generator
def minkowski(depth: int, size: float) -> vp.LineCollection:
    """Generate a Minkowski Sausage fractal.

    A variant of the Koch curve using 90-degree angles, producing a
    sausage-like closed shape with intricate rectangular bumps.
    """
    return generate_lsystem_fractal("minkowski", depth, size)


minkowski.help_group = "Fractals"  # type: ignore[attr-defined]
