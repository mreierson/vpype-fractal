"""Hilbert curve command."""

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
    type=click.IntRange(min=0, max=8),
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
def hilbert(
    doc: vp.Document,
    depth: int | None,
    size: float,
    pitch: float,
    target_layer: int | None,
    raster: bool,
) -> vp.Document:
    """Generate a Hilbert space-filling curve."""
    region = get_region_context(doc)

    if region is not None and region.is_region:
        # --- Region-aware mode ---
        effective_depth = depth if depth is not None else auto_depth(
            region.width, region.height, pitch, "hilbert"
        )
        # Generate at a nominal size, then scale to region bounds
        nominal_size = max(region.width, region.height)
        lc = generate_lsystem_fractal("hilbert", effective_depth, nominal_size)
        lc = scale_to_bounds(lc, region.bounds)

        # Clip to region mask if available. The mask covers the full image
        # (vpype-raster protocol), so pass the mask's full extent as bounds.
        if region.mask is not None:
            mask_h, mask_w = region.mask.shape
            lc = clip_lines_to_mask(
                lc, region.mask, (0.0, 0.0, float(mask_w), float(mask_h))
            )

        return finalize_fractal(doc, lc, target_layer=target_layer, raster=raster)

    # --- Standalone mode (no regression) ---
    effective_depth = depth if depth is not None else 5
    lc = generate_lsystem_fractal("hilbert", effective_depth, size)
    return finalize_fractal(doc, lc, target_layer=target_layer, raster=raster)


hilbert.help_group = "Fractals"  # type: ignore[attr-defined]
