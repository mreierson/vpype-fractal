"""Shared utilities for fractal commands."""

from __future__ import annotations

import click
import numpy as np
import vpype as vp
from PIL import Image, ImageDraw

from vpype_fractal.engines import expand, turtle_to_lines
from vpype_fractal.engines.contour import extract_contours_by_level
from vpype_fractal.presets import PRESETS

# Metadata key compatible with vpype-raster's loadimage
_RASTER_IMAGE_KEY = "vpype_raster.image"

# Default raster resolution for vector→image conversion
_RASTER_RESOLUTION = 800


# ---------------------------------------------------------------------------
# Plugin-level --raster and --layer options
# ---------------------------------------------------------------------------

def fractal_options(fn: click.BaseCommand) -> click.BaseCommand:
    """Add standard ``--layer`` and ``--raster`` options to a fractal command."""
    fn = click.option(
        "--raster",
        is_flag=True,
        help="Store fractal as raster image metadata for downstream "
        "raster commands (stipple, hatch, halftone, etc.).",
    )(fn)
    fn = click.option(
        "-ly",
        "--layer",
        "target_layer",
        type=int,
        default=None,
        help="Target layer (default: new layer).",
    )(fn)
    return fn


def finalize_fractal(
    doc: vp.Document,
    lc: vp.LineCollection,
    *,
    target_layer: int | None = None,
    raster: bool = False,
) -> vp.Document:
    """Add a LineCollection to the document and optionally store as raster.

    This is the standard exit path for generator-style fractal commands
    that have been converted to global_processor.
    """
    if lc and len(lc) > 0:
        layer_id = target_layer if target_layer is not None else doc.free_id()
        doc[layer_id] = lc
        if raster:
            _store_raster_from_lines(doc, lc)
    return doc


# ---------------------------------------------------------------------------
# Raster storage helpers
# ---------------------------------------------------------------------------

def _make_image_data(pil_image: Image.Image) -> object:
    """Create an ImageData-compatible object from a PIL image.

    Uses vpype-raster's ImageData when available, otherwise a duck-type
    compatible stand-in.
    """
    try:
        from vpype_raster.core.image import ImageData
        return ImageData.from_pil(pil_image)
    except ImportError:
        w, h = pil_image.size
        return _ImageCompat(
            array=np.array(pil_image, dtype=np.uint8),
            width=w,
            height=h,
            path=None,
            mode=pil_image.mode,
        )


def _publish_raster(doc: vp.Document, pil_image: Image.Image) -> None:
    """Store a PIL image in document metadata for downstream raster commands."""
    w, h = pil_image.size
    doc.metadata[_RASTER_IMAGE_KEY] = _make_image_data(pil_image)
    doc.metadata["raster_scale"] = 1.0
    doc.page_size = (float(w), float(h))


def _store_raster(
    doc: vp.Document,
    escape: np.ndarray,
    max_iter: int,
) -> None:
    """Store escape-time grid as a grayscale raster image."""
    normalized = (escape / max_iter * 255).astype(np.uint8)
    _publish_raster(doc, Image.fromarray(normalized, mode="L"))


def _store_raster_from_lines(
    doc: vp.Document,
    lc: vp.LineCollection,
    resolution: int = _RASTER_RESOLUTION,
) -> None:
    """Render a LineCollection to a grayscale image and store as raster metadata.

    Lines are drawn as black strokes on a white background, producing a
    tone map where dense geometry appears dark — suitable for downstream
    raster commands (stipple, hatch, halftone, etc.).
    """
    bounds = lc.bounds()
    if bounds is None:
        return

    x_min, y_min, x_max, y_max = bounds
    width = x_max - x_min
    height = y_max - y_min
    if width == 0 or height == 0:
        return

    # Compute pixel dimensions preserving aspect ratio
    aspect = height / width
    if width >= height:
        px_w = resolution
        px_h = max(1, int(resolution * aspect))
    else:
        px_h = resolution
        px_w = max(1, int(resolution / aspect))

    img = Image.new("L", (px_w, px_h), 255)
    draw = ImageDraw.Draw(img)

    sx = (px_w - 1) / width if width > 0 else 1.0
    sy = (px_h - 1) / height if height > 0 else 1.0

    for line in lc:
        pts = [
            (int((p.real - x_min) * sx), int((p.imag - y_min) * sy))
            for p in line
        ]
        if len(pts) >= 2:
            draw.line(pts, fill=0, width=1)

    _publish_raster(doc, img)


class _ImageCompat:
    """Minimal duck-type stand-in for vpype-raster's ImageData."""

    __slots__ = ("array", "width", "height", "path", "mode")

    def __init__(
        self,
        array: np.ndarray,
        width: int,
        height: int,
        path: object,
        mode: str,
    ) -> None:
        self.array = array
        self.width = width
        self.height = height
        self.path = path
        self.mode = mode

    def to_pil(self) -> Image.Image:
        return Image.fromarray(self.array, mode=self.mode)


# ---------------------------------------------------------------------------
# L-system helpers
# ---------------------------------------------------------------------------

def generate_lsystem_fractal(
    preset_name: str,
    depth: int,
    size: float,
) -> vp.LineCollection:
    """Generate an L-system fractal from a named preset, scaled to fit size."""
    preset = PRESETS[preset_name]
    instructions = expand(preset.axiom, preset.rules, depth)
    lc = turtle_to_lines(
        instructions,
        angle=preset.angle,
        step=1.0,
        heading=preset.heading,
    )
    return scale_to_size(lc, size)


