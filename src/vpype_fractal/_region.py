"""Shared region detection utility for region-aware fractal commands.

Provides helpers to detect whether a fractal command is running inside a
vpype-raster ``forregion`` block and to compute automatic recursion depth
from region dimensions.  This module is internal -- it is imported by
sibling command modules but not exported from the package.
"""

from __future__ import annotations

import dataclasses
import math
from typing import Any

import vpype as vp

# ---------------------------------------------------------------------------
# Optional vpype-raster integration
# ---------------------------------------------------------------------------

try:
    from vpype_raster.commands.forregion import CURRENT_REGION_KEY
    from vpype_raster.core.regions import REGIONS_METADATA_KEY

    HAS_RASTER = True
except ImportError:
    CURRENT_REGION_KEY = "vpype_raster.current_region"
    REGIONS_METADATA_KEY = "vpype_raster.regions"
    HAS_RASTER = False

try:
    from vpype_raster.core.regions import Region as _RasterRegion
    from vpype_raster.core.regions import RegionSet as _RasterRegionSet

    _HAS_REGION_TYPES = True
except ImportError:
    _RasterRegion = None  # type: ignore[assignment]
    _RasterRegionSet = None  # type: ignore[assignment]
    _HAS_REGION_TYPES = False


# ---------------------------------------------------------------------------
# Region context dataclass
# ---------------------------------------------------------------------------


@dataclasses.dataclass
class RegionContext:
    """Describes the spatial context in which a fractal command runs.

    Attributes:
        bounds: Axis-aligned bounding box ``(minx, miny, maxx, maxy)``
            in vpype document units (CSS px at 96 dpi).
        mask: Boolean numpy array marking valid pixels inside the
            region, or ``None`` when no mask is available.
        width: Region width in document units.
        height: Region height in document units.
        is_region: ``True`` when the command is executing inside a
            ``forregion`` block, ``False`` when standalone.
    """

    bounds: tuple[float, float, float, float]
    mask: Any  # NDArray[np.bool_] | None
    width: float
    height: float
    is_region: bool


# ---------------------------------------------------------------------------
# Region detection
# ---------------------------------------------------------------------------


def get_region_context(document: vp.Document) -> RegionContext | None:
    """Build a :class:`RegionContext` from the current pipeline state.

    Detection order:

    1. If vpype-raster is installed **and** a ``forregion`` block is
       active (``CURRENT_REGION_KEY`` present in metadata), extract
       bounds and mask from the current :class:`Region`.
    2. Otherwise fall back to the document's own bounding box.
    3. If neither source provides bounds, return ``None``.

    Args:
        document: The vpype :class:`Document` passed to the command's
            global processor.

    Returns:
        A populated :class:`RegionContext`, or ``None`` when no
        spatial extent can be determined.
    """
    # --- path 1: inside a forregion block ---
    if CURRENT_REGION_KEY in document.metadata:
        region = document.metadata[CURRENT_REGION_KEY]
        # Region.bounds is (x, y, w, h) in pixel coordinates
        rx, ry, rw, rh = region.bounds
        bounds = (float(rx), float(ry), float(rx + rw), float(ry + rh))
        mask = region.mask if hasattr(region, "mask") else None
        return RegionContext(
            bounds=bounds,
            mask=mask,
            width=float(rw),
            height=float(rh),
            is_region=True,
        )

    # --- path 2: standalone -- use document bounds ---
    doc_bounds = document.bounds()
    if doc_bounds is not None:
        minx, miny, maxx, maxy = doc_bounds
        return RegionContext(
            bounds=(minx, miny, maxx, maxy),
            mask=None,
            width=maxx - minx,
            height=maxy - miny,
            is_region=False,
        )

    # --- path 3: empty document, no page size ---
    if document.page_size is not None:
        pw, ph = document.page_size
        return RegionContext(
            bounds=(0.0, 0.0, pw, ph),
            mask=None,
            width=pw,
            height=ph,
            is_region=False,
        )

    return None


# ---------------------------------------------------------------------------
# Automatic depth calculation
# ---------------------------------------------------------------------------

# Hex scaling factor for Gosper curves: each level multiplies the linear
# extent by sqrt(7).
_GOSPER_SCALE = math.sqrt(7)


