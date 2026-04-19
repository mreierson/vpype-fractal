"""Shared utilities for fractal commands."""

from __future__ import annotations

import click
import numpy as np
import vpype as vp
from PIL import Image, ImageDraw, ImageFilter

from vpype_fractal.engines import expand, turtle_to_lines
from vpype_fractal.engines.contour import extract_contours_by_level
from vpype_fractal.palettes import DEFAULT_PALETTE, expand_palette
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


def _normalize_escape(
    escape: np.ndarray,
    max_iter: int,
) -> tuple[np.ndarray, np.ndarray]:
    """Normalize escape-time values to [0, 1] for coloring.

    Returns (mu, interior_mask).  High mu = near the fractal boundary
    (slow to escape), low mu = far exterior (quick to escape).
    Interior points (never escaped) are masked separately.

    Uses log normalization to compress dynamic range, then a power
    curve to concentrate color detail near the fractal boundary while
    keeping a smooth dark-to-bright gradient from far exterior inward.
    """
    interior = escape >= max_iter
    exterior = ~interior

    mu = np.zeros_like(escape)
    if np.any(exterior):
        # Log normalization: maps escape times to [0, 1] with compressed
        # dynamic range so detail is visible across all iteration ranges.
        raw = np.log(np.maximum(escape[exterior], 1.0)) / np.log(max_iter)
        mu[exterior] = raw

    return mu, interior


def _escape_to_image(
    escape: np.ndarray,
    max_iter: int,
) -> Image.Image:
    """Convert escape-time grid to a grayscale PIL image.

    Interior points are black.  The log-normalized escape values are
    mapped to brightness with a mild curve, preserving the visible
    contour bands that give fractals their characteristic depth.
    """
    mu, interior = _normalize_escape(escape, max_iter)

    # Power 1.8 gives dark backgrounds while preserving visible
    # gradient bands.  Capping at 90% leaves headroom for the glow
    # effect to add its luminous halo without washing out bands.
    mu = np.power(mu, 1.8)

    brightness = (mu * 230).astype(np.uint8)
    brightness[interior] = 0
    return Image.fromarray(brightness, mode="L")


def _store_raster(
    doc: vp.Document,
    escape: np.ndarray,
    max_iter: int,
    palette_name: str | None = None,
) -> None:
    """Store escape-time grid as a raster image.

    Resolution order for palette selection:
    1. Explicit ``palette_name`` argument
    2. Active penset in document metadata
    3. Default built-in palette
    """
    # Determine palette source
    palette = None
    if palette_name:
        palette = expand_palette(palette_name)
    else:
        palette = _get_palette_colors(doc)
        if palette is None:
            palette = expand_palette(DEFAULT_PALETTE)

    _publish_raster(doc, _escape_to_palette_image(escape, max_iter, palette))


def _get_palette_colors(doc: vp.Document) -> np.ndarray | None:
    """Extract RGB palette array from active penset, or None.

    When a penset has few colors (typical: 5-12 pens), the anchors are
    expanded into a smooth 256-color gradient via linear interpolation
    so raster output gets continuous color transitions instead of bands.
    """
    try:
        from vpype_penset.pipeline import PENSET_METADATA_KEY

        penset = doc.metadata.get(PENSET_METADATA_KEY)
        if penset is None:
            return None
        anchors = np.array(
            [[p.color.red, p.color.green, p.color.blue] for p in penset.pens],
            dtype=np.float64,
        )
        # Expand to 256 colors for smooth raster gradients
        n_anchors = len(anchors)
        if n_anchors < 2:
            return anchors.astype(np.uint8)
        t_anchors = np.linspace(0.0, 1.0, n_anchors)
        t_output = np.linspace(0.0, 1.0, 256)
        result = np.zeros((256, 3), dtype=np.float64)
        for ch in range(3):
            result[:, ch] = np.interp(t_output, t_anchors, anchors[:, ch])
        return np.clip(result, 0, 255).astype(np.uint8)
    except ImportError:
        return None


