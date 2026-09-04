---
name: bug_report.md
about: Something is broken or behaving unexpectedly
title: "[BUG]:"
labels: bug
assignees: drumscript-admin
type: Bug

---

name: Bug report
description: Something is broken or behaving unexpectedly
title: "[BUG] "
labels: [bug]
body:
  - type: textarea
    id: bug-description
    attributes:
      label: Describe the bug
      description: A clear description of what is broken and what you expected to happen instead.
    validations:
      required: true
  - type: textarea
    id: reproduction-steps
    attributes:
      label: Steps to reproduce
      description: Minimal code that reproduces the problem and the steps to see the error.
      value: |
        ```python
        import drumscript as ds
        ds.transcribe("my_file.wav")
        ```
        1. Step one
        2. Step two
        3. See error
    validations:
      required: true
  - type: textarea
    id: expected-behaviour
    attributes:
      label: Expected behaviour
      description: What you expected to happen.
    validations:
      required: true
  - type: textarea
    id: actual-behaviour
    attributes:
      label: Actual behaviour
      description: What actually happened. Include the full error message and stack trace if there is one.
    validations:
      required: true
  - type: textarea
    id: environment
    attributes:
      label: Environment
      description: Run `uv pip list | grep -E "drumscript|torch|librosa|demucs|numpy|soundfile"` and paste the output. Please include OS and Python version.
    validations:
      required: true
  - type: textarea
    id: audio-details
    attributes:
      label: Audio file details (if relevant)
      description: Format, sample rate, duration, input type.
  - type: textarea
    id: context
    attributes:
      label: Additional context
      description: Any other information that might help — screenshots, links, related issues.
