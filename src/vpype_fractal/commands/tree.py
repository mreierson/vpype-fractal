"""Fractal branching tree command."""

import math

import click
import vpype as vp
import vpype_cli

from vpype_fractal.engines.geometric import build_tree

from ._shared import scale_to_size


@click.command()
@click.option(
    "-d",
    "--depth",
    type=click.IntRange(min=0, max=15),
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
@click.option(
    "--branch-angle",
    type=click.FloatRange(min=0.0, max=180.0),
    default=25.0,
    help="Branch angle in degrees.",
)
@click.option(
    "--shrink",
    type=click.FloatRange(min=0.01, max=1.0),
    default=0.7,
    help="Branch length shrink factor per level (0.01–1.0).",
)
@vpype_cli.generator
def tree(
    depth: int,
    size: float,
    branch_angle: float,
    shrink: float,
) -> vp.LineCollection:
    """Generate a fractal branching tree."""
    lines = build_tree(depth, math.radians(branch_angle), shrink)

    lc = vp.LineCollection()
    for line in lines:
        lc.append(line)

    return scale_to_size(lc, size)


tree.help_group = "Fractals"  # type: ignore[attr-defined]