# ---------------------------------------------------------------------------
# Scaling helpers
# ---------------------------------------------------------------------------

def scale_to_size(lc: vp.LineCollection, size: float) -> vp.LineCollection:
    """Scale a LineCollection to fit within the given size, placed at origin."""
    if len(lc) == 0:
        return lc

    bounds = lc.bounds()
    if bounds is None:
        return lc

    x_min, y_min, x_max, y_max = bounds
    width = x_max - x_min
    height = y_max - y_min
    max_dim = max(width, height)

    if max_dim == 0:
        return lc

    scale = size / max_dim
    lc.scale(scale)

    # Translate so bounding box starts at origin
    bounds = lc.bounds()
    if bounds is not None:
        lc.translate(-bounds[0], -bounds[1])

    return lc


def scale_all_to_size(
    collections: list[vp.LineCollection],
    size: float,
) -> list[vp.LineCollection]:
    """Scale multiple LineCollections uniformly to fit within size."""
    all_bounds = [lc.bounds() for lc in collections if len(lc) > 0]
    valid = [b for b in all_bounds if b is not None]
    if not valid:
        return collections

    x_min = min(b[0] for b in valid)
    y_min = min(b[1] for b in valid)
    x_max = max(b[2] for b in valid)
    y_max = max(b[3] for b in valid)

    width = x_max - x_min
    height = y_max - y_min
    max_dim = max(width, height)
    if max_dim == 0:
        return collections

    factor = size / max_dim
    for lc in collections:
        if len(lc) > 0:
            lc.scale(factor)
            lc.translate(-x_min * factor, -y_min * factor)

    return collections


# ---------------------------------------------------------------------------
# Escape-time fractal helper
# ---------------------------------------------------------------------------

def generate_escape_time_fractal(
    doc: vp.Document,
    x: np.ndarray,
    y: np.ndarray,
    escape: np.ndarray,
    max_iter: int,
    levels: int,
    size: float,
    raster: bool = False,
) -> vp.Document:
    """Build contour layers from escape-time data and add them to a document.

    When ``raster`` is True, stores the escape-time grid as a grayscale
    image in document metadata for downstream raster commands and skips
    contour generation (the downstream command produces the geometry).
    """
    if raster:
        _store_raster(doc, escape, max_iter)
        return doc

    level_values = np.linspace(1, max_iter * 0.8, levels).tolist()

    # Skip ~5% of boundary cells to prevent edge artifacts
    grid_margin = max(2, escape.shape[1] // 20)

    level_lcs = extract_contours_by_level(x, y, escape, level_values, margin=grid_margin)
    non_empty = [lc for lc in level_lcs if len(lc) > 0]
    if non_empty:
        scale_all_to_size(non_empty, size)
        for lc in non_empty:
            doc[doc.free_id()] = lc

    return doc


# ---------------------------------------------------------------------------
# Density contour helper (attractors)
# ---------------------------------------------------------------------------

def generate_density_contours(
    doc: vp.Document,
    points: np.ndarray,
    resolution: int,
    levels: int,
    size: float,
) -> vp.Document:
    """Build density contours from a point cloud and add to document."""
    from scipy.ndimage import gaussian_filter

    x_vals = points.real
    y_vals = points.imag

    aspect = (y_vals.max() - y_vals.min()) / (x_vals.max() - x_vals.min())
    nx = resolution
    ny = max(1, int(resolution * aspect))

    density, x_edges, y_edges = np.histogram2d(x_vals, y_vals, bins=[nx, ny])
    density = density.T

    density = gaussian_filter(density, sigma=1.5)

    x = (x_edges[:-1] + x_edges[1:]) / 2
    y = (y_edges[:-1] + y_edges[1:]) / 2

    max_density = density.max()
    if max_density <= 0:
        return doc

    level_values = np.linspace(max_density * 0.02, max_density * 0.8, levels).tolist()

    grid_margin = max(2, nx // 20)
    level_lcs = extract_contours_by_level(x, y, density, level_values, margin=grid_margin)
    non_empty = [lc for lc in level_lcs if len(lc) > 0]
    if non_empty:
        scale_all_to_size(non_empty, size)
        for lc in non_empty:
            doc[doc.free_id()] = lc

    return doc


# ---------------------------------------------------------------------------
# Attractor trajectory helper
# ---------------------------------------------------------------------------

def generate_attractor_layers(
    doc: vp.Document,
    points: np.ndarray,
    layers: int,
    size: float,
    smooth: int = 0,
    raster: bool = False,
) -> vp.Document:
    """Split attractor trajectory into layers and add to document.

    When ``raster`` is True, renders all layers to a raster image for
    downstream raster commands.
    """
    from vpype_fractal.engines.attractor import smooth_trajectory

    max_polyline = 5000
    chunks = np.array_split(points, layers)
    lcs: list[vp.LineCollection] = []
    for chunk in chunks:
        if len(chunk) < 2:
            continue
        if smooth > 0:
            chunk = smooth_trajectory(chunk, samples_per_segment=smooth)
        lc = vp.LineCollection()
        for start in range(0, len(chunk), max_polyline - 1):
            seg = chunk[start : start + max_polyline]
            if len(seg) >= 2:
                lc.append(seg)
        lcs.append(lc)

    if lcs:
        scale_all_to_size(lcs, size)
        for lc in lcs:
            doc[doc.free_id()] = lc

        if raster:
            # Merge all layers into one LineCollection for rasterization
            merged = vp.LineCollection()
            for lc in lcs:
                merged.extend(lc)
            _store_raster_from_lines(doc, merged)

    return doc
