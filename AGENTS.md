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

## Non-negotiables

- **Everything tracked here is public, `dist/` included.** No credential in any committed file —
  and note that the bundles are built from `skills/`, so a token parked in a `SKILL.md` gets
  published on the next build. The write token lives in `.env` (gitignored) and is supplied at
  the moment of pushing, never stored.
- **CONFIRMED vs REPORTED is load-bearing.** Items are promoted only when corroboration actually
  appears. A digest full of unverified claims is worse than a stale one, because staleness is a
  gap the reader can be told about and a fabricated baseline isn't.
- **Append, don't rewrite.** New months get added; existing months stay as written. The
  instructional comment block, the `coverage-end` meta tag, and the visible patch label survive
  every regeneration. Correcting a claim that later proved wrong is fine — say so in the gaps
  box, with the revision that changed it.
- **Don't edit `dist/` by hand.** It is generated. Change `skills/` and rebuild.

## Conventions

- Commit messages state what changed, which agent wrote it, and — for digest changes — the new
  revision. `git log --oneline digest.html` is the audit trail.
- The build is reproducible: identical content produces identical zips, so `git status` stays
  clean if nothing actually changed. If a rebuild dirties `dist/` when you changed nothing,
  that's a bug in `scripts/build-skills.sh`, not noise to commit.
