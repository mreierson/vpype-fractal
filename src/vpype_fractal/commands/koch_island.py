"""Koch Island (quadratic Koch island) command."""

import click
import vpype as vp
import vpype_cli

from ._shared import finalize_fractal, fractal_options, generate_lsystem_fractal


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
@fractal_options
@vpype_cli.global_processor
def koch_island(
    doc: vp.Document, depth: int, size: float, target_layer: int | None, raster: bool
) -> vp.Document:
    """Generate a Koch Island (quadratic Koch island).

    A square variant of the Koch snowflake that produces an island-like shape
    with a complex, jagged coastline.
    """
    lc = generate_lsystem_fractal("koch_island", depth, size)
    return finalize_fractal(doc, lc, target_layer=target_layer, raster=raster)


koch_island.help_group = "Fractals"  # type: ignore[attr-defined]
