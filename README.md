# ai-news-research-skill

Shared state — plus the skills that read and write it — for keeping two assistants current on
AI news. Grok has live X access and feeds verbatim, sourced material *into* the digest; Claude
has no X access and a training cutoff well before these events, so it reads the digest and
reasons with it. The digest is the interface between them.

**Installing:** see [INSTALL.md](INSTALL.md).

## Layout

```
├── digest.html                       the digest — the only copy, fetched live by both skills
├── manifest.json                     cheap freshness check; read this before the digest
├── INSTALL.md
├── AGENTS.md                         conventions for agents working on this repo
├── .env.example                      how to mint the write token
├── skills/
│   ├── common/references/
│   │   └── github-sync.md            shared write procedure (contents API, sha as concurrency control)
│   ├── claude/ai-news-research/SKILL.md
│   └── grok/ai-news-research/SKILL.md
├── scripts/build-skills.sh           skills/ → dist/
└── dist/
    ├── ai-news-research-claude.skill  what you upload to Claude (.skill, not .zip —
    │                                  it's what shows the "save skill" button)
    └── ai-news-research-grok.zip      download container for the two Grok files
```

| File | Purpose |
| --- | --- |
| `manifest.json` | `coverage_start`, `coverage_end`, `updated_at`, `updated_by`, `revision`. A few hundred bytes, so an agent can check freshness without pulling 46 KB. |
| `digest.html` | Dated, sourced chronology of AI developments, every item tagged CONFIRMED or REPORTED. Carries its own `coverage-start`/`coverage-end` meta tags and an instructional comment block for whichever agent regenerates it. |

## Conventions

- **Manifest first.** If `coverage_end` predates the period in question, don't fetch the digest —
  search instead.
- **Append, don't rewrite.** New months get added; existing months stay as written. The
  instructional comment block, the `coverage-end` meta tag, and the visible patch label are
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
