# ai-news-research-skill

Shared state for the `ai-news-research` skill. Two agents read and write these files:
Claude (consumes the digest to reason about recent AI events it has no training data for)
and Grok (feeds verbatim X-sourced material in, since it has live X access).

| File | Purpose |
| --- | --- |
| `manifest.json` | Cheap freshness check — read this first. Carries `coverage_start`, `coverage_end`, `updated_at`, `updated_by`, `revision`. |
| `digest.html` | The digest itself: a dated, sourced chronology of AI developments, every item tagged CONFIRMED or REPORTED. |

Raw URLs the skill fetches:

```
https://raw.githubusercontent.com/thomasN4/ai-news-research-skill/main/manifest.json
https://raw.githubusercontent.com/thomasN4/ai-news-research-skill/main/digest.html
```

## Conventions

- **Manifest first.** If `coverage_end` predates the period in question, don't bother
  fetching the digest — search instead.
- **Append, don't rewrite.** New months get added; existing months stay as written.
  The instructional comment block at the top of `digest.html` is preserved across
  regenerations, along with the `coverage-end` meta tag and the visible patch label.
- **Digest first, manifest second** when pushing, so the manifest never advertises
  coverage the digest lacks. Both go up in the same session.
- **CONFIRMED vs REPORTED is load-bearing.** A digest full of unverified claims is
  worse than a stale one. Items get upgraded to CONFIRMED only when corroboration
  actually appears.
- `revision` is bumped on every write and `updated_by` set to the agent that wrote it
  (`claude` or `grok`). `git log --oneline digest.html` is the audit trail.

Writes use the GitHub contents API with the current blob `sha` as concurrency control —
a 409 means the other agent pushed first, so re-pull, re-apply, retry. Procedure lives
in the skill's `references/github-sync.md`.

Seeded from the copy bundled in the skill (v3, compiled 2026-07-25).