def _apply_penset_colors(doc: vp.Document, layer_ids: list[int]) -> None:
    """Assign penset colors to layers if an active penset exists.

    Samples pens from the active penset and sets ``vp_color`` (and
    ``vp_pen_width`` when defined) on each layer.  This mirrors what
    ``colorize`` does, but runs automatically so the user doesn't need
    an explicit colorize step.
    """
    if not layer_ids:
        return
    try:
        from vpype_penset.pipeline import PENSET_METADATA_KEY

        penset = doc.metadata.get(PENSET_METADATA_KEY)
        if penset is None:
            return
        pens = penset.sample_pens(len(layer_ids))
        for lid, pen in zip(layer_ids, pens, strict=True):
            doc[lid].set_property("vp_color", pen.color)
            if pen.width is not None:
                doc[lid].set_property("vp_pen_width", pen.width)
    except ImportError:
        return


def _apply_gradient_colors(
    doc: vp.Document,
    layer_ids: list[int],
    palette_name: str | None = None,
) -> None:
    """Apply gradient colors and stroke widths to SVG contour layers.

    Colors map dark→bright from outer→inner contours, matching the
    raster rendering's dark-background-bright-boundary aesthetic.
    With filled contours (via svg_fill post-processing), this creates
    a dark fractal body with bright highlights at the boundary.

    Stroke widths decrease from outer to inner for natural layering.
    """
    if not layer_ids:
        return

    name = palette_name or DEFAULT_PALETTE
    n = len(layer_ids)
    palette_full = expand_palette(name, 256)

    # Stroke width range in mm (converted to vpype units)
    min_width_mm = 0.3
    max_width_mm = 1.2
    mm_to_px = 96.0 / 25.4  # vpype uses 96 DPI

    for i, lid in enumerate(layer_ids):
        # Dark→bright mapping: outer contours (i=0) get dark palette colors,
        # inner contours (i=n-1) get bright palette colors.
        # With fills, this creates dark body + bright boundary highlights.
        t = i / max(n - 1, 1)
        idx = int(t * 255)
        r, g, b = int(palette_full[idx, 0]), int(palette_full[idx, 1]), int(palette_full[idx, 2])
        color = vp.Color(r, g, b)
        doc[lid].set_property("vp_color", color)

        # Stroke width: outer contours thicker, inner thinner
        width_mm = max_width_mm - t * (max_width_mm - min_width_mm)
        doc[lid].set_property("vp_pen_width", width_mm * mm_to_px)


def _add_glow(img: Image.Image) -> Image.Image:
    """Add selective dual-layer glow around bright regions only.

    The glow is applied selectively: only pixels above a brightness
    threshold contribute to the blur source.  This preserves the
    subtle gradient bands in the dark mid-range (which give fractals
    their topographic depth) while still creating an atmospheric
    halo around the bright fractal boundary.

    Two passes:
    1. Tight glow — edge definition and immediate halo
    2. Wide bloom — atmospheric depth and gradient separation
    """
    dim = max(img.width, img.height)
    base = np.array(img, dtype=np.float64)

    # Extract only the bright regions as the glow source.
    # Threshold at ~30% brightness so only boundary detail glows,
    # not the subtle dark gradient bands.
    bright = base.copy()
    if img.mode == "L":
        bright[bright < 75] = 0
    else:
        # For RGB: threshold on max channel
        mask = np.max(bright, axis=-1) < 75
        bright[mask] = 0

    bright_img = Image.fromarray(np.clip(bright, 0, 255).astype(np.uint8), mode=img.mode)

    # Pass 1: tight edge glow from bright regions only
    tight = bright_img.filter(ImageFilter.GaussianBlur(radius=max(2, dim // 100)))
    base += np.array(tight, dtype=np.float64) * 0.15

    # Pass 2: wide atmospheric bloom from bright regions only
    wide = bright_img.filter(ImageFilter.GaussianBlur(radius=max(4, dim // 25)))
    base += np.array(wide, dtype=np.float64) * 0.08

    return Image.fromarray(np.clip(base, 0, 255).astype(np.uint8), mode=img.mode)


def _escape_to_palette_image(
    escape: np.ndarray,
    max_iter: int,
    palette: np.ndarray,
) -> Image.Image:
    """Map escape-time values to palette colors with smooth gradient interpolation.

    Uses the smooth iteration count directly for rich color mapping.
    The palette's own color progression (dark anchors at the start,
    bright anchors at the end) naturally produces dark backgrounds and
    vivid boundary detail.  No additional darkening is applied, which
    preserves the visible escape-time contour bands that give fractals
    their characteristic topographic depth.

    Interior points (escape == max_iter) are rendered black.
    """
    n_colors = len(palette)
    interior = escape >= max_iter
    exterior = ~interior

    # Build the color-mapped image
    rgb = np.zeros((*escape.shape, 3), dtype=np.float64)

    if np.any(exterior):
        raw = escape[exterior]

        # Log-normalize escape times to [0, 1].
        mu = np.log(np.maximum(raw, 1.0)) / np.log(max_iter)

        # Power 1.8 gives dark backgrounds with visible gradient bands.
        # Capping at 90% leaves headroom for the glow effect.
        mu_curved = np.power(mu, 1.8)

        # Map across the full palette with smooth interpolation
        pos = mu_curved * (n_colors - 1)
        idx_lo = np.floor(pos).astype(int)
        idx_hi = np.minimum(idx_lo + 1, n_colors - 1)
        frac = pos - idx_lo
        idx_lo = np.clip(idx_lo, 0, n_colors - 1)

        c_lo = palette[idx_lo].astype(np.float64)
        c_hi = palette[idx_hi].astype(np.float64)
        colors = c_lo + frac[..., np.newaxis] * (c_hi - c_lo)

        # Subtle cyclic modulation: use the smooth iteration count's
        # fractional part to create visible contour bands within the
        # gradient.  This adds the topographic ring effect that gives
        # reference-quality renders their characteristic depth.
        cycle = 0.5 * (1.0 + np.cos(raw * 0.4))  # gentle sinusoidal bands
        colors *= (0.85 + 0.15 * cycle[..., np.newaxis])  # ±15% modulation

        # Cap at 90% to leave headroom for glow effect
        colors *= 0.9
        rgb[exterior] = colors

    rgb = np.clip(rgb, 0, 255).astype(np.uint8)
    rgb[interior] = 0

    img = Image.fromarray(rgb, mode="RGB")
    return _add_glow(img)


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

def clip_lines_to_mask(
    lc: vp.LineCollection,
    mask: np.ndarray,
    bounds: tuple[float, float, float, float],
) -> vp.LineCollection:
    """Clip line segments to a boolean region mask.

    Resamples each line at sub-pixel resolution, tests each point
    against the mask, and breaks lines at mask boundaries.

    Args:
        lc: Input line collection in document coordinates.
        mask: 2-D boolean array (height x width) -- True inside region.
        bounds: ``(minx, miny, maxx, maxy)`` in document units matching
            the mask extent.

    Returns:
        A new LineCollection containing only segments inside the mask.
    """
    minx, miny, maxx, maxy = bounds
    mask_h, mask_w = mask.shape
    sx = (mask_w - 1) / max(maxx - minx, 1e-10)
    sy = (mask_h - 1) / max(maxy - miny, 1e-10)

    result = vp.LineCollection()

    for line in lc:
        # Convert complex points to pixel coordinates for mask lookup
        xs = np.clip(((line.real - minx) * sx).astype(int), 0, mask_w - 1)
        ys = np.clip(((line.imag - miny) * sy).astype(int), 0, mask_h - 1)

        inside = mask[ys, xs]

        # Walk through the array and break into sub-lines where inside is True
        current_segment: list[complex] = []
        for i, pt in enumerate(line):
            if inside[i]:
                current_segment.append(pt)
            else:
                if len(current_segment) >= 2:
                    result.append(np.array(current_segment))
                current_segment = []

        if len(current_segment) >= 2:
            result.append(np.array(current_segment))

    return result


def scale_to_bounds(
    lc: vp.LineCollection,
    target_bounds: tuple[float, float, float, float],
    cover: bool = False,
    overfill: float = 1.0,
) -> vp.LineCollection:
    """Scale and translate a LineCollection to fill the target bounding box.

    The curve is scaled uniformly (preserving aspect ratio) and centered
    within the target bounds.

    Args:
        lc: The line collection to scale.
        target_bounds: ``(minx, miny, maxx, maxy)`` of the target box.
        cover: When ``True``, scale so the curve *covers* the target
            (the larger dimension fits exactly and the smaller overflows).
            When ``False`` (default), scale so the curve *fits* inside
            the target. ``cover`` is useful when a downstream clip will
            discard overflow but the curve has concave coverage (e.g. a
            Gosper snowflake whose corners would otherwise miss a
            tilted rectangle).
        overfill: Multiplier applied after cover/fit scaling. Values >1
            scale the curve larger than the target; the overflow is
            centered around the target so a downstream mask clip yields
            a filled region even when the curve has concave boundaries
            or the mask is rotated within the bbox. Use ~1.15 for
            Hilbert, ~1.55 for Gosper to guarantee coverage of any
            rotated rectangle inside the target.
    """
    src = lc.bounds()
    if src is None:
        return lc

    sx_min, sy_min, sx_max, sy_max = src
    sw = sx_max - sx_min
    sh = sy_max - sy_min
    if sw == 0 or sh == 0:
        return lc

    tx_min, ty_min, tx_max, ty_max = target_bounds
    tw = tx_max - tx_min
    th = ty_max - ty_min

    scale = max(tw / sw, th / sh) if cover else min(tw / sw, th / sh)
    scale *= overfill
    lc.scale(scale)

    # Re-read bounds after scale
    new_bounds = lc.bounds()
    if new_bounds is None:
        return lc

    nw = new_bounds[2] - new_bounds[0]
    nh = new_bounds[3] - new_bounds[1]

    # Center within target bounds
    offset_x = tx_min + (tw - nw) / 2 - new_bounds[0]
    offset_y = ty_min + (th - nh) / 2 - new_bounds[1]
    lc.translate(offset_x, offset_y)

    return lc


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

def _chaikin_smooth(line: np.ndarray, passes: int = 1, closed: bool = False) -> np.ndarray:
    """Chaikin corner-cutting: each segment becomes two subdivision points.

    Operates on a complex-valued polyline. ``closed=True`` treats the
    polyline as cyclic (no endpoint preservation); ``closed=False``
    preserves the first and last points so open paths keep their ends.
    """
    for _ in range(max(0, passes)):
        if len(line) < 3:
            return line
        if closed:
            # Cyclic: pair every vertex with the next, wrap at end.
            nxt = np.roll(line, -1)
            q = 0.75 * line + 0.25 * nxt
            r = 0.25 * line + 0.75 * nxt
            new = np.empty(len(line) * 2, dtype=line.dtype)
            new[0::2] = q
            new[1::2] = r
            line = np.append(new, new[0])  # re-close
        else:
            q = 0.75 * line[:-1] + 0.25 * line[1:]
            r = 0.25 * line[:-1] + 0.75 * line[1:]
            new = np.empty(len(line) * 2 - 2, dtype=line.dtype)
            new[0::2] = q
            new[1::2] = r
            # Preserve endpoints
            line = np.concatenate([[line[0]], new, [line[-1]]])
    return line


def generate_escape_time_fractal(
    doc: vp.Document,
    x: np.ndarray,
    y: np.ndarray,
    escape: np.ndarray,
    max_iter: int,
    levels: int,
    size: float,
    raster: bool = False,
    palette_name: str | None = None,
    save_image: str | None = None,
) -> vp.Document:
    """Build contour layers from escape-time data and add them to a document.

    When ``raster`` is True, stores the escape-time grid as a colored
    image in document metadata for downstream raster commands and skips
    contour generation.

    When ``save_image`` is set, saves the rendered image directly to
    that path (PNG/JPG) in addition to normal processing.

    ``palette_name`` selects a built-in gradient palette for coloring.
    """
    if raster or save_image:
        palette = None
        if palette_name:
            palette = expand_palette(palette_name)
        else:
            palette = _get_palette_colors(doc)
            if palette is None:
                palette = expand_palette(DEFAULT_PALETTE)

        img = _escape_to_palette_image(escape, max_iter, palette)

        if save_image:
            img.save(save_image)

        if raster:
            _publish_raster(doc, img)
            return doc

    # Hybrid level distribution: linear bulk across the escape range for
    # smooth far-exterior banding, plus geometric clustering near the body
    # boundary where filigree detail lives. Pure geomspace over-samples the
    # near-body range and under-samples the outer gradient, which produces
    # visible bands in the filled SVG's outer region.
    #
    # Body-fill behavior depends on Julia-set topology:
    #   - Connected body (main-cardioid c values like -0.7+0.27i): a single
    #     large interior polygon — fill with black works cleanly.
    #   - Dendritic/disconnected (e.g. c=-0.7269+0.1889i): no bulk interior,
    #     only filamentary structure. A body fill at any level overwrites
    #     the filigree with a big black blob. Skip the body fill entirely
    #     when the interior fraction is low (< ~5% of grid cells).
    interior_count = int(np.count_nonzero(escape >= max_iter))
    interior_frac = interior_count / escape.size
    add_body_fill = interior_frac >= 0.05
    n_linear = max(levels - levels // 3, levels // 2 + 1)
    n_geom = max(levels - n_linear, 2)
    linear_part = np.linspace(
        max(1.0, max_iter * 0.01), max_iter * 0.6, n_linear,
    ).tolist()
    geom_part = np.geomspace(
        max_iter * 0.6, max_iter * 0.95, n_geom + 1,
    ).tolist()[1:]  # extend inward to capture near-body filigree
    level_values = sorted(linear_part + geom_part)
    if add_body_fill:
        level_values.append(max_iter - 0.5)

    # Skip ~5% of boundary cells to prevent edge artifacts
    grid_margin = max(2, escape.shape[1] // 20)

    level_lcs = extract_contours_by_level(x, y, escape, level_values, margin=grid_margin)
    non_empty = [lc for lc in level_lcs if len(lc) > 0]
    if non_empty:
        # Close contour paths by connecting last point to first, then
        # apply one pass of Chaikin corner-cutting to soften the stair-step
        # artifacts inherent to marching-squares output on a pixel grid.
        # A single pass doubles vertex count and halves perceived jaggedness
        # without materially changing the contour's geometry.
        for idx, lc in enumerate(non_empty):
            closed_lc = vp.LineCollection()
            for line in lc:
                if len(line) >= 3:
                    dist = abs(line[-1] - line[0])
                    extent = max(abs(line.max() - line.min()), 1e-10)
                    is_closed = dist / extent < 0.1
                    if is_closed:
                        line = np.append(line, line[0])
                    line = _chaikin_smooth(line, passes=2, closed=is_closed)
                closed_lc.append(line)
            non_empty[idx] = closed_lc

        scale_all_to_size(non_empty, size)
        new_layer_ids = []
        for lc in non_empty:
            lid = doc.free_id()
            doc[lid] = lc
            new_layer_ids.append(lid)

        # Separate the body-fill layer (last) from the gradient layers.
        # Body contour was added last to level_values; its layer must be
        # colored black so filled SVG output shows a dark fractal body
        # instead of inheriting the brightest palette color. When the
        # fractal has no bulk interior (dendritic Julia), there is no
        # body layer to separate.
        if add_body_fill and len(new_layer_ids) > 1:
            gradient_ids = new_layer_ids[:-1]
            body_id = new_layer_ids[-1]
        else:
            gradient_ids = new_layer_ids
            body_id = None

        # Try penset first, then fall back to built-in palette colors
        penset_colors = _get_palette_colors(doc)
        if penset_colors is not None:
            _apply_penset_colors(doc, gradient_ids)
        else:
            _apply_gradient_colors(doc, gradient_ids, palette_name)

        if body_id is not None:
            doc[body_id].set_property("vp_color", vp.Color(0, 0, 0))
            # Hairline stroke so plotter-side it still produces a clean
            # body outline; fill mode renders the black interior.
            doc[body_id].set_property("vp_pen_width", 0.3 * 96.0 / 25.4)

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
        new_layer_ids = []
        for lc in non_empty:
            lid = doc.free_id()
            doc[lid] = lc
            new_layer_ids.append(lid)
        # Try penset first, then fall back to built-in palette
        penset_colors = _get_palette_colors(doc)
        if penset_colors is not None:
            _apply_penset_colors(doc, new_layer_ids)
        else:
            _apply_gradient_colors(doc, new_layer_ids)

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
        new_layer_ids = []
        for lc in lcs:
            lid = doc.free_id()
            doc[lid] = lc
            new_layer_ids.append(lid)
        # Try penset first, then fall back to built-in palette
        penset_colors = _get_palette_colors(doc)
        if penset_colors is not None:
            _apply_penset_colors(doc, new_layer_ids)
        else:
            _apply_gradient_colors(doc, new_layer_ids)

        if raster:
            # Merge all layers into one LineCollection for rasterization
            merged = vp.LineCollection()
            for lc in lcs:
                merged.extend(lc)
            _store_raster_from_lines(doc, merged)

    return doc
