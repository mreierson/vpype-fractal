"""Post-process SVG files for high-quality fractal output.

Usage:
    python -m vpype_fractal.svg_fill input.svg output.svg [--bg image.png]

Two modes:
  Without --bg:  Adds a dark background rectangle and fill attributes to
                 contour layers, creating a pure-vector SVG with gradient
                 fills that matches the raster look.
  With --bg:     Embeds a raster PNG as the background and overlays
                 semi-transparent vector contour lines on top.
"""

from __future__ import annotations

import base64
import re
import sys
from pathlib import Path


def add_fills(svg_content: str, fill_opacity: float = 1.0) -> str:
    """Replace fill="none" with the layer's stroke color on each group.

    When ``fill_opacity`` < 1, uses a graduated opacity schedule: darker
    fills (outer gradient) get lower opacity so the outer doesn't
    accumulate into an opaque wall, while brighter fills (near the
    fractal boundary) stay closer to full opacity so filigree detail
    pops.  This preserves the raster's dark-atmospheric-exterior +
    bright-luminous-filigree aesthetic.

    ``fill_opacity`` is the opacity floor for the darkest gradient fill;
    the brightest non-body fill receives full opacity.  The black body
    fill always stays fully opaque.
    """

    def _brightness(hex_color: str) -> float:
        try:
            r = int(hex_color[1:3], 16)
            g = int(hex_color[3:5], 16)
            b = int(hex_color[5:7], 16)
            return (r + g + b) / (3 * 255)
        except (ValueError, IndexError):
            return 0.5

    def _replace_fill(match: re.Match[str]) -> str:
        group_tag = match.group(0)
        stroke_match = re.search(r'stroke="(#[a-fA-F0-9]{6})"', group_tag)
        if stroke_match:
            color = stroke_match.group(1)
            replacement = f'fill="{color}"'
            is_body = color.lower() in ("#000000", "#000")
            if fill_opacity < 1.0 and not is_body:
                # Graduated opacity: dark strokes get ``fill_opacity``,
                # bright strokes get 1.0, linear ramp between.
                b = _brightness(color)
                op = fill_opacity + (1.0 - fill_opacity) * b
                replacement += f' fill-opacity="{op:.2f}"'
            return group_tag.replace('fill="none"', replacement)
        return group_tag

    return re.sub(
        r'<g[^>]*fill="none"[^>]*stroke="[^"]*"[^>]*>',
        _replace_fill,
        svg_content,
    )


def _collect_layer_colors(svg_content: str) -> list[str]:
    """Return ordered list of stroke colors from vpype's layer <g> tags.

    Order is document order, which for vpype-fractal output matches
    outer→inner contour order (body last).
    """
    return re.findall(
        r'<g[^>]*stroke="(#[a-fA-F0-9]{6})"[^>]*>',
        svg_content,
    )


def _centroid_from_viewbox(svg_content: str) -> tuple[float, float, float]:
    """Return (cx, cy, r) for a gradient anchored at the viewbox center."""
    vb_match = re.search(r'viewBox="([^"]*)"', svg_content)
    if not vb_match:
        return 0.0, 0.0, 100.0
    parts = vb_match.group(1).split()
    if len(parts) != 4:
        return 0.0, 0.0, 100.0
    vb_x, vb_y, vb_w, vb_h = map(float, parts)
    cx = vb_x + vb_w / 2
    cy = vb_y + vb_h / 2
    r = max(vb_w, vb_h) / 2
    return cx, cy, r


