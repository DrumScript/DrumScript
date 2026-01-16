# Installation

## Prerequisites
* **Python:** 3.9 or higher
* **System Tools:** `FFmpeg` (for audio)

```bash
uv pip install drumscript
```

```bash
# Install dependencies
uv sync --all-groups
```

**Dependencies**

`DrumScript` manages dependencies using `uv` and `pyproject.toml`. A full list of project- and optional dependencies can be found in the **[`pyproject.toml`](https://github.com/DrumScript/DrumScript/blob/main/pyproject.toml)**.

> For installation of `uv` go to **[the official `uv` website](https://docs.astral.sh/uv/getting-started/installation/)**.
> 
> Alternatively, users familiar with **[`Homebrew`](https://docs.brew.sh/Installation)** can also use the command `brew install uv`
>

`DrumScript` does not use a [`requirements.txt`], or a [`requirements.in`] file. **All dependencies** are declared in the **[`pyproject.toml`](https://github.com/DrumScript/DrumScript/blob/main/pyproject.toml)**.

> If you are contributing to `DrumScript` please check the **[Contributor Guidance](https://github.com/DrumScript/DrumScript/blob/main/docs/development/contributor_guidance.md)** for more help on how to install the package in `editable` mode and the `[dev]` dependency group.


## Standard Installation
The easiest way to install DrumScript is via pip:


    uv pip install drumscript

## Installing External Dependencies

**DrumScript requires `FFmpeg` for audio processing**

### macOS Installation of `FFmpeg`

The standard way to install FFmpeg on macOS is using **Homebrew**, which automatically sets up the system path for you.

1.  Open your **Terminal**.
2.  Run the following command:
    ```bash
    brew install ffmpeg
    ```
3.  *Note: If you do not have Homebrew installed, visit [brew.sh](https://brew.sh) to install it first.*

**Windows:**
[Download FFmpeg here](https://ffmpeg.org) and add it to your PATH.


### Windows Installation of `FFmpeg`

1.  **Download:** Visit the [official `FFmpeg` website](https://ffmpeg.org/download.html) (hover over the Windows logo and select a build link, like **gyan.dev**). Download the "full" or "essentials" build.
2.  **Extract:** Unzip the downloaded folder and move it to a simple location, like `C:\ffmpeg`.
3.  **Add to Path:**
    * Press the **Windows Key**, type **"Edit the system environment variables"**, and hit Enter.
    * Click the **Environment Variables...** button.
    * Under **System variables** (the bottom box), find the variable named **Path** and click **Edit**.
    * Click **New** and paste the path to the `bin` folder inside your`FFmpeg` folder (e.g., `C:\ffmpeg\bin`).
    * Click **OK** on all open windows to save.

### Verify Installation of `FFmpeg`

To confirm `FFmpeg` is correctly added to your system path, open a new Terminal (or Command Prompt for Windows users) and run:

```bash
ffmpeg -version
```