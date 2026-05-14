# `DrumScript` Security Policy

<!--date_added:2026-05-10-->
<!--date_updated:2026-05-10-->

---

## Reporting a Vulnerability

**Do not open a public GitHub Issue for security vulnerabilities.**

Email **hello.drumscript@gmail.com** with:

- Description of the vulnerability and its potential impact.
- Steps to reproduce (or a minimal proof-of-concept).
- DrumScript version and Python version.

The development team is small. Please expect a response within 1 calendar month.
Alternatively, you can also raise a PR request with corrected fix, which will be addressed quicker as these are prioritised

## Scope

DrumScript is a local audio-processing library. It does **not** run a server or
**handle authentication**. The most likely concerns are malicious audio files
exploiting parsing bugs in dependencies, or path-traversal in file output.

---
<!--END-->