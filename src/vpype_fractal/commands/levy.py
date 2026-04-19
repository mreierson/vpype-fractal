"""Levy C curve command."""

import click
import vpype as vp
import vpype_cli

from ._shared import finalize_fractal, fractal_options, generate_lsystem_fractal


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
@fractal_options
@vpype_cli.global_processor
def levy(
    doc: vp.Document, depth: int, size: float, target_layer: int | None, raster: bool
) -> vp.Document:
    """Generate a Levy C curve fractal."""
    lc = generate_lsystem_fractal("levy", depth, size)
    return finalize_fractal(doc, lc, target_layer=target_layer, raster=raster)


levy.help_group = "Fractals"  # type: ignore[attr-defined]
