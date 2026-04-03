"""Julia set contour command."""

import click
import vpype as vp
import vpype_cli

from vpype_fractal.engines.escape_time import julia_grid

from ._shared import generate_escape_time_fractal


@click.command()
@click.option(
    "-d",
    "--depth",
    "max_iter",
    type=click.IntRange(min=1),
    default=100,
    help="Maximum iteration count.",
)
@click.option(
    "-s",
    "--size",
    type=vpype_cli.LengthType(),
    default="100mm",
    help="Overall output size.",
)
@click.option(
    "-r",
    "--resolution",
    type=click.IntRange(min=50),
    default=500,
    help="Grid resolution (points along longest axis).",
)
@click.option(
    "-n",
    "--levels",
    type=click.IntRange(min=1),
    default=20,
    help="Number of contour levels.",
)
@click.option(
    "--cx",
    type=float,
    default=-0.7,
    help="Real part of the Julia constant c.",
)
@click.option(
    "--cy",
    type=float,
    default=0.27015,
    help="Imaginary part of the Julia constant c.",
)
@click.option("--x-min", type=float, default=-1.5, help="Left bound of z-plane.")
@click.option("--x-max", type=float, default=1.5, help="Right bound of z-plane.")
@click.option("--y-min", type=float, default=-1.5, help="Bottom bound of z-plane.")
@click.option("--y-max", type=float, default=1.5, help="Top bound of z-plane.")
@vpype_cli.global_processor
def julia(
    doc: vp.Document,
    max_iter: int,
    size: float,
    resolution: int,
    levels: int,
    cx: float,
    cy: float,
    x_min: float,
    x_max: float,
    y_min: float,
    y_max: float,
) -> vp.Document:
    """Generate contour lines of a Julia set.

    Computes escape-time values for z^2 + c and extracts iso-contour lines.
    The constant c is set via --cx and --cy. Each contour level is placed
    on a separate layer.

    Use ``penset ... colorize`` in the pipeline for colored output.

    \b
    Popular c values:
      -0.7 + 0.27015i (default), -0.4 + 0.6i, 0.355 + 0.355i,
      -0.8 + 0.156i, -0.123 + 0.745i
    """
    if x_min >= x_max:
        raise click.UsageError(f"--x-min ({x_min}) must be less than --x-max ({x_max})")
    if y_min >= y_max:
        raise click.UsageError(f"--y-min ({y_min}) must be less than --y-max ({y_max})")
    x, y, escape = julia_grid(cx, cy, x_min, x_max, y_min, y_max, resolution, max_iter)
    return generate_escape_time_fractal(doc, x, y, escape, max_iter, levels, size)


julia.help_group = "Fractals"  # type: ignore[attr-defined]
