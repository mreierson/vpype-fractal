"""Koch Island (quadratic Koch island) command."""

import click
import vpype as vp
import vpype_cli

from ._shared import generate_lsystem_fractal


@click.command("koch-island")
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
def koch_island(depth: int, size: float) -> vp.LineCollection:
    """Generate a Koch Island (quadratic Koch island).

    A square variant of the Koch snowflake that produces an island-like shape
    with a complex, jagged coastline.
    """
    return generate_lsystem_fractal("koch_island", depth, size)


koch_island.help_group = "Fractals"  # type: ignore[attr-defined]
