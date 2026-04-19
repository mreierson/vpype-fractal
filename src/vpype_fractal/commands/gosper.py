"""Gosper flowsnake curve command."""

import click
import vpype as vp
import vpype_cli

from ._shared import finalize_fractal, fractal_options, generate_lsystem_fractal


@click.command()
@click.option(
    "-d",
    "--depth",
    type=click.IntRange(min=0, max=6),
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
def gosper(
    doc: vp.Document, depth: int, size: float, target_layer: int | None, raster: bool
) -> vp.Document:
    """Generate a Gosper flowsnake curve."""
    lc = generate_lsystem_fractal("gosper", depth, size)
    return finalize_fractal(doc, lc, target_layer=target_layer, raster=raster)


gosper.help_group = "Fractals"  # type: ignore[attr-defined]
