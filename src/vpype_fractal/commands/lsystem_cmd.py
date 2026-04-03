"""Generic L-system command for custom fractal definitions."""

import click
import vpype as vp
import vpype_cli

from vpype_fractal.engines import expand, turtle_to_lines

from ._shared import scale_to_size


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
    "--axiom",
    type=str,
    required=True,
    help="Starting axiom string (e.g., 'F--F--F').",
)
@click.option(
    "--rule",
    "rules",
    type=str,
    multiple=True,
    required=True,
    help="Replacement rule in 'X=replacement' format. Can be specified multiple times.",
)
@click.option(
    "--angle",
    type=float,
    required=True,
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
    default=0.0,
    help="Initial turtle heading in degrees (0 = right, 90 = up).",
)
@vpype_cli.generator
def lsystem(
    axiom: str,
    rules: tuple[str, ...],
    angle: float,
    depth: int,
    size: float,
    heading: float,
) -> vp.LineCollection:
    """Generate a custom L-system fractal.

    Example: vpype lsystem --axiom "F--F--F" --rule "F=F+F--F+F" --angle 60 -d 4 show
    """
    rule_dict = dict(parse_rule(r) for r in rules)
    instructions = expand(axiom, rule_dict, depth)
    lc = turtle_to_lines(instructions, angle=angle, step=1.0, heading=heading)
    return scale_to_size(lc, size)


lsystem.help_group = "Fractals"  # type: ignore[attr-defined]
