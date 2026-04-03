"""Sierpinski triangle (recursive subdivision) command."""

import click
import vpype as vp
import vpype_cli

from vpype_fractal.engines.geometric import build_sierpinski_triangle

from ._shared import scale_to_size


@click.command("sierpinski-triangle")
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
def sierpinski_triangle(depth: int, size: float) -> vp.LineCollection:
    """Generate a Sierpinski triangle by recursive subdivision.

    Unlike the 'sierpinski' command (which traces the arrowhead curve),
    this produces the classic triangle-with-holes pattern.
    """
    lines = build_sierpinski_triangle(depth)

    lc = vp.LineCollection()
    for line in lines:
        lc.append(line)

    return scale_to_size(lc, size)


sierpinski_triangle.help_group = "Fractals"  # type: ignore[attr-defined]
