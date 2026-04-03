"""Clifford strange attractor command."""

import click
import vpype as vp
import vpype_cli

from vpype_fractal.engines.attractor import ATTRACTOR_PRESETS, run_clifford

from ._shared import generate_attractor_layers

_CLIFFORD_PRESETS = {k: v for k, v in ATTRACTOR_PRESETS.items() if v.kind == "clifford"}


@click.command()
@click.option(
    "--preset",
    type=click.Choice(sorted(_CLIFFORD_PRESETS.keys())),
    default=None,
    help="Named parameter preset.",
)
@click.option("-a", type=float, default=None, help="Parameter a (default -1.4).")
@click.option("-b", type=float, default=None, help="Parameter b (default 1.6).")
@click.option("-c", type=float, default=None, help="Parameter c (default 1.0).")
@click.option("-d", type=float, default=None, help="Parameter d (default 0.7).")
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
def clifford(
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
    """Generate a Clifford strange attractor.

    x_{n+1} = sin(a*y) + c*cos(a*x)
    y_{n+1} = sin(b*x) + d*cos(b*y)

    Use --preset for a named parameter set, or -a/-b/-c/-d for custom
    values. Use -n to split into layers for color gradients:

    \b
      vpype penset warm clifford --preset ribbon -n 6 colorize write out.svg
      vpype clifford -a -1.4 -b 1.6 -c 1.0 -d 0.7 show

    \b
    Presets: butterfly (default), ribbon, swirl
    """
    if preset:
        p = _CLIFFORD_PRESETS[preset].params
        a = a if a is not None else p["a"]
        b = b if b is not None else p["b"]
        c = c if c is not None else p["c"]
        d = d if d is not None else p["d"]
    else:
        a = a if a is not None else -1.4
        b = b if b is not None else 1.6
        c = c if c is not None else 1.0
        d = d if d is not None else 0.7

    raw = run_clifford(a, b, c, d, points, seed=seed)
    return generate_attractor_layers(doc, raw, layers, size, smooth=10)


clifford.help_group = "Fractals"  # type: ignore[attr-defined]
