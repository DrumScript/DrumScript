# Benchmarks

<!--date_updated:sat-19-september-2026-->
<!--date_updated:weds-30september-2026-->

Evaluation entrypoints that score the **existing** DrumScript classifier
against a dataset's ground truth and report metrics.

Out of scope: training, dataset acquisition, and manifest preparation.

- **[Data](#data)**
- **[Conventions](#conventions)**
- **[DrumScript Mappings](#drumscript-labels)**
  * **[Excluded Drum Parts](#not-covered)** 
- **[Verified Benchmarks](#verified-benchmarks)**
  - **[IDMT-SMT-DRUMS-V2](#idmt-smt-drums-v2)**
  - **[MDBDrums-master](#mdb-drums)**
  - **[ENST-Drums](#enst-drums)** *(adapter added; first run pending)*
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

**NOTE**: care has been taken to ensure that the unzipped folder name(s) from source ENST, IDMT, MDB datasets matches that copied into `benchmarks/README.md`. However, to ensure smooth running, check that the `DATASET_NAME `in the adapter file (ie. `drumscript/datasets/*.py` for $[*:=`enst`, `idmt`,`mdb`]$ ) is *matching** whast it is in the [`benchmarks/datasets`](./../benchmarks/datasets/) folder. 

It's also recommended that you copy the downloaded `.zip` or `.tar.bz2` file **directly** into the [`benchmarks/datasets`](./../benchmarks/datasets/) folder and unzip there


> **Example**
```python
# drumscript/datasets/idmt.py
from drumscript.datasets.base import BenchmarkItem

logger = logging.getLogger(__name__)

DATASET_NAME = "idmt" # THIS LINE
``` 

> must match the folder name where the dataset has been stored locally; normally it's in [benchmarks/dataset/](./../benchmarks/datasets/)


```zsh

├── datasets  # Users must first copy the dataset locally. Data must never be committed to git.
│   ├── ENST-drums-public
│   ├── IDMT-SMT-DRUMS-V2
│   └── MDBDrums-master
```


1. All datasets belong in the `benchmarks/datasets` folder.
2. Above tree shows indicative structure
3. Users **must first** copy the dataset locally: see below^1^ for data sources^2^
4. Raw data **must never** be pushed to remote, ie committed. Ensure the path `benchmarks/datasets/**` is added to `.gitignore`

<details/>
<summary/> <b/>notes</b></summary>

^1^ *data sources are true at time of writing.*
*Please submit an issue if you believe a link to be incorrect*

^2^ *the `zenodo` website is temperamental; try again during working hours,*
 *...ie Monday-Friday EST/GMT if you are struggling to get a connection, or get `401 error`*

</details>

---

## Conventions
*[(back)](#benchmarks)*


<!--PREVIOUS -- KEEP FOR NOW -- CODE_TO_DRUMSCRIPT renamed to DRUMSCRIPT_DICT
- One entrypoint script: `run.py`. It dispatches on the dataset subcommand to
  an adapter under `drumscript/datasets/<name>.py`. Adding a new benchmark
  means adding an adapter module that exposes
  `DATASET_NAME` / `INSTRUMENT_CODES` / `CODE_TO_DRUMSCRIPT` /
  `add_cli_args(parser)` / `iter_items(args)`, then registering it in
  `ADAPTERS` in `run.py`.-->
- One entrypoint script: `run.py`. It dispatches on the dataset subcommand to
  an adapter under `drumscript/datasets/<name>.py`. Adding a new benchmark
  means adding an adapter module that exposes
  `DATASET_NAME` / `INSTRUMENT_CODES` / `DRUMSCRIPT_DICT` /
  `add_cli_args(parser)` / `iter_items(args)`, then registering it in
  `ADAPTERS` in `run.py`. `tests/unit/test_benchmarks_run.py` checks every
  registered adapter exposes all five.
- `DATASET_NAME` matches the dataset's native unzipped folder name under
  `benchmarks/datasets/` (e.g. `IDMT-SMT-DRUMS-V2`). It is also the `run.py`
  subcommand and the output folder name, so nothing needs renaming.
- Scripts only read data and the production classifier; they never mutate the
  model.
- Outputs (metrics, prediction CSVs) go under `outputs/benchmarks/<dataset>/`
  and stay untracked.


## DrumScript Labels
*[(back)](#benchmarks)*
DrumScript model currently covers **nine** parts of the drum: 

1. kick
2. snare
3. closed hi-hat
4. open hi-hat
5. high floor tom
6. low floor tom
7. mid floor tom
8. crash
9. ride

These are defined in [`constants.py`](../drumscript/notation_generator/constants.py) 
under `DRUM_NOTATION_MAPPING`

Because different datasets will have varying mappings to different drum parts we select
mappings based on **absolutes**. DrumScript's classification model is in development. 
It cannot cope with variations of things yet, such as below.

### Not Covered
*[(back)](#benchmarks)*

#### Snare Drum
* Snare drum: brush
* Snare drum: drag
* Snare drum: flam
* Snare drum: ghost note
* Snare drum: side stick
* Snare drum: no snare
* Snare drum: rim shot *(ENST)*
* Snare drum: brush sweep *(ENST)*

#### Hi-Hat

* Pedal hi-hat

#### Toms

* High-mid tom
* Tom hit on the rim *(ENST)*

#### Ride

* Ride cymbal: bell

#### Cymbals

* China cymbal
* Splash cymbal
* Other cymbals *(ENST)*

#### Other Percussion

* TMB: Tambourine
* Cowbell *(ENST)*
* Sticks hit together *(ENST)*

    


## Verified benchmarks
*[(back)](#benchmarks)*

Two datasets are currently verified to run end-to-end **with select mappings relevant to DrumScript**.
To ensure the mir_eval results are relevant, some of the labels in datasets have been excluded
If and when DrumScript expands its labels these mappings will be updated

1. **IDMT-SMT-Drums V2**
2. **MDB-Drums**

A third adapter, **ENST-Drums**, has been added but is **not yet verified** (first run pending).

### IDMT-SMT-Drums V2

*[(back)](#benchmarks)*

- Source: <https://zenodo.org/records/7544164>
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

Run:

  ```bash
  uv run --extra dev python benchmarks/run.py IDMT-SMT-DRUMS-V2 \
    --root benchmarks/datasets/IDMT-SMT-DRUMS-V2
  ```

  Optional flags:

  ```bash
  uv run --extra dev python benchmarks/run.py IDMT-SMT-DRUMS-V2 --root <path_to_benchmarking_data> --subset RealDrum
  uv run --extra dev python benchmarks/run.py --limit 5 IDMT-SMT-DRUMS-V2 --root <path_to_benchmarking_data>
  ```

  <!--Results archive to `outputs/benchmarks/idmt/` (untracked).-->
  Results archive to `outputs/benchmarks/IDMT-SMT-DRUMS-V2/` (untracked).

### MDB-Drums

*[(back)](#benchmarks)*

- Source: <https://github.com/CarlSouthall/MDBDrums>
- Evaluation scope: MDB-Drums is the first full-kit benchmark. It uses the
  dataset's **subclass** annotations, mapped onto DrumScript's instrument
  classes. The mapping principle is strict: a subclass maps to a DrumScript
  label **only** where a direct, unambiguous notation equivalent exists.
  Anything without a direct equivalent is **excluded** from evaluation (counted
  as neither a hit nor a false positive) rather than folded into a nearby class
  — DrumScript is a transcription engine, so china ≠ crash, splash ≠ crash,
  side-stick ≠ snare.

  <!--PREVIOUS MAPPING -- KEEP FOR NOW -- 
  | MDB subclass | DrumScript label |
  | --- | --- |
  | `KD` | `kick` |
  | `SD`, `SDG`, `SDB`, `SDF`, `SDD` | `snare` |
  | `CHH`, `PHH` | `hi_hat_closed` |
  | `OHH` | `hi_hat_open` |
  | `RDC`, `RDB` | `ride` |
  | `CRC` | `crash` |
  | `LFT` | `low_tom` |
  | `MHT` | `mid_tom` |
  | `HFT` | `high_tom` |-->

  <!--PREVIOUS MAPPING -- KEEP FOR NOW -- 

  **Excluded** (no direct DrumScript notation): `SDNS` (snares-off),
  `CHC` (china), `SPC` (splash), `SST` (side/cross-stick), `TMB` (tambourine),
  `HIT` (generic/ambiguous), `OT` (class-level "other"). Unmapped codes are
  skipped with a one-time warning, so a new/renamed label is surfaced rather
  than silently dropped.-->

  *possible overlap* 

<!-->> ?? try with both, withtout first?? and then review results with possible ones to see if results are better-->

| # | MDB Subclass | MDB Description | DrumScript Class |
| --- | --- | --- | --- |
| 1 | KD | Kick Drum | `kick` |
| 2 | SD,*ST* | Snare, *Snare stick* | `snare` |
| 3 | CHH | Closed Hi-Hat | `hi_hat_closed` |
| 4 | OHH | Open Hi-Hat | `hi_hat_open` |
| 5 | RDC | Ride | `ride` |
| 6 | CRC | Crash | `crash` |
| 7 | LFT | Low Floor | `low_tom` |
| 8 | HFT, *MHT* | High Floor Tom, *High-Mid Tom* | `mid_tom` | 
| 9 | HIT | High Tom | `high_tom` |

**Excluded Codes**

*possible overlap*

| MDB Subclass | MDB Description |
| --- | --- |
| SDB, SDD, SDF, SDG, SDNS, *SST* | Snare (ghost, flam, brush, *stick*) |
| PHH | Pedal Hi-Hat |
| RDB | Ride Bell |
| CHC, SPC | China / Splash|
| *MHT* | *High-Mid Tom* |
| TMB | Tambourine |
| OT | Other Percussion |



- Clone the repository and place it under `benchmarks/datasets/`.
- The benchmark evaluates the **`drum_only`** audio against the **`subclass`**
  annotations by default.
- Required layout (the path you pass to `--root` must be the directory that
  directly contains `audio/` and `annotations/`):

  ```
  MDBDrums-master/
    MDB Drums/                       ← pass this path to --root
      audio/
        drum_only/
          MusicDelta_Rock_Drum.wav
          ...                        (one *_Drum.wav per track)
        full_mix/                    ← optional; used only with --audio full_mix
      annotations/
        subclass/                    ← labels this benchmark reads
          MusicDelta_Rock_subclass.txt
          ...                        (one *_subclass.txt per track, same stem)
        class/                       ← coarse labels; not used
        beats/                       ← beat grid; not used
  ```

  Notes:
  - Annotation format is `<onset_seconds>\t<SUBCLASS_CODE>` per line; onset
    times are real seconds.
  - Stem matching is by track name: `audio/drum_only/<stem>_Drum.wav` pairs with
    `annotations/subclass/<stem>_subclass.txt`.
  - The `bucket` used in per-bucket summaries is the MedleyDB genre taken from
    the track name (e.g. `MusicDelta_Rock` → `Rock`).

Run:

  ```bash
  uv run --extra dev python benchmarks/run.py MDBDrums-master \
    --root "benchmarks/datasets/MDBDrums-master/MDB Drums"
  ```

  Optional flags:

  ```bash
  # transcribe the full mix instead of the isolated drum stem
  uv run --extra dev python benchmarks/run.py MDBDrums-master --root "benchmarks/datasets/MDBDrums-master/MDB Drums" --audio full_mix
  # process only the first N tracks (global flag, goes before the dataset name)
  uv run --extra dev python benchmarks/run.py --limit 1 MDBDrums-master --root "benchmarks/datasets/MDBDrums-master/MDB Drums"
  ```

  <!--Results archive to `outputs/benchmarks/mdb/` (untracked).-->
  Results archive to `outputs/benchmarks/MDBDrums-master/` (untracked).

  Note: MDB tracks are full songs and each is decomposed with HPSS onset
  detection, so a full 23-track run takes several minutes. Use `--limit 1`
  first to sanity-check before a full run.

### ENST-Drums

*[(back)](#benchmarks)*

> **Status:** adapter added on `benchmarks/enst-first-run`; first run pending.
> Move to the verified list above once a full run has been checked.

- Source: <!--TODO: add download/access link--> Paper: Gillet & Richard (2006),
  [ENST-Drums: an extensive audio-visual database for drum signals processing](https://archives.ismir.net/ismir2006/paper/000027.pdf), ISMIR.
- Evaluation scope: ENST-Drums is a full-kit benchmark with real acoustic kits
  played by three drummers. It follows the same strict principle as MDB: a label
  maps to a DrumScript notation **only** where a direct, unambiguous equivalent
  exists; everything else is **excluded** (counted as neither a hit nor a false
  positive).

<!--| # | ENST Label | ENST Description | DrumScript Class |
| --- | --- | --- | --- |
| 1 | bd | Bass drum | `kick` |
| 2 | sd | Snare drum | `snare` |
| 3 | chh | Closed hi-hat | `hi_hat_closed` |
| 4 | ohh | Open hi-hat | `hi_hat_open` |
| 5 | rc | Ride cymbal | `ride` |
| 6 | cr | Crash cymbal | `crash` |

**Pending decision** (currently unmapped; logged as a warning, not scored)

| ENST Label | ENST Description |
| --- | --- |
| lft | Lowest tom |
| lt | Low tom |
| lmt | Low-mid tom |
| mt | Mid tom |

**Excluded Codes**

| ENST Label | ENST Description |
| --- | --- |
| rs, cs | Rim shot, cross stick |
| sweep | Brush sweep |
| mtr, ltr | Mid / low tom hit on the rim |
| ch, spl, c | Chinese, splash, other cymbals |
| cb | Cowbell |
| sticks | Sticks hit together |-->

**Included ENST annotations (uses the 20-part segment of ENST)**
| Label | Instrument | Technique / Articulation Specified | DrumScript mapping |
| --- | --- | --- | --- |
| SD_cl | Snare Drum | Centre struck note (clean) | SD |
| RC_bl | Ride Cymbal | Bell strike (pure bell tone) | RD |
| TT_mid | Tom-Tom | Mid-pitched rack tom | MT |
| TT_low | Tom-Tom | Low-pitched rack or floor tom | LT |
| TT_floor | Tom-Tom | Main low floor tom | LT |
| TT_hi | Tom-Tom | High-pitched rack tom | HT |
| HH_op | Hi-Hat | Fully open ringing strike | HH-OP |
| HH_cl | Hi-Hat | Tightly closed strike with tip or shoulder | HH-CL |
| CR_lh | Crash Cymbal | Left-hand crash cymbal placement | CC |
| CR_rh | Crash Cymbal | Right-hand crash cymbal placement | CC |
| BD | Bass Drum | Standard kick pedal hit | BD |

**Excluded ENST annotations (uses the 20-part segment of ENST)**

| Label | Instrument | Technique / Articulation Specified | DrumScript mapping |
| --- | --- | --- | --- |
| RC_bw | Ride Cymbal | Bow strike (standard ping riding) | -- |
| SD_rs | Snare Drum | Rimshot (hitting head and rim together) | -- |
| SD_ss | Snare Drum | Side-stick / Cross-stick (clicking the rim) | -- |
| SD_roll | Snare Drum | Closed roll / buzz pattern | -- |
| HH_ho | Hi-Hat | Half-open "sloshy" strike | -- |
| HH_pd | Hi-Hat | Foot pedal close action (chick sound) | -- |
| SPL | Splash Cymbal | Accent splash cymbal hit | -- |
| CB | Cowbell | Accessory percussion hit | -- |
| BR_sw | Brushes | Brush sweep / sustained friction swirl | -- |

Please advise if any columns need adjusting or if further details on DrumScript mapping are required.


- Place the dataset under `benchmarks/datasets/`.
- The benchmark evaluates the **`wet_mix`** audio by default. The per-mic
  channels and `accompaniment/` are not used.
- Required layout (the path you pass to `--root` must be the directory that
  directly contains the `drummer_*` folders):

  ```
  ENST-drums-public/                 ← pass this path to --root
    drummer_1/
      annotation/                    ← labels this benchmark reads
        001_hits_snare-drum_sticks_x6.txt
        ...                          (one *.txt per take, same stem as the audio)
      audio/
        wet_mix/                     ← default
        dry_mix/                     ← optional; used only with --audio dry_mix
        kick/ snare/ hi-hat/ tom_1/ tom_2/ overhead_L/ overhead_R/ accompaniment/   ← not used
    drummer_2/                       (same layout)
    drummer_3/                       (same layout, plus tom_3/)
  ```

  Notes:
  - Annotation format is `<onset_seconds> <label>` per line; onset times are
    real seconds. Line endings are handled whatever their style.
  - A trailing instance number on a label (e.g. a second crash) identifies
    which physical drum or cymbal was hit, not a different class, so it is
    stripped before mapping.
  - Stem matching is exact, per drummer: `audio/<mix>/<name>.wav` pairs with
    `annotation/<name>.txt`.
  - Filenames repeat across drummers, so the `track` id is prefixed with the
    drummer (e.g. `drummer_1_001_hits_snare-drum_sticks_x6.wav`).
  - The `bucket` used in per-bucket summaries is the recording type, taken from
    the second token of the filename: `hits`, `phrase`, `solo` or `minus-one`.
    `--subset` filters on this.

Run:

  ```bash
  uv run --extra dev python benchmarks/run.py ENST-drums-public \
    --root benchmarks/datasets/ENST-drums-public
  ```

  Optional flags:

  ```bash
  # transcribe the dry mix instead of the wet mix
  uv run --extra dev python benchmarks/run.py ENST-drums-public --root benchmarks/datasets/ENST-drums-public --audio dry_mix
  # one recording type only
  uv run --extra dev python benchmarks/run.py ENST-drums-public --root benchmarks/datasets/ENST-drums-public --subset minus-one
  # process only the first N items (global flag, goes before the dataset name)
  uv run --extra dev python benchmarks/run.py --limit 5 ENST-drums-public --root benchmarks/datasets/ENST-drums-public
  ```

  <!--Results archive to `outputs/benchmarks/enst/` (untracked).-->
  Results archive to `outputs/benchmarks/ENST-drums-public/` (untracked).

  Diagnostics: `drumscript/utils/research/analyze_enst_dataset.py` gives
  per-class stage attribution and feature profiles, in the same format as the
  MDB diagnostics script.

## Planned dataset coverage
*[(back)](#benchmarks)*

IDMT was the first end-to-end benchmark because its three-class setup matches the
core classifier and keeps the initial `mir_eval` pipeline easy to audit.
MDB-Drums added the first full-kit coverage (toms, ride, crash, open/closed
hi-hat). <!--The next planned adapter is **ENST-Drums**, which adds real acoustic
kits and a wider articulation vocabulary.--> **ENST-Drums** has now been added
(first run pending), bringing real acoustic kits and a wider articulation
vocabulary. Each new adapter defines its own
code-to-DrumScript mapping, following the same strict "direct notation
equivalent or exclude" principle used for MDB.

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
<!--### <DATASET NAME>

- Source: <url>
- Evaluation scope: describe which of the dataset's labels are evaluated and
  the mapping onto DrumScript classes. State the mapping principle: a label maps
  to a DrumScript notation ONLY where a direct, unambiguous equivalent exists;
  everything else is EXCLUDED (never folded into a nearby class).

  | <dataset> code | DrumScript label(s) |
  | --- | --- |
  | ... | ... |

  Excluded (no direct DrumScript notation): ...

- Acquisition + placement under benchmarks/datasets/ (never committed).
- Required layout after extraction (the path passed to --root must directly
  contain the audio and annotation directories):

  ```
  <DATASET>/                         ← pass this path to --root
    audio/
      ...
    annotations/                     ← labels this benchmark reads
      ...
  ```

  Notes:
  - annotation format + units
  - stem-matching rule (audio ↔ annotation)
  - bucket/subset definition

- Run:

  ```bash
  uv run --extra dev python benchmarks/run.py <name> \
    --root benchmarks/datasets/<DATASET>
  ```

  Results archive to `outputs/benchmarks/<name>/` (untracked).
-->

---

<!--END-->