"""Dragon curve command."""

import click
import vpype as vp
import vpype_cli

from ._shared import generate_lsystem_fractal


@click.command()
@click.option(
    "-d",
    "--depth",
    type=click.IntRange(min=0, max=16),
    default=10,
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
def dragon(depth: int, size: float) -> vp.LineCollection:
    """Generate a dragon curve fractal."""
    return generate_lsystem_fractal("dragon", depth, size)


dragon.help_group = "Fractals"  # type: ignore[attr-defined]
