# Troubleshooting

<!--date_added:mon-07-september-2026-->

We endeavour to make the DrumScript package as warning-free and seemless to use as possible. 

This page lists known warnings and errors from **packages that DrumScript depends on**, which you may encounter. The list exists to differentiate between DrumScript issues and dep-related issues outside of our control. Items are grouped by whether they originate from DrumScript itself or from a third-party dependency.

> **See [CHANGELOG.md](../../CHANGELOG.md)** list future or ongoing fixes/resolutions for these dependency-related issues

- [Known dependency issues/warnings](#known-dependency-warnings)
- [DrumScript warnings](#drumscript-warnings)
- [How to submit an issue](#)


---

## Known dependency warnings

These warnings come from libraries that DrumScript depends on. They do **not** affect DrumScript's output or accuracy and can be safely ignored.

|Error|Log|Source|Impact|Fix|
|-|-|-|-|-|
|`libmpg123` -- ID3 comment warning|`src/libmpg123/id3.c:process_comment():587] error: No comment text / valid description`?|Loading `.wav` or `.mp3` files that contain ID3 metadata tags with an empty or malformed comment field. Common with files converted from MP3, or exported from certain DAWs.|None. Audio data is loaded correctly.|None required. The message is cosmetic. Add warning suppression in DrumScript v0.2.1+|
| `pydub` -- SyntaxWarning on import|`SyntaxWarning: invalid escape sequence`|On first import of `pydub`, particularly on Python 3.12+. The warning comes from unescaped backslashes in `pydub`'s source code.|`pydub` (v0.25.1). This is an [upstream issue](https://github.com/jiaaro/pydub/issues) in the `pydub` package itself. None. All `pydub` functionality (MP3 export, stem mixing) works correctly.|DrumScript will add warning suppression in v0.2.1+ ie `warnings.filterwarnings` in `main.py`. If you see it in a notebook or standalone script, you can suppress it manually with `warnings.filterwarnings("ignore", category=SyntaxWarning, module="pydub")`|
|`audioread` / `aifc` / `audioop` / `sunau` -- DeprecationWarnings|`DeprecationWarning: 'aifc' is deprecated`; `DeprecationWarning: 'audioop' is deprecated`; `DeprecationWarning: 'sunau' is deprecated` |On Python 3.12+ when `librosa` loads audio via `audioread`. These standard library modules were deprecated in Python 3.11 and removed in Python 3.13. `audioread` (used by `librosa`).|None on Python 3.9--3.12. On Python 3.13+, `audioread` may fail entirely (this is tracked separately under the numpy 2.x / Python 3.13 migration).|DrumScript's `pyproject.toml` suppresses these warnings in pytest.|
|-|-|-|-|-|


---

## DrumScript warnings

_No known DrumScript-specific warnings at this time. This section will be updated as issues are identified._

---

## How to submit an issue

If you identify a dependency issue with DrumScript please [Raise an Issue](https://github.com/DrumScript/DrumScript/issues/new/choose)* or email: *hello.drumscript@gmail.com*

  <!--^*^*requires a GitHub account*-->

---

<!--END-->