"""Gosper flowsnake curve command."""

import click
import vpype as vp
import vpype_cli

from .._region import auto_depth, get_region_context
from ._shared import (
    clip_lines_to_mask,
    finalize_fractal,
    fractal_options,
    generate_lsystem_fractal,
    scale_to_bounds,
)


@click.command()
@click.option(
    "-d",
    "--depth",
    type=click.IntRange(min=0, max=6),
    default=None,
    help="Recursion depth (auto-calculated in region mode when omitted).",
)
@click.option(
    "-s",
    "--size",
    type=vpype_cli.LengthType(),
    default="100mm",
    help="Overall size (ignored in region mode).",
)
@click.option(
    "--pitch",
    type=vpype_cli.LengthType(),
    default="1mm",
    help="Line spacing for auto-depth calculation in region mode.",
)
@fractal_options
@vpype_cli.global_processor
def gosper(
    doc: vp.Document,
    depth: int | None,
    size: float,
    pitch: float,
    target_layer: int | None,
    raster: bool,
) -> vp.Document:
    """Generate a Gosper flowsnake curve."""
    region = get_region_context(doc)

    if region is not None and region.is_region:
        # --- Region-aware mode ---
        # Gosper's hexagonal outline has concave fractal notches; scale
        # ~1.55x so the hex comfortably contains any rotated rectangle
        # within the bbox. Feed the inflated size into depth calculation
        # so the requested pitch is preserved after the overfill.
        overfill = 1.55
        effective_depth = (
            depth
            if depth is not None
            else auto_depth(region.width * overfill, region.height * overfill, pitch, "gosper")
        )
        nominal_size = max(region.width, region.height)
        lc = generate_lsystem_fractal("gosper", effective_depth, nominal_size)
        lc = scale_to_bounds(lc, region.bounds, cover=True, overfill=overfill)

        # Clip to region mask if available. The mask covers the full image
        # (vpype-raster protocol), so pass the mask's full extent as bounds.
        if region.mask is not None:
            mask_h, mask_w = region.mask.shape
            lc = clip_lines_to_mask(lc, region.mask, (0.0, 0.0, float(mask_w), float(mask_h)))

        return finalize_fractal(doc, lc, target_layer=target_layer, raster=raster)

    # --- Standalone mode (no regression) ---
    effective_depth = depth if depth is not None else 4
    lc = generate_lsystem_fractal("gosper", effective_depth, size)
    return finalize_fractal(doc, lc, target_layer=target_layer, raster=raster)


gosper.help_group = "Fractals"  # type: ignore[attr-defined]
