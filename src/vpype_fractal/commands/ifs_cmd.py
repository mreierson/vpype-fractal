"""Generic IFS (Iterated Function System) command."""

import click
import vpype as vp
import vpype_cli

from vpype_fractal.engines.ifs import IFS_PRESETS, AffineTransform, ifs_to_lines

from ._shared import scale_to_size


def _parse_transform(s: str) -> AffineTransform:
    """Parse 'a,b,c,d,e,f,weight' into an AffineTransform."""
    parts = [float(x.strip()) for x in s.split(",")]
    if len(parts) != 7:
        raise click.BadParameter(
            f"Transform must have 7 comma-separated values (a,b,c,d,e,f,weight), got {len(parts)}"
        )
    return AffineTransform(*parts)


@click.command()
@click.option(
    "--preset",
    type=click.Choice(sorted(IFS_PRESETS.keys())),
    default=None,
    help="Named IFS preset.",
)
@click.option(
    "--transform",
    "transforms_raw",
    type=str,
    multiple=True,
    help="Custom transform as 'a,b,c,d,e,f,weight'. Can be repeated.",
)
@click.option(
    "-s",
    "--size",
    type=vpype_cli.LengthType(),
    default="100mm",
    help="Overall size.",
)
@click.option(
    "-p",
    "--points",
    type=click.IntRange(min=100),
    default=50000,
    help="Number of points to generate.",
)
@click.option(
    "--segment-length",
    type=click.IntRange(min=2),
    default=500,
    help="Maximum points per path segment.",
)
@click.option(
    "--seed",
    type=int,
    default=None,
    help="Random seed for reproducibility.",
)
@vpype_cli.generator
def ifs(
    preset: str | None,
    transforms_raw: tuple[str, ...],
    size: float,
    points: int,
    segment_length: int,
    seed: int | None,
) -> vp.LineCollection:
    """Generate an IFS fractal using the chaos game algorithm.

    Use --preset for a named fractal, or define custom transforms with
    --transform (repeatable).

    \b
    Available presets: fern, sierpinski-ifs, maple, crystal

    \b
    Custom transform format: a,b,c,d,e,f,weight
      Maps (x,y) → (ax+by+e, cx+dy+f) with given probability weight.

    \b
    Examples:
        vpype ifs --preset fern show
        vpype ifs --preset maple -p 30000 show
        vpype ifs --transform "0.5,0,0,0.5,0,0,1" \\
                  --transform "0.5,0,0,0.5,0.5,0,1" \\
                  --transform "0.5,0,0,0.5,0.25,0.433,1" show
    """
    if preset and transforms_raw:
        raise click.UsageError("Use either --preset or --transform, not both.")
    if not preset and not transforms_raw:
        raise click.UsageError(
            "Provide --preset <name> or one or more --transform values. "
            f"Presets: {', '.join(sorted(IFS_PRESETS.keys()))}"
        )

    if preset:
        transforms = IFS_PRESETS[preset].transforms
    else:
        transforms = [_parse_transform(t) for t in transforms_raw]

    lc = ifs_to_lines(transforms, points, seed=seed, segment_length=segment_length)
    return scale_to_size(lc, size)


ifs.help_group = "Fractals"  # type: ignore[attr-defined]
