"""Sierpinski arrowhead curve command."""

import click
import vpype as vp
import vpype_cli

from ._shared import generate_lsystem_fractal


@click.command()
@click.option(
    "-d",
    "--depth",
    type=click.IntRange(min=0, max=10),
    default=5,
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
def sierpinski(depth: int, size: float) -> vp.LineCollection:
    """Generate a Sierpinski arrowhead curve."""
    return generate_lsystem_fractal("sierpinski", depth, size)


sierpinski.help_group = "Fractals"  # type: ignore[attr-defined]
