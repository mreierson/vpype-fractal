"""Generic L-system command for custom fractal definitions."""

import click
import vpype as vp
import vpype_cli

from vpype_fractal.engines import expand, turtle_to_lines
from vpype_fractal.presets import PRESETS

from ._shared import finalize_fractal, fractal_options, scale_to_size

# Preset names available via --preset
_PRESET_NAMES = sorted(PRESETS.keys())


def parse_rule(rule_str: str) -> tuple[str, str]:
    """Parse a rule string like 'F=F+F--F+F' into (key, value)."""
    if "=" not in rule_str:
        raise click.BadParameter(f"Rule must be in 'X=replacement' format, got: {rule_str}")
    key, value = rule_str.split("=", 1)
    if len(key) != 1:
        raise click.BadParameter(f"Rule key must be a single character, got: {key}")
    return key, value


@click.command()
@click.option(
    "--preset",
    type=click.Choice(_PRESET_NAMES, case_sensitive=False),
    default=None,
    help="Named preset (overrides --axiom/--rule/--angle).",
)
@click.option(
    "--axiom",
    type=str,
    default=None,
    help="Starting axiom string (e.g., 'F--F--F').",
)
@click.option(
    "--rule",
    "rules",
    type=str,
    multiple=True,
    help="Replacement rule in 'X=replacement' format. Can be specified multiple times.",
)
@click.option(
    "--angle",
    type=float,
    default=None,
    help="Turn angle in degrees.",
)
@click.option(
    "-d",
    "--depth",
    type=click.IntRange(min=0, max=12),
    default=4,
    help="Recursion depth.",
)
@click.option(
    "-s",
    "--size",
    type=vpype_cli.LengthType(),
    default="100mm",
    help="Overall size.",
)
@click.option(
    "--heading",
    type=float,
    default=None,
    help="Initial turtle heading in degrees (0 = right, 90 = up).",
)
@fractal_options
@vpype_cli.global_processor
def lsystem(
    doc: vp.Document,
    preset: str | None,
    axiom: str | None,
    rules: tuple[str, ...],
    angle: float | None,
    depth: int,
    size: float,
    heading: float | None,
    target_layer: int | None,
    raster: bool,
) -> vp.Document:
    """Generate a custom L-system fractal.

    Use --preset for a named L-system, or provide --axiom/--rule/--angle for custom rules.

    \b
    Examples:
      vpype lsystem --preset bush -d 4 show
      vpype lsystem --axiom "F--F--F" --rule "F=F+F--F+F" --angle 60 -d 4 show
    """
    if preset:
        defn = PRESETS[preset]
        axiom = axiom or defn.axiom
        rule_dict = dict(defn.rules) if not rules else dict(parse_rule(r) for r in rules)
        angle = angle if angle is not None else defn.angle
        heading = heading if heading is not None else defn.heading
    else:
        if not axiom or not rules or angle is None:
            raise click.UsageError(
                "Provide --preset <name>, or all of --axiom, --rule, and --angle."
            )
        rule_dict = dict(parse_rule(r) for r in rules)
        heading = heading if heading is not None else 0.0

    instructions = expand(axiom, rule_dict, depth)
    lc = turtle_to_lines(instructions, angle=angle, step=1.0, heading=heading)
    lc = scale_to_size(lc, size)
    return finalize_fractal(doc, lc, target_layer=target_layer, raster=raster)


lsystem.help_group = "Fractals"  # type: ignore[attr-defined]
