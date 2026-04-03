"""De Jong strange attractor command."""

import click
import vpype as vp
import vpype_cli

from vpype_fractal.engines.attractor import ATTRACTOR_PRESETS, run_dejong

from ._shared import generate_attractor_layers

_DEJONG_PRESETS = {k: v for k, v in ATTRACTOR_PRESETS.items() if v.kind == "dejong"}


@click.command()
@click.option(
    "--preset",
    type=click.Choice(sorted(_DEJONG_PRESETS.keys())),
    default=None,
    help="Named parameter preset.",
)
@click.option("-a", type=float, default=None, help="Parameter a (default 1.4).")
@click.option("-b", type=float, default=None, help="Parameter b (default -2.3).")
@click.option("-c", type=float, default=None, help="Parameter c (default 2.4).")
@click.option("-d", type=float, default=None, help="Parameter d (default -2.1).")
@click.option("-s", "--size", type=vpype_cli.LengthType(), default="100mm", help="Overall size.")
@click.option(
    "-p",
    "--points",
    type=click.IntRange(min=100),
    default=3000,
    help="Number of iterations (more = denser overlapping strokes).",
)
@click.option(
    "-n",
    "--layers",
    type=click.IntRange(min=1),
    default=1,
    help="Split trajectory into N layers for color gradients.",
)
@click.option("--seed", type=int, default=None, help="Random seed for reproducibility.")
@vpype_cli.global_processor
def dejong(
    doc: vp.Document,
    preset: str | None,
    a: float | None,
    b: float | None,
    c: float | None,
    d: float | None,
    size: float,
    points: int,
    layers: int,
    seed: int | None,
) -> vp.Document:
    """Generate a De Jong strange attractor.

    x_{n+1} = sin(a*y) - cos(b*x)
    y_{n+1} = sin(c*x) - cos(d*y)

    Use --preset for a named parameter set, or -a/-b/-c/-d for custom
    values. Use -n to split into layers for color gradients:

    \b
      vpype penset cool dejong --preset wings -n 6 colorize write out.svg

    \b
    Presets: orbit (default), tangle, wings
    """
    if preset:
        p = _DEJONG_PRESETS[preset].params
        a = a if a is not None else p["a"]
        b = b if b is not None else p["b"]
        c = c if c is not None else p["c"]
        d = d if d is not None else p["d"]
    else:
        a = a if a is not None else 1.4
        b = b if b is not None else -2.3
        c = c if c is not None else 2.4
        d = d if d is not None else -2.1

    raw = run_dejong(a, b, c, d, points, seed=seed)
    return generate_attractor_layers(doc, raw, layers, size, smooth=10)


dejong.help_group = "Fractals"  # type: ignore[attr-defined]
