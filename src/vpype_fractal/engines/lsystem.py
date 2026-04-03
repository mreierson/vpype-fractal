"""L-system string expansion engine."""

# Safety limit: 10 million characters (~10 MB). L-system strings grow
# exponentially, so even moderate depths with high branching factors can
# exhaust memory. This limit prevents accidental OOM.
_MAX_STRING_LENGTH = 10_000_000


def expand(axiom: str, rules: dict[str, str], iterations: int) -> str:
    """Expand an L-system axiom through the given number of iterations.

    Args:
        axiom: The starting string.
        rules: Mapping of characters to their replacement strings.
        iterations: Number of expansion iterations.

    Returns:
        The fully expanded instruction string.

    Raises:
        ValueError: If the expanded string exceeds the safety limit.
    """
    current = axiom
    for _ in range(iterations):
        current = "".join(rules.get(c, c) for c in current)
        if len(current) > _MAX_STRING_LENGTH:
            raise ValueError(
                f"L-system expansion exceeded {_MAX_STRING_LENGTH:,} characters. "
                "Reduce depth or simplify rules."
            )
    return current
