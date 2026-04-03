"""Peano space-filling curve command."""

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
def peano(depth: int, size: float) -> vp.LineCollection:
    """Generate a Peano space-filling curve."""
    return generate_lsystem_fractal("peano", depth, size)


peano.help_group = "Fractals"  # type: ignore[attr-defined]
