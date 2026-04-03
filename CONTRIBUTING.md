# Contributing to vpype-fractal

## Development Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

If you want to exercise pen set workflows locally, install `vpype-penset` in the same
environment:

```bash
pip install vpype-penset
```

## Running Checks

These match what CI runs:

```bash
ruff check src tests
pytest
python -m build
```

## Guidelines

- All geometry logic belongs in `engines/`, not in `commands/`. Commands should be thin CLI wrappers.
- Keep CLI changes reflected in the README and docs pages.
- Add tests for new commands, presets, or edge cases.
- Preserve deterministic behavior for seeded generators.
- Prefer backward-compatible command changes unless a version bump is intentional.
