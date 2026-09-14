# Benchmarks

<!--date_updated:mon-14-september-2026-->

Evaluation entrypoints that score the **existing** DrumScript classifier
against a dataset's ground truth and report metrics.

Out of scope: training, dataset acquisition, and manifest preparation.

- **[Data](#data)**
- **[Conventions](#conventions)**
- **[Verified Benchmarks](#verified-benchmarks)**
  - **[IDMT-SMT-DRUMS-V2](#idmt-smt-drums-v2)**
  - **[MDBDrums-master](#idmt-smt-drums-v2)**
- **[Planned Dataset Coverage](#planned-dataset-coverage)**
  - **[How to Add/Update a New/an Existing Dataset](#how-to-addupdate-a-newan-existing-dataset)**


---
## Data
*[(back)](#benchmarks)*

```text
./benchmarks
├── README.md
├── datasets  # Users must first copy the dataset locally. Data must never be committed to git.
│   ├── ENST-drums-public
│   ├── IDMT-SMT-DRUMS-V2
│   └── MDBDrums-master
├── run.py
└── tree_benchmarks.txt
```

1. All datasets belong in the `benchmarks/datasets` folder.
2. Above tree shows indicative structure
3. Users **must first** copy the dataset locally: see below^1^ for data sources^2^
4. Raw data **must never** be pushed to remote, ie committed. Ensure the path `benchmarks/datasets/**` is added to `.gitignore`

<details/>
<summary/> <b/>notes</b></summary>

> ^1^ *data sources are true at time of writing.*
*Please submit an issue if you believe a link to be incorrect*

> ^2^ *the `zenodo` website is temperamental; try again during working hours,*
 *...ie Monday-Friday EST/GMT if you are struggling to get a connection, or get `401 error`*

</details>

---

## Conventions


- One entrypoint script: `run.py`. It dispatches on the dataset subcommand to
  an adapter under `drumscript/datasets/<name>.py`. Adding a new benchmark
  means adding an adapter module that exposes
  `DATASET_NAME` / `INSTRUMENT_CODES` / `CODE_TO_DRUMSCRIPT` /
  `add_cli_args(parser)` / `iter_items(args)`, then registering it in
  `ADAPTERS` in `run.py`.
- Scripts only read data and the production classifier; they never mutate the
  model.
- Outputs (metrics, prediction CSVs) go under `outputs/benchmarks/<dataset>/`
  and stay untracked.

## Verified benchmarks
*[(back)](#benchmarks)*

Only IDMT-SMT-Drums is currently verified to run end-to-end.

### IDMT-SMT-Drums V2

*[(back)](#benchmarks)*

- Source: <https://zenodo.org/record/7544164>
- Evaluation scope: the current IDMT benchmark covers the dataset's

  | IDMT code | DrumScript label(s) |
  | --- | --- |
  | `KD` | `kick` |
  | `SD` | `snare` |
  | `HH` | `hi_hat_closed`, `hi_hat_open` |

  This is intentional for the first verified benchmark: IDMT-SMT-DRUMS-V2's
  evaluation annotations focus on kick drum, snare drum, and hi-hat, which makes
  it a clean target for validating the core `mir_eval` scoring pipeline before
  expanding the benchmark surface.
- Download the V2 archive from Zenodo and extract it anywhere.
- Required layout after extraction (the path you pass to `--root` must be
  the directory that directly contains `audio/` and `annotation_xml/`):

  ```
  IDMT-SMT-DRUMS-V2/                 ← pass this path to --root
    audio/
      RealDrum01_00#MIX.wav
      WaveDrum01_00#MIX.wav
      TechnoDrum01_00#MIX.wav
      ...                            (one *.wav per take, naming = <subset>NN_MM#MIX.wav)
    annotation_xml/                  ← labels this benchmark reads
      RealDrum01_00#MIX.xml
      ...                            (one *.xml per *.wav, same stem)
    annotation_svl/                  ← optional, Sonic Visualiser; not required to run
  ```

  Notes:
  - `audio/` and `annotation_xml/` are mandatory. `annotation_svl/` is kept
    only for parity with the upstream release.
  - Stem matching is exact: each `audio/<name>.wav` must have
    `annotation_xml/<name>.xml`.
  - Subset names (`RealDrum`, `WaveDrum`, `TechnoDrum`) are the filename
    prefix; `--subset` filters on this prefix.

- Run:

  <!-->```bash
  uv run --extra dev python benchmarks/run.py idmt \
    --root /path/to/IDMT-SMT-DRUMS-V2
  ```-->

  ```bash
  uv run --extra dev python benchmarks/run.py idmt \
    --root benchmarks/datasets/IDMT-SMT-DRUMS-V2
  ```

  Optional flags:

  ```bash
  uv run --extra dev python benchmarks/run.py idmt --root <path_to_benchmarking_data> --subset RealDrum
  # uv run --extra dev python benchmarks/run.py idmt --root <path_to_benchmarking_data> -limit 5
  uv run --extra dev python benchmarks/run.py --limit 5 idmt --root <path_to_benchmarking_data>
  ```

  Results archive to `outputs/benchmarks/idmt/` (untracked).

## Planned dataset coverage
*[(back)](#benchmarks)*

IDMT is the first end-to-end benchmark because its three-class setup matches the
current core classifier and keeps the initial `mir_eval` pipeline easy to audit.
Future benchmark adapters should add broader automatic drum transcription
datasets such as ENST-Drums and MDB-Drums so DrumScript can evaluate full-kit
classes including toms, crash, ride, and other cymbal types. Those adapters will
also expand each dataset's code-to-DrumScript mapping beyond the current
`KD`/`SD`/`HH` scope.

### How to Add/Update a New/an Existing Dataset
*[(back)](#benchmarks)*

1. It is advisable to create raise a [Pull Request](https://github.com/DrumScript/DrumScript/pulls) for new benchmarks; it is advisable to create a branch on DrumScript repository rather than a fork. 
2. This allows the DrumScript maintainers and contributors to **isolate** specific pieces of work on public record; serving as both an internal log. It is not mandatory that your [Pull Request](https://github.com/DrumScript/DrumScript/pulls) **must always** result in a merge to main, or change in underlying codebase. 
4. Not all datasets have uniform mappings and/or drumkit part coverage. Therefore, `run.py` will need to be amended as required. 
5. Copy the template block provided below (commented out as a base guidance under **[Verified Benchmarks](#verified-benchmarks)** section)
6. It is advisable to create a branch on DrumScript repository rather than a fork. If creating a branch, please use [Conventional Commit](https://www.conventionalcommits.org/en/v1.0.0/) standards, ie `benchmark(scope):commit_message`.
7. Ensure documentation is updated. Please also upload benchmarking results to the PR or email hello.drumscript@gmail.com.

---

<!--TEMPLATE_BLOCK_FOR_NEW_DATASET-->
<!--### IDMT-SMT-Drums V2

- Source: <https://zenodo.org/record/7544164>
- Evaluation scope: the current IDMT benchmark covers the dataset's
  foundational instrument classes only:

  | IDMT code | DrumScript label(s) |
  | --- | --- |
  | `KD` | `kick` |
  | `SD` | `snare` |
  | `HH` | `hi_hat_closed`, `hi_hat_open` |

  This is intentional for the first verified benchmark: IDMT-SMT-DRUMS-V2's
  evaluation annotations focus on kick drum, snare drum, and hi-hat, which makes
  it a clean target for validating the core `mir_eval` scoring pipeline before
  expanding the benchmark surface.
- Download the V2 archive from Zenodo and extract it anywhere.
- Required layout after extraction (the path you pass to `--root` must be
  the directory that directly contains `audio/` and `annotation_xml/`):

  ```
  IDMT-SMT-DRUMS-V2/                 ← pass this path to --root
    audio/
      RealDrum01_00#MIX.wav
      WaveDrum01_00#MIX.wav
      TechnoDrum01_00#MIX.wav
      ...                            (one *.wav per take, naming = <subset>NN_MM#MIX.wav)
    annotation_xml/                  ← labels this benchmark reads
      RealDrum01_00#MIX.xml
      ...                            (one *.xml per *.wav, same stem)
    annotation_svl/                  ← optional, Sonic Visualiser; not required to run
  ```

  Notes:
  - `audio/` and `annotation_xml/` are mandatory. `annotation_svl/` is kept
    only for parity with the upstream release.
  - Stem matching is exact: each `audio/<name>.wav` must have
    `annotation_xml/<name>.xml`.
  - Subset names (`RealDrum`, `WaveDrum`, `TechnoDrum`) are the filename
    prefix; `--subset` filters on this prefix.

- Run:

  ```bash
  uv run --extra dev python benchmarks/run.py idmt \
    --root /path/to/IDMT-SMT-DRUMS-V2
  ```

  ```bash
  uv run --extra dev python benchmarks/run.py idmt \
    --root benchmarks/datasets/IDMT-SMT-DRUMS-V2
  ```

  Optional flags:

  ```bash
  uv run --extra dev python benchmarks/run.py idmt --root <path_to_benchmarking_data> --subset RealDrum
  # uv run --extra dev python benchmarks/run.py idmt --root <path_to_benchmarking_data> -limit 5
  uv run --extra dev python benchmarks/run.py --limit 5 idmt --root <path_to_benchmarking_data>
  ```

  Results archive to `outputs/benchmarks/idmt/` (untracked).
-->

---

<!--END-->