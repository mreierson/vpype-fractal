"""Lorenz strange attractor command."""

import click
import vpype as vp
import vpype_cli

from vpype_fractal.engines.attractor import ATTRACTOR_PRESETS, run_lorenz

from ._shared import generate_attractor_layers

_LORENZ_PRESETS = {k: v for k, v in ATTRACTOR_PRESETS.items() if v.kind == "lorenz"}


@click.command()
@click.option(
    "--preset",
    type=click.Choice(sorted(_LORENZ_PRESETS.keys())),
    default=None,
    help="Named parameter preset.",
)
@click.option("--sigma", type=float, default=None, help="Lorenz sigma (default 10.0).")
@click.option("--rho", type=float, default=None, help="Lorenz rho (default 28.0).")
@click.option("--beta", type=float, default=None, help="Lorenz beta (default 8/3).")
@click.option("--dt", type=float, default=None, help="Integration time step (default 0.005).")
@click.option("-s", "--size", type=vpype_cli.LengthType(), default="100mm", help="Overall size.")
@click.option(
    "-p",
    "--points",
    type=click.IntRange(min=100),
    default=50000,
    help="Number of points to generate.",
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
def lorenz(
    doc: vp.Document,
    preset: str | None,
    sigma: float | None,
    rho: float | None,
    beta: float | None,
    dt: float | None,
    size: float,
    points: int,
    layers: int,
    seed: int | None,
) -> vp.Document:
    """Generate a Lorenz strange attractor (XZ projection).

    The classic butterfly-shaped chaotic system, integrated with RK4 and
    projected onto the XZ plane for plotter output.

    \b
      vpype lorenz show                                            (classic)
      vpype lorenz --preset lorenz-tight show                      (tight orbit)
      vpype penset viridis lorenz -n 10 colorize write out.svg     (colored)
    """
    if preset:
        p = _LORENZ_PRESETS[preset].params
        sigma = sigma if sigma is not None else p["sigma"]
        rho = rho if rho is not None else p["rho"]
        beta = beta if beta is not None else p["beta"]
        dt = dt if dt is not None else p.get("dt", 0.005)
    else:
        sigma = sigma if sigma is not None else 10.0
        rho = rho if rho is not None else 28.0
        beta = beta if beta is not None else 8.0 / 3.0
        dt = dt if dt is not None else 0.005

    raw = run_lorenz(sigma, rho, beta, dt, points, seed=seed)
    return generate_attractor_layers(doc, raw, layers, size)


lorenz.help_group = "Fractals"  # type: ignore[attr-defined]
