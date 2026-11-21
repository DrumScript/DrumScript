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

Describe the tests you ran or added, and include the commands you used.

```bash
pytest tests/unit/test_...
```

* **Python version and OS:**
* **Anything you could not run, and why:**

Saying plainly that you could not run something is more useful than leaving it
unsaid, and it is never held against you.

## Checklist

- [ ] Fast tests pass locally: `pytest -m "not slow"`
- [ ] **If this touches Demucs, audio loading or stem splitting:** the full suite passes
  locally with a plain `pytest`, no marker filter. CI does not run these, so if you have
  not run them, nobody has.
- [ ] Code is formatted: `uv run ruff format .`
- [ ] Linter is clean: `uv run ruff check .`
- [ ] I have added or updated tests to cover my changes (where applicable).
- [ ] I have added or updated docstrings for any changed public functions.
- [ ] I have updated `CHANGELOG.md` under `[Unreleased]` for user-facing code, dependency, or build changes (not needed for docs/tests-only changes).
- [ ] No `.ipynb` files are included in this PR.

## Screenshots / output (if relevant)

Paste generated PDF previews, terminal output, or other evidence that the
change works as described.
