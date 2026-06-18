# benchmarks/

Evaluation entrypoints that score the **existing** DrumScript classifier
against a dataset's ground truth and report metrics.

Out of scope: training, dataset acquisition, and manifest preparation.

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

Only IDMT-SMT-Drums is currently verified to run end-to-end.

### IDMT-SMT-Drums V2

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

  Optional flags:

  ```bash
  uv run --extra dev python benchmarks/run.py idmt --root … --subset RealDrum
  uv run --extra dev python benchmarks/run.py idmt --root … --limit 5
  ```

  Results archive to `outputs/benchmarks/idmt/` (untracked).

## Planned dataset coverage

IDMT is the first end-to-end benchmark because its three-class setup matches the
current core classifier and keeps the initial `mir_eval` pipeline easy to audit.
Future benchmark adapters should add broader automatic drum transcription
datasets such as ENST-Drums and MDB-Drums so DrumScript can evaluate full-kit
classes including toms, crash, ride, and other cymbal types. Those adapters will
also expand each dataset's code-to-DrumScript mapping beyond the current
`KD`/`SD`/`HH` scope.