def auto_depth(
    width: float,
    height: float,
    pitch: float,
    curve_type: str,
) -> int:
    """Compute a recursion depth that fills a region at the given pitch.

    The pitch is the approximate distance between adjacent curve
    segments (in the same units as *width* and *height*).

    Args:
        width: Region width.
        height: Region height.
        pitch: Desired spacing between adjacent curve segments.
        curve_type: One of ``"hilbert"``, ``"gosper"``, or ``"peano"``.

    Returns:
        An integer recursion depth, clamped to a curve-specific safe
        range.

    Raises:
        ValueError: If *curve_type* is not recognised.
    """
    extent = min(width, height)
    if extent <= 0 or pitch <= 0:
        return 1

    ratio = extent / pitch

    if curve_type == "hilbert":
        # Hilbert: 2^depth segments per side
        depth = int(math.log2(ratio))
        return max(1, min(depth, 10))

    if curve_type == "gosper":
        # Gosper: sqrt(7)^depth scaling per level
        depth = int(math.log(ratio) / math.log(_GOSPER_SCALE))
        return max(1, min(depth, 10))

    if curve_type == "peano":
        # Peano: 3^depth segments per side
        depth = int(math.log(ratio) / math.log(3))
        return max(1, min(depth, 8))

    msg = f"Unknown curve type: {curve_type!r}"
    raise ValueError(msg)


# ---------------------------------------------------------------------------
# Region emission (ADR-001: --emit-region protocol)
# ---------------------------------------------------------------------------


def emit_region_mask(
    document: vp.Document,
    mask: Any,  # NDArray[np.bool_]
    *,
    generator: str,
    source: str = "",
    params: dict | None = None,
    color: tuple[int, int, int] = (255, 255, 255),
    name: str | None = None,
) -> None:
    """Write a boolean region mask to the shared region-set metadata slot.

    Implements the emission side of ADR-001 ("cross-plugin region-producer
    protocol"). Any fractal command with a natural 2D region
    interpretation can call this to make its output consumable by
    vpype-raster's ``forregion`` and downstream region-aware generators.

    The metadata key and dataclass shape are documented in vpype-raster's
    ``core/regions.py`` (``REGIONS_METADATA_KEY`` = ``"vpype_raster.regions"``).
    When vpype-raster is installed, we use its real ``Region`` / ``RegionSet``
    types. Otherwise we fall back to a duck-typed namespace with the
    same attribute surface so downstream code that soft-imports still
    works.

    Args:
        document: The vpype document being mutated.
        mask: A 2D boolean numpy array; ``True`` = inside the region.
        generator: Short name of the emitting command (e.g. ``"mandelbrot"``).
        source: Optional source descriptor (e.g. the c-value string).
        params: Optional dict of generator params for downstream inspection.
        color: Representative RGB for the region. Defaults to white.
        name: Optional human-readable name for the region.
    """
    import numpy as _np

    mask_arr = _np.asarray(mask, dtype=bool)
    h, w = mask_arr.shape
    if not mask_arr.any():
        # Empty mask — skip rather than emit a zero-area region, which
        # would confuse forregion's iterator.
        return

    # Compute bounding box (x, y, w, h) of the True cells
    ys, xs = _np.nonzero(mask_arr)
    x0, x1 = int(xs.min()), int(xs.max())
    y0, y1 = int(ys.min()), int(ys.max())
    bounds = (x0, y0, x1 - x0 + 1, y1 - y0 + 1)
    area_px = int(mask_arr.sum())

    if _HAS_REGION_TYPES:
        region = _RasterRegion(
            index=0,
            mask=mask_arr,
            area_px=area_px,
            bounds=bounds,
            color=color,
            name=name,
        )
        region_set = _RasterRegionSet(
            generator=generator,
            source=source,
            image_size=(w, h),
            regions=[region],
            generator_params=params or {},
        )
    else:
        # Duck-typed fallback — same attribute surface as vpype-raster's
        # RegionSet/Region so consumers that soft-import can still read us.
        region = _FallbackRegion(
            index=0,
            mask=mask_arr,
            area_px=area_px,
            bounds=bounds,
            color=color,
            name=name,
        )
        region_set = _FallbackRegionSet(
            generator=generator,
            source=source,
            image_size=(w, h),
            regions=[region],
            generator_params=params or {},
        )

    document.metadata[REGIONS_METADATA_KEY] = region_set


@dataclasses.dataclass
class _FallbackRegion:
    """Used when vpype-raster isn't installed. Mirrors ``vpype_raster.core.regions.Region``."""

    index: int
    mask: Any
    area_px: int
    bounds: tuple[int, int, int, int]
    color: tuple[int, int, int]
    name: str | None = None


@dataclasses.dataclass
class _FallbackRegionSet:
    """Used when vpype-raster isn't installed. Mirrors ``vpype_raster.core.regions.RegionSet``."""

    generator: str
    source: str
    image_size: tuple[int, int]
    regions: list
    generator_params: dict = dataclasses.field(default_factory=dict)
