"""Sierpinski carpet fractal command."""

import click
import vpype as vp
import vpype_cli

from vpype_fractal.engines.geometric import build_carpet

from ._shared import scale_to_size


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
def carpet(depth: int, size: float) -> vp.LineCollection:
    """Generate a Sierpinski carpet fractal."""
    lines = build_carpet(depth)

    lc = vp.LineCollection()
    for line in lines:
        lc.append(line)

    return scale_to_size(lc, size)


carpet.help_group = "Fractals"  # type: ignore[attr-defined]
