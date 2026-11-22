# Announcements

<!--date_created: thurs-05-nov-2026-->
<!--date_edited: thurs-05-nov-2026-->

Project-wide notices that affect how you use or contribute to DrumScript.
Smaller, version-specific changes are in the [Release Notes](release_notes/index.md)
and the [Changelog](changelog.md).

---

## Git history rewritten (8 October 2026)

**If you cloned or forked DrumScript before 8 October 2026, you need to re-clone.
A normal `git pull` will no longer work.**

### What happened

The `.git` folder had grown very large. Old documentation build artefacts and
notebooks with audio baked into them had been committed over time, and git keeps
every version of every file forever, so the history carried all of it.

On 8 October 2026 the history was rewritten to strip those blobs:

```bash
git filter-repo --strip-blobs-bigger-than 10M
```

The cleaned history was then force-pushed to GitHub.

### What this means for you

| If you | Then |
|---|---|
| Installed via `pip install drumscript` | Nothing to do. PyPI is unaffected |
| Only read the docs site | Nothing to do. The docs site is unaffected |
| Cloned or forked **before** 8 Oct 2026 | **Re-clone.** Your local history no longer matches the remote |
| Cloned **after** 8 Oct 2026 | Nothing to do |

Re-cloning:

```bash
# Save any local work first
git bundle create ~/my-drumscript-work.bundle --all

# Then re-clone
cd ..
mv DrumScript DrumScript-old
git clone https://github.com/DrumScript/DrumScript.git
```

If you had a **fork**, GitHub forks do not re-sync after a history rewrite.
Delete the fork and fork again.

### Why it was not avoidable

Rewriting history is normally something to avoid, because it breaks everyone's
clones. It was done here because the alternative was worse: every new contributor
would have had to download the entire bloated history before they could make a
one-line change, and the problem compounds with every commit.

Doing it during the alpha, while the contributor base is small, was the least
disruptive moment available.

### Safety net

Nothing was discarded. The pre-rewrite state is preserved in a full repository
backup and on the `backup/before-filter-repo` branch.

### Published releases are unaffected

The PyPI package, all GitHub Releases, their tags, and the documentation site
were untouched by the rewrite.

---

## The alpha is ongoing

DrumScript has been in public alpha since 1 June 2026 and will stay there until
transcription accuracy and score generation are good enough for a beta.

Contributions, bug reports and submitted transcription results are all welcome.
See the [contributor guidance](development/contributor_guidance.md), or open an
issue using one of the [issue forms](https://github.com/DrumScript/DrumScript/issues/new/choose).

---

<!--END-->
