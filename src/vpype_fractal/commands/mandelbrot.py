"""Mandelbrot set contour command."""

import click
import vpype as vp
import vpype_cli

from vpype_fractal.engines.escape_time import mandelbrot_grid

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
@click.option("--x-min", type=float, default=-2.2, help="Left bound of real axis.")
@click.option("--x-max", type=float, default=0.8, help="Right bound of real axis.")
@click.option("--y-min", type=float, default=-1.2, help="Bottom bound of imaginary axis.")
@click.option("--y-max", type=float, default=1.2, help="Top bound of imaginary axis.")
@vpype_cli.global_processor
def mandelbrot(
    doc: vp.Document,
    max_iter: int,
    size: float,
    resolution: int,
    levels: int,
    x_min: float,
    x_max: float,
    y_min: float,
    y_max: float,
) -> vp.Document:
    """Generate contour lines of the Mandelbrot set.

    Computes escape-time values on a grid and extracts iso-contour lines,
    producing plotter-friendly vector output. Each contour level is placed
    on a separate layer.

    Use ``penset ... colorize`` in the pipeline for colored output.
    """
    if x_min >= x_max:
        raise click.UsageError(f"--x-min ({x_min}) must be less than --x-max ({x_max})")
    if y_min >= y_max:
        raise click.UsageError(f"--y-min ({y_min}) must be less than --y-max ({y_max})")
    x, y, escape = mandelbrot_grid(x_min, x_max, y_min, y_max, resolution, max_iter)
    return generate_escape_time_fractal(doc, x, y, escape, max_iter, levels, size)


mandelbrot.help_group = "Fractals"  # type: ignore[attr-defined]
