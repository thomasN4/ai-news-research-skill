# AGENTS.md

Shared state for two assistants: Grok has live X access and feeds verbatim, sourced material
*into* `digest.html`; Claude has no X access and a training cutoff well before these events, so
it reads the digest and reasons with it.

`README.md` has the layout and the rationale — read it before changing anything here. This file
covers only what bites.

## Start by cloning

```bash
git clone https://github.com/thomasN4/ai-news-research-skill.git
```

Don't enumerate the repo through the GitHub API to find your way around. Unauthenticated calls
are capped at 60/hour against your egress IP, which on a hosted sandbox is shared with everyone
else on that host, and `README.md` already contains the full tree. Reads need no token at all;
only writes do.

## What bumps what

| Change | bump `revision` | rebuild `dist/` |
| --- | --- | --- |
| `digest.html` content | yes | no |
| a `SKILL.md` or `github-sync.md` | no | yes |
| docs (`README`, `INSTALL`, this file) | no | no |

```bash
bash scripts/build-skills.sh   # only for the middle row
```

The Claude bundle is built as `.skill`, the Grok one as `.zip`. That is not cosmetic: the web
app only offers its "save skill" button for a `.skill` file, and Grok has no uploader at all.
If you hand a rebuilt bundle back in chat, hand back the `.skill`.

`revision` in `manifest.json` tracks digest content only. `coverage_end` moves only when new
dates are genuinely covered — a backfill *inside* the existing window bumps `revision` and
leaves `coverage_end` where it is.

The digest is deliberately not bundled into `dist/`; both skills fetch it live at runtime. That
is why a digest push never invalidates an installed bundle, and why editing a `SKILL.md` does.

## The Pages copy is for humans

GitHub Pages serves the repo root, so `digest.html` renders at
<https://thomasn4.github.io/ai-news-research-skill/>. Both skills still fetch the
`raw.githubusercontent.com` copy, which stays canonical. Don't retarget them at Pages: it is the
same file behind a second CDN cache, so a fresh push appears on `raw` first, and the skills'
`curl`-not-`web_fetch` instruction is written against the raw URL.

`index.html` (a meta-refresh to `digest.html`) and `.nojekyll` are hand-written, not generated.
Regenerating the digest never touches them, and `.nojekyll` needs to stay — without it Pages runs
a Jekyll build the digest has no use for.

## Concurrency is asymmetric

Grok pushes straight to `main` through the contents API, where the blob `sha` is the concurrency
guard. A 409 means the other agent pushed first: re-pull, re-apply, retry. Never work around a
409 by dropping the `sha` — that overwrites their work.

Claude works on a branch and merges a PR. **The `sha` guard does not protect a branch.** Check
`updated_by` and `updated_at` in the manifest before opening a branch and again before merging.
If Grok pushed in between, rebase — don't force.

The ordering rule (`digest.html` before `manifest.json`, so the manifest never advertises
coverage the digest lacks) governs direct pushes. A PR merge is atomic, so ordering is moot
there; what matters instead is that both files are in the same PR.

Full write procedure, including token handling: `skills/common/references/github-sync.md`.

## Card order within a month

Cards inside a `<section class="month">` read top to bottom as a chronology. Keep them that
way — a reader scanning a month should be able to follow the sequence without checking every
`<span class="date">`.

The order is:

1. **Dated events, earliest first.** Sort on the *start* of the date, so `Jul 20–22` comes
   before `Jul 21–22`. Ties keep their existing order.
2. **Then cards spanning the section's whole window.** A roundup covering `Jul 10–24` inside
   the `July (10th–24th)` section is a summary of the period, not an event in it, so it
   belongs after the events it summarises — not first, which is where a naive start-date sort
   puts it.
3. **Then undated cards last** (`Mar`, `Mar (ongoing)`), in whatever order they already had.

`early`/`mid`/`late <Month>` are dates, not undated — sort them as roughly the 5th, 15th and
25th. Only a card with no day-level information at all falls to group 3.

New months are written in order, so this mostly costs nothing. It matters when backfilling:
an item added to a month that already exists goes at its date, not at the bottom.

### Scope: new and backfilled months only

This binds a month **while you are writing it**. Sort a new month as you compose it, and
place a backfilled item at its date rather than at the bottom of the month it lands in.

Months already published are **frozen**, even when their order is wrong. Finding a
mis-ordered card in an existing month is not licence to re-sort it — *append, don't rewrite*
wins, because a reorder rewrites history in the diff whether or not it rewrites any text,
and the audit trail in `git log --oneline digest.html` is worth more than a tidy month.

Revision 8 reordered January through May in one pass. That was the baseline-setting
normalisation and it is not a precedent: after rev 8, an existing month is only reordered
with the maintainer's agreement, asked for first (see *Non-negotiables*).

### Checking a reorder

While you are still writing a month, a reorder is a pure move: no card text changes. If a
reorder produces a diff with unequal insertions and deletions, or changes the file's byte
length, something other than order changed and the diff needs reading before it is pushed.
A reorder is a `digest.html` content change, so it bumps `revision` and leaves
`coverage_start` / `coverage_end` alone.

## Non-negotiables

- **Everything tracked here is public, `dist/` included.** No credential in any committed file —
  and note that the bundles are built from `skills/`, so a token parked in a `SKILL.md` gets
  published on the next build. The write token lives in `.env` (gitignored) and is supplied at
  the moment of pushing, never stored.
- **CONFIRMED vs REPORTED is load-bearing.** Items are promoted only when corroboration actually
  appears. A digest full of unverified claims is worse than a stale one, because staleness is a
  gap the reader can be told about and a fabricated baseline isn't.
- **Append, don't rewrite.** New months get added; existing months stay as written, card order
  included, once the month is published. The instructional comment block, the `coverage-end`
  meta tag, and the visible patch label survive every regeneration. Correcting a claim that
  later proved wrong is fine — say so in the gaps box, with the revision that changed it.
- **Don't edit `dist/` by hand.** It is generated. Change `skills/` and rebuild.
- **If a change would break a rule in this file, say so before making it.** Not in the commit
  message, not in the PR body after the fact — beforehand, to the maintainer, with the rule
  named and the reason it seems worth breaking. Some of these rules should lose an argument
  occasionally; none of them should lose one silently. A PR that quietly bends a rule costs
  more review attention than the change was worth, because the reviewer has to reconstruct
  which rule moved and why. This applies to the agent that notices, whichever one that is.

## Conventions

- Commit messages state what changed, which agent wrote it, and — for digest changes — the new
  revision. `git log --oneline digest.html` is the audit trail.
- The build is reproducible: identical content produces identical zips, so `git status` stays
  clean if nothing actually changed. If a rebuild dirties `dist/` when you changed nothing,
  that's a bug in `scripts/build-skills.sh`, not noise to commit.