def add_radial_band_gradients(svg_content: str) -> str:
    """Replace per-band solid fills with radialGradient interpolating to the next band.

    Each gradient is a radial gradient centered on the viewbox centroid,
    going from 0% = current band color to 100% = next-brighter band color.
    This smooths the boundary between contour bands so the SVG shows a
    continuous gradient rather than discrete band steps.

    The final body layer (black) is left as a solid fill.
    """
    colors = _collect_layer_colors(svg_content)
    if len(colors) < 2:
        return svg_content

    cx, cy, r = _centroid_from_viewbox(svg_content)
    # Identify body (last layer if black)
    body_last = colors[-1].lower() in ("#000000", "#000")
    gradient_range = len(colors) - (1 if body_last else 0)

    defs = []
    for i in range(gradient_range):
        this_color = colors[i]
        next_color = colors[i + 1] if i + 1 < len(colors) else colors[i]
        defs.append(
            f'<radialGradient id="band-grad-{i}" cx="{cx:.1f}" cy="{cy:.1f}" r="{r:.1f}" '
            f'gradientUnits="userSpaceOnUse">'
            f'<stop offset="0%" stop-color="{this_color}"/>'
            f'<stop offset="100%" stop-color="{next_color}"/>'
            f"</radialGradient>"
        )

    # Replace each group's fill with url(#band-grad-i) in document order.
    # Body layer keeps its solid black fill.
    group_counter = [0]

    def _replace(match: re.Match[str]) -> str:
        group_tag = match.group(0)
        stroke_match = re.search(r'stroke="(#[a-fA-F0-9]{6})"', group_tag)
        if not stroke_match:
            return group_tag
        color = stroke_match.group(1)
        is_body = body_last and color.lower() in ("#000000", "#000")
        if is_body:
            return group_tag.replace('fill="none"', f'fill="{color}"')
        idx = group_counter[0]
        group_counter[0] += 1
        return group_tag.replace('fill="none"', f'fill="url(#band-grad-{idx})"')

    result = re.sub(
        r'<g[^>]*fill="none"[^>]*stroke="[^"]*"[^>]*>',
        _replace,
        svg_content,
    )

    # Inject gradient defs
    defs_block = "\n".join(f"    {d}" for d in defs)
    for marker in ["<defs/>", "</defs>"]:
        if marker in result:
            if marker == "<defs/>":
                result = result.replace(marker, f"<defs>\n{defs_block}\n  </defs>", 1)
            else:
                result = result.replace(marker, f"{defs_block}\n  {marker}", 1)
            break
    return result


_GLOW_FILTER = """
  <filter id="fractal-glow" x="-20%" y="-20%" width="140%" height="140%">
    <feGaussianBlur stdDeviation="1.5" result="soft"/>
    <feGaussianBlur in="soft" stdDeviation="4" result="halo"/>
    <feMerge>
      <feMergeNode in="halo"/>
      <feMergeNode in="soft"/>
      <feMergeNode in="SourceGraphic"/>
    </feMerge>
  </filter>
"""


def _inject_glow(svg_content: str) -> str:
    """Add a two-pass Gaussian glow filter and apply it to layer groups.

    Emulates the raster render's atmospheric halo around bright filigree
    in pure SVG. Uses feGaussianBlur + feMerge. No rasterization — stays
    vector and resolution-independent on re-export.
    """
    if 'id="fractal-glow"' in svg_content:
        return svg_content
    for marker in ["<defs/>", "</defs>"]:
        if marker in svg_content:
            svg_content = svg_content.replace(
                marker,
                "<defs>" + _GLOW_FILTER + "</defs>"
                if marker == "<defs/>"
                else _GLOW_FILTER + marker,
                1,
            )
            break
    return re.sub(
        r'(<g[^>]*stroke="[^"]*"[^>]*?)(>)',
        r'\1 filter="url(#fractal-glow)"\2',
        svg_content,
    )


def _add_background_rect(svg_content: str, color: str = "#000000") -> str:
    """Add a dark background rectangle as the first SVG element.

    This makes dark outer contour fills blend naturally with the
    background, while bright inner contour fills create the gradient
    detail — matching the raster rendering's appearance.
    """
    vb_match = re.search(r'viewBox="([^"]*)"', svg_content)
    if not vb_match:
        return svg_content

    parts = vb_match.group(1).split()
    if len(parts) != 4:
        return svg_content

    vb_x, vb_y, vb_w, vb_h = parts
    rect = f'  <rect x="{vb_x}" y="{vb_y}" width="{vb_w}" height="{vb_h}" fill="{color}" />\n'

    for marker in ["<defs/>", "</defs>"]:
        if marker in svg_content:
            return svg_content.replace(marker, marker + "\n" + rect, 1)

    return svg_content


