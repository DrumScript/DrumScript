# DrumScript post-0.4.0 list

## Workflow fixes (one PR, `.github/workflows/`)

1. **`#363`** `pull_requests.yml` references `${{ matrix.python-version }}` but the `test-and-lint` job defines no `strategy.matrix`, so it resolves to an empty string and `setup-python` falls back to the runner default.

2. **`release.yml` toctree insert.** Line 144 uses `sed -i "/^\`\`\`/i <version>"` with no address restriction, so it inserts before every fence line. `index.md` has two. Would leave a stray version paragraph above the toctree.

3. **`release.yml` versions.json label.** Line 96 writes `"<version> (Alpha)"`. Every other entry carries `(Pypi)` as well.

4. **`release.yml` prerelease flag.** Line 205 is `prerelease: ${{ inputs.release_type != 'Stable' }}`, which you override by hand every release. Hardcode `false`, or make it a dispatch input.

5. **Node.js 20 deprecation** on `actions/checkout@v4`, `actions/setup-python@v5`, `astral-sh/setup-uv@v5`.

## Tidy-ups

6. **Restore `# __version__ = "0.1.6"`** in `drumscript/__init__.py`, removed during the manual bump. `release.yml` still has a comment explaining its sed avoids that line.

7. **Two changelogs in the release body.** `## Changes since v0.3.0` comes from your `git log` step, `## What's Changed` from `generate_release_notes: true`. Pick one.

## Dependency work

8. **`#364` drop Python 3.9.** Also lets `tests.yml` return to `ubuntu-latest`, lifts the numpy ceiling from 2.0, removes the `lameenc` downgrade, and clears the only version where the Demucs integration tests fail.

9. **`#365` fix the `load_audio` FileNotFoundError contract**, so `librosa<1` can be dropped. On 3.13 that also removes `audioread`, `standard-aifc`, `standard-chunk` and `standard-sunau`.

## Open PRs from @ashenthefox

10. **`#369`** docs, roadmap link fix plus a regression test. Awaiting rebase. Low risk.

11. **`#362`** Demucs module detection and skip guards. Still draft, awaiting rebase. You have said you will approve their fork CI runs.

## Carried over from before the release

12. **Stem output naming inconsistency.** `<song>_no_drums.wav` versus `<song>_only_drums.wav`, result keys `drums_stem` versus `drums`, and four different default output locations. The `gh issue create` command is drafted but I do not think you ever ran it.

13. **`CONTRIBUTING.md`** line 3 has a malformed comment, `<!--date_added:sun-10-may-2026->`, missing a dash. Line ~48 has a stray `w`.

14. **`docs/guide/troubleshooting.md`** has `date_added` but no `date_updated`.

15. **Warning suppression.** `warnings.filterwarnings` for the pydub `SyntaxWarning` and the libmpg123 ID3 message. The docs now say "a future release" rather than v0.4.0, and the roadmap still lists it.