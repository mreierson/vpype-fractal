"""Barnsley Fern shortcut — alias for `ifs --preset fern`."""

import click
import vpype as vp
import vpype_cli

from vpype_fractal.engines.ifs import IFS_PRESETS, ifs_to_lines

from ._shared import scale_to_size


@click.command()
@click.option(
    "-s",
    "--size",
    type=vpype_cli.LengthType(),
    default="100mm",
    help="Overall size.",
)
@click.option(
    "-p",
    "--points",
    type=click.IntRange(min=100),
    default=50000,
    help="Number of points to generate.",
)
@click.option(
    "--segment-length",
    type=click.IntRange(min=2),
    default=500,
    help="Maximum points per path segment.",
)
@click.option(
    "--seed",
    type=int,
    default=None,
    help="Random seed for reproducibility.",
)
@vpype_cli.generator
def fern(
    size: float,
    points: int,
    segment_length: int,
    seed: int | None,
) -> vp.LineCollection:
    """Generate a Barnsley Fern (shortcut for `ifs --preset fern`)."""
    transforms = IFS_PRESETS["fern"].transforms
    lc = ifs_to_lines(transforms, points, seed=seed, segment_length=segment_length)
    return scale_to_size(lc, size)


fern.help_group = "Fractals"  # type: ignore[attr-defined]