def _extract_darkest_color(svg_content: str) -> str:
    """Extract the darkest stroke color from the SVG for background use."""
    colors = re.findall(r'stroke="(#[a-fA-F0-9]{6})"', svg_content)
    if not colors:
        return "#000000"

    def _brightness(hex_color: str) -> int:
        r = int(hex_color[1:3], 16)
        g = int(hex_color[3:5], 16)
        b = int(hex_color[5:7], 16)
        return r + g + b

    return min(colors, key=_brightness)


def _set_stroke_opacity(svg_content: str, opacity: float) -> str:
    """Set stroke opacity on layer groups for semi-transparent vector overlay."""
    return svg_content.replace(
        'style="display:inline"',
        f'style="display:inline;opacity:{opacity}"',
    )


def embed_background(svg_content: str, image_path: str) -> str:
    """Embed a raster image as the SVG background layer."""
    img_data = Path(image_path).read_bytes()
    suffix = Path(image_path).suffix.lower()
    mime = "image/png" if suffix == ".png" else "image/jpeg"
    b64 = base64.b64encode(img_data).decode()

    vb_match = re.search(r'viewBox="([^"]*)"', svg_content)
    if not vb_match:
        return svg_content

    parts = vb_match.group(1).split()
    if len(parts) != 4:
        return svg_content

    vb_x, vb_y, vb_w, vb_h = parts

    img_element = (
        f'  <image x="{vb_x}" y="{vb_y}" width="{vb_w}" height="{vb_h}" '
        f'href="data:{mime};base64,{b64}" '
        f'preserveAspectRatio="none" />\n'
    )

    for marker in ["<defs/>", "</defs>"]:
        if marker in svg_content:
            return svg_content.replace(marker, marker + "\n" + img_element, 1)

    return svg_content


def main() -> None:
    """CLI entry point."""
    args = sys.argv[1:]
    bg_image = None
    fill_opacity = 1.0
    glow = "--glow" in args
    if glow:
        args = [a for a in args if a != "--glow"]
    radial = "--radial" in args
    if radial:
        args = [a for a in args if a != "--radial"]

    if "--bg" in args:
        bg_idx = args.index("--bg")
        if bg_idx + 1 < len(args):
            bg_image = args[bg_idx + 1]
            args = args[:bg_idx] + args[bg_idx + 2 :]

    if "--fill-opacity" in args:
        op_idx = args.index("--fill-opacity")
        if op_idx + 1 < len(args):
            fill_opacity = float(args[op_idx + 1])
            args = args[:op_idx] + args[op_idx + 2 :]

    if len(args) < 2:
        print(
            "Usage: python -m vpype_fractal.svg_fill input.svg output.svg "
            "[--bg image.png] [--fill-opacity 0.5]"
        )
        sys.exit(1)

    with open(args[0]) as f:
        content = f.read()

    if bg_image:
        # Hybrid mode: raster background + subtle vector overlay
        result = _set_stroke_opacity(content, 0.2)
        result = embed_background(result, bg_image)
        mode = "hybrid"
    else:
        # Pure-vector mode: dark background rect + filled contours
        bg_color = _extract_darkest_color(content)
        if radial:
            result = add_radial_band_gradients(content)
        else:
            result = add_fills(content, fill_opacity=fill_opacity)
        result = _add_background_rect(result, bg_color)
        if glow:
            result = _inject_glow(result)
        mode_tag = "radial" if radial else f"opacity={fill_opacity}"
        mode = f"filled({mode_tag}{',glow' if glow else ''})"

    with open(args[1], "w") as f:
        f.write(result)

    print(f"[{mode}] {args[0]} → {args[1]}")


if __name__ == "__main__":
    main()
