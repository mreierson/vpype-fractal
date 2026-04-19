"""Koch snowflake fractal command."""

import click
import vpype as vp
import vpype_cli

from ._shared import finalize_fractal, fractal_options, generate_lsystem_fractal


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
@fractal_options
@vpype_cli.global_processor
def koch(
    doc: vp.Document, depth: int, size: float, target_layer: int | None, raster: bool
) -> vp.Document:
    """Generate a Koch snowflake fractal."""
    lc = generate_lsystem_fractal("koch", depth, size)
    return finalize_fractal(doc, lc, target_layer=target_layer, raster=raster)


koch.help_group = "Fractals"  # type: ignore[attr-defined]
