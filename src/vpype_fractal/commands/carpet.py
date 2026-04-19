"""Sierpinski carpet fractal command."""

import click
import vpype as vp
import vpype_cli

from vpype_fractal.engines.geometric import build_carpet

from ._shared import finalize_fractal, fractal_options, scale_to_size


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
@fractal_options
@vpype_cli.global_processor
def carpet(
    doc: vp.Document, depth: int, size: float, target_layer: int | None, raster: bool
) -> vp.Document:
    """Generate a Sierpinski carpet fractal."""
    lines = build_carpet(depth)

    lc = vp.LineCollection()
    for line in lines:
        lc.append(line)

    lc = scale_to_size(lc, size)
    return finalize_fractal(doc, lc, target_layer=target_layer, raster=raster)


carpet.help_group = "Fractals"  # type: ignore[attr-defined]
