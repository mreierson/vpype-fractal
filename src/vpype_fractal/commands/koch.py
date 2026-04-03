"""Koch snowflake fractal command."""

import click
import vpype as vp
import vpype_cli

from ._shared import generate_lsystem_fractal


@click.command()
@click.option(
    "-d",
    "--depth",
    type=click.IntRange(min=0, max=8),
    default=4,
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
def koch(depth: int, size: float) -> vp.LineCollection:
    """Generate a Koch snowflake fractal."""
    return generate_lsystem_fractal("koch", depth, size)


koch.help_group = "Fractals"  # type: ignore[attr-defined]
