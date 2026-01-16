# Installation
<!--date_created:fri-16-jan-2026-->
<!--date_updated:fri-16-jan-2026-->
<!------->

> `DrumScript` manages dependencies using `uv` and `pyproject.toml`.

```bash
pip install drumscript
# or
uv pip install drumscript
```

```bash
# Install dependencies
uv sync

```

**Dependencies**

A full list of project- and optional dependencies can be found in the **[`pyproject.toml`](#pyproject.toml)**.

`DrumScript` does not use a [`requirements.txt`](#requirements.txt), or a [`requirements.in`](#requirements.in) file. **All dependencies** are declared in the **[`pyproject.toml`](#pyproject.toml)**.

## Installation

### Prerequisites
* **Python:** 3.9 or higher
* **System Tools:** FFmpeg (for audio), LilyPond (for sheet music)

### Standard Installation
The easiest way to install DrumScript is via pip:


    uv pip install drumscript


### Installing External Dependencies

DrumScript requires FFmpeg for audio processing.

**MacOS:**


```zsh
brew install ffmpeg lilypond
```

**Windows:**
[Download FFmpeg here](https://ffmpeg.org) and add it to your PATH.

<!------->
<!--END-->