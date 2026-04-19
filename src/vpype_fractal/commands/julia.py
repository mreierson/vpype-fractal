"""Julia set contour command."""

import click
import vpype as vp
import vpype_cli

from vpype_fractal.engines.escape_time import julia_grid
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
@click.option("--x-min", type=float, default=-1.8, help="Left bound of z-plane.")
@click.option("--x-max", type=float, default=1.8, help="Right bound of z-plane.")
@click.option("--y-min", type=float, default=-1.2, help="Bottom bound of z-plane.")
@click.option("--y-max", type=float, default=1.2, help="Top bound of z-plane.")
@click.option(
    "--raster",
    is_flag=True,
    help="Store escape-time grid as raster image metadata for downstream "
    "raster commands (stipple, hatch, halftone, etc.).",
)
@click.option(
    "--emit-region",
    is_flag=True,
    help="Write the Julia interior (non-escaped points) as a region mask "
    "to vpype-raster region metadata for use with forregion | stipple/hatch. "
    "Skips contour generation when set (use --also-lines to get both).",
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
    raster: bool,
    emit_region: bool,
    also_lines: bool,
    palette_name: str | None,
    save_image: str | None,
) -> vp.Document:
    """Generate contour lines of a Julia set.

    Computes escape-time values for z^2 + c and extracts iso-contour lines.
    The constant c is set via --cx and --cy. Each contour level is placed
    on a separate layer.

    Layers are automatically colored using the active penset or a built-in
    gradient palette (use --palette to choose).

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

    if emit_region:
        from vpype_fractal._region import emit_region_mask

        interior_mask = escape >= max_iter
        emit_region_mask(
            doc,
            interior_mask,
            generator="julia",
            source=f"c={cx}+{cy}i",
            params={
                "cx": cx,
                "cy": cy,
                "max_iter": max_iter,
                "bounds": (x_min, x_max, y_min, y_max),
            },
            name=f"julia_interior_{cx}_{cy}",
        )
        if not also_lines:
            if raster or save_image:
                from vpype_fractal.commands._shared import _store_raster

                _store_raster(doc, escape, max_iter, palette_name)
            return doc

    return generate_escape_time_fractal(
        doc,
        x,
        y,
        escape,
        max_iter,
        levels,
        size,
        raster=raster,
        palette_name=palette_name,
        save_image=save_image,
    )


julia.help_group = "Fractals"  # type: ignore[attr-defined]
