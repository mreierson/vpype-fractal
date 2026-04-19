"""Mandelbrot set contour command."""

import click
import vpype as vp
import vpype_cli

from vpype_fractal.engines.escape_time import mandelbrot_grid
from vpype_fractal.palettes import PALETTE_NAMES

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
    default=60,
    help="Number of contour levels. Higher values reduce visible banding in filled SVG output.",
)
@click.option("--x-min", type=float, default=-2.2, help="Left bound of real axis.")
@click.option("--x-max", type=float, default=0.8, help="Right bound of real axis.")
@click.option("--y-min", type=float, default=-1.2, help="Bottom bound of imaginary axis.")
@click.option("--y-max", type=float, default=1.2, help="Top bound of imaginary axis.")
@click.option(
    "--raster",
    is_flag=True,
    help="Store escape-time grid as raster image metadata for downstream "
    "raster commands (stipple, hatch, halftone, etc.).",
)
@click.option(
    "--emit-region",
    is_flag=True,
    help="Write the Mandelbrot interior as a region mask to vpype-raster "
    "region metadata for use with forregion | stipple/hatch. Skips contour "
    "generation when set (use --also-lines to get both).",
)
@click.option(
    "--also-lines",
    is_flag=True,
    help="Emit both the region mask (--emit-region) AND contour lines.",
)
@click.option(
    "--palette",
    "palette_name",
    type=click.Choice(PALETTE_NAMES, case_sensitive=False),
    default=None,
    help="Built-in color palette for gradient coloring.",
)
@click.option(
    "--save-image",
    type=click.Path(),
    default=None,
    help="Save rendered fractal image to this path (PNG/JPG).",
)
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
    raster: bool,
    emit_region: bool,
    also_lines: bool,
    palette_name: str | None,
    save_image: str | None,
) -> vp.Document:
    """Generate contour lines of the Mandelbrot set.

    Computes escape-time values on a grid and extracts iso-contour lines,
    producing plotter-friendly vector output. Each contour level is placed
    on a separate layer.

    Layers are automatically colored using the active penset or a built-in
    gradient palette (use --palette to choose).
    """
    if x_min >= x_max:
        raise click.UsageError(f"--x-min ({x_min}) must be less than --x-max ({x_max})")
    if y_min >= y_max:
        raise click.UsageError(f"--y-min ({y_min}) must be less than --y-max ({y_max})")
    x, y, escape = mandelbrot_grid(x_min, x_max, y_min, y_max, resolution, max_iter)

    if emit_region:
        from vpype_fractal._region import emit_region_mask
        interior_mask = escape >= max_iter
        emit_region_mask(
            doc,
            interior_mask,
            generator="mandelbrot",
            source="",
            params={"max_iter": max_iter,
                    "bounds": (x_min, x_max, y_min, y_max)},
            name="mandelbrot_interior",
        )
        if not also_lines:
            # Still publish the raster if requested — downstream commands
            # like stipple/hatch need both the image (for tone) and the
            # region mask (for clipping) to run inside forregion.
            if raster or save_image:
                from vpype_fractal.commands._shared import _store_raster
                _store_raster(doc, escape, max_iter, palette_name)
            return doc

    return generate_escape_time_fractal(
        doc, x, y, escape, max_iter, levels, size,
        raster=raster, palette_name=palette_name, save_image=save_image,
    )


mandelbrot.help_group = "Fractals"  # type: ignore[attr-defined]
