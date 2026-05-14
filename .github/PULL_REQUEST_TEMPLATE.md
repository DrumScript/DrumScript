# `DrumScript` PULL REQUEST TEMPLATE

## Description
What does this PR do? Why is it needed?
Link to the related issue if there is one: Closes #___

## Type of change
- [ ] Bug fix (non-breaking change that fixes an issue)
- [ ] New feature (non-breaking change that adds functionality)
- [ ] Breaking change (fix or feature that changes existing behaviour)
- [ ] Documentation / comments only
- [ ] Build / CI / dependency change
- [ ] Refactor (no behaviour change)

## How has this been tested?

Describe the tests you ran or added. Include the pytest command you used.

```bash
pytest tests/unit/test_...
```

## Checklist

- [ ] All tests pass locally: `pytest -m "not slow"`
- [ ] Code is formatted: `uv run ruff format .`
- [ ] Linter is clean: `uv run ruff check .`
- [ ] I have added or updated tests to cover my changes (where applicable).
- [ ] I have added or updated docstrings for any changed public functions.
- [ ] I have updated `CHANGELOG.md` under `[Unreleased]`.
- [ ] No `.ipynb` files are included in this PR.

## Screenshots / output (if relevant)

Paste generated PDF previews, terminal output, or other evidence that the
change works as described.