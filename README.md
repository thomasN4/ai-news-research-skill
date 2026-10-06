# ai-news-research-skill

Shared state — plus the skills that read and write it — for keeping two assistants current on
AI news. Grok has live X access and feeds verbatim, sourced material *into* the digest; Claude
has no X access and a training cutoff well before these events, so it reads the digest and
reasons with it. The digest is the interface between them.

**Reading the digest:** <https://thomasn4.github.io/ai-news-research-skill/> renders it in a
browser. The raw URL the skills fetch is served as `text/plain`, so it shows source instead.

**Installing:** see [INSTALL.md](INSTALL.md).

## Layout

```text
├── digest.html                       the digest — the only copy, fetched live by both skills
├── manifest.json                     cheap freshness check; read this before the digest
├── index.html                        redirect to digest.html, so the Pages URL lands on it
├── .nojekyll                         no Jekyll build; digest.html is self-contained
├── INSTALL.md
├── AGENTS.md                         conventions for agents working on this repo
├── .env.example                      how to mint the write token
├── skills/
│   ├── common/references/
│   │   └── github-sync.md            shared write procedure (contents API, sha as concurrency control)
│   ├── claude/ai-news-research/SKILL.md
│   └── grok/ai-news-research/SKILL.md
├── .github/workflows/lint.yml         CI checks for pushes to main and pull requests
├── .markdownlint-cli2.jsonc           Markdown lint configuration
├── .htmlvalidate.json                HTML validation configuration
├── scripts/
│   ├── build-skills.sh               skills/ → dist/
│   ├── lint.sh                       the same checks locally and in CI
│   └── lint-digest.py                digest metadata and card checks
├── tests/test_digest_lint.py          regression checks for the digest linter
└── dist/
    ├── ai-news-research-claude.skill  what you upload to Claude (.skill, not .zip —
    │                                  it's what shows the "save skill" button)
    └── ai-news-research-grok.zip      download container for the two Grok files
```

| File | Purpose |
| --- | --- |
| `manifest.json` | `coverage_start`, `coverage_end`, `updated_at`, `updated_by`, `revision`. A few hundred bytes, so an agent can check freshness without pulling ~60 KB. |
| `digest.html` | Sourced chronology of AI developments, each dated by when it happened rather than when it was disclosed, every item tagged CONFIRMED or REPORTED. Carries its own `coverage-start`/`coverage-end` meta tags and an instructional comment block for whichever agent regenerates it. |

## Conventions

- **Manifest first.** If `coverage_end` predates the period in question, don't fetch the digest —
  search instead.
- **Fix cards in place.** New months get added. When an existing card is wrong or stale,
  correct the card itself and say what changed in the commit message; git holds the history.
  The gaps box lists only what is still open, unverified or deliberately not covered. The
  digest records the current state only; its history lives in git. The comment block's
  instructions and coverage line, the `coverage-end` meta tag, and the visible patch label are
  preserved across regenerations.
- **Digest first, manifest second** when pushing, so the manifest never advertises coverage the
  digest lacks. Both go up in the same session.
- **CONFIRMED vs REPORTED is load-bearing.** A digest full of unverified claims is worse than a
  stale one. Items get upgraded to CONFIRMED only when corroboration actually appears.
- `revision` is bumped on every write and `updated_by` set to the agent that wrote it (`claude`
  or `grok`). `git log --oneline digest.html` is the audit trail.

Grok writes straight to `main` through the GitHub contents API, using the current blob `sha` as
concurrency control — a 409 means the other agent pushed first, so re-pull, re-apply, retry.
Claude works on a branch and opens a PR, where that guard doesn't apply. Full procedure in
[`skills/common/references/github-sync.md`](skills/common/references/github-sync.md). Reads need
no auth; only writes need the token from `.env`.

## Why the digest isn't bundled in the skills

Both skills fetch `digest.html` from its raw URL at runtime and neither ships a copy. So a digest
push — the frequent operation, and the point of the repo — never invalidates the installed
bundles, and there is exactly one copy of the digest to keep honest. The cost is that an
unreachable raw URL leaves the agent with no baseline at all; both SKILL.md files handle that by
saying so out loud and falling back to search, rather than reasoning about post-cutoff events
from memory.

`dist/` therefore only needs rebuilding when a `SKILL.md` or `github-sync.md` changes — never on
a digest update:

```bash
bash scripts/build-skills.sh
```

Docs and skill edits are not digest revisions: `revision` in the manifest tracks digest content
only, so a commit like this one leaves it alone.

## Linting

GitHub Actions checks Markdown with markdownlint, HTML with html-validate, shell scripts
with ShellCheck, and the digest's metadata and cards on pushes to `main` and pull requests.
Markdown line length is unrestricted to accommodate prose and source URLs; the other
default rules apply.

Digest checks require the coverage meta tags, instructional comment, and visible patch
label to agree with `manifest.json`, and the title, patch label, and footer to carry its
revision. Every event card must be in a month section and have a heading, date, a consistent
CONFIRMED/REPORTED chip, and a source link.

Within each month section, the linter rejects definite chronological inversions. Ranges
and arrows sort on their start; `early`/`mid`/`late` use the 5th/15th/25th. Bounds such as
`by Sep 24` or `on or before Jan 13` are compared only when their ordering is certain.
`~` dates have no defined tolerance, so their relative order is left to review. An ambiguous
card between two definitely reversed cards does not hide the inversion.

Mark whole-window summaries with `data-roundup="true"` on their `.ev` divs; these belong
after dated events and before month-only dates such as `Mar` or `Mar (ongoing)`. An ordinary
event can span the same window, so date spans alone never imply a roundup. Unknown date
formats fail with a line number rather than silently bypassing the check. If coverage
spans multiple years, add `data-year="2026"` (with the appropriate year) to each month section.
The checks validate structure, metadata, and definite ordering; event dating, ambiguous
ordering, corroboration, and source availability still need review.

To run the same checks locally, install Node.js 22.22+ or 24.8+ (with npm), Python 3, and
ShellCheck, then run:

```bash
bash scripts/lint.sh
```

The script downloads pinned markdownlint and html-validate CLIs via `npx` on its first run.
