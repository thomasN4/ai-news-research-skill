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

## Dating a card

**A card's date records when the thing happened, not when anyone said so.** An incident made
public months later is dated by the incident. The same goes for a Zvi post, a press write-up, a
report's byline or a lab's disclosure: all of them are dates of *telling*.

1. **The chip is the event date.** Use a range when the event spans days (`Jul 23–25`), or an
   arrow for a chronology (`May 7 → Jul 20`). When only the month is known, use it, falling back
   to `early`/`mid`/`late <Month>` and then to the undated group below.
2. **The card lives in the event's section.** A June breach disclosed in September goes in June.
   That makes every such disclosure a backfill: it bumps `revision` and leaves `coverage_end`
   where it is.
3. **Date the thing by when it happened, and date the telling by when it was told. Give the
   telling its own card only if it is news in itself.** A disclosure is news when governments,
   labs or courts act on it, or when the disclosure decision is the story. Albanese's
   press conference and OpenAI's confirmation that it chose not to disclose the wiki board are
   news. A write-up that only reports an old event is not. When both cards exist, each points to
   the other (`the June 18 card`, `the September 23 card`), and the incident's facts live on the
   incident card.
4. **A recent window still tells readers about old events.** When a disclosure in a window adds a
   card to an earlier month, the window's roundup gets a one-line pointer ("Disclosed this
   window, carried at the event's date: ..."). The skill tells readers to start from the latest
   sections, and without the pointer they would never find the backfill.
5. **Partial dates stay honest.** Where the primary dates an incident only loosely ("this
   summer", "in June"), date it as precisely as the primary allows, and say in the card text,
   not the chip, what is unknown.

A report, paper or system card is its own event. It is dated by publication even when it
describes earlier work. What moves is an *incident* dated by its telling.

## Card order within a month

Cards inside a `<section class="month">` read top to bottom as a chronology. Keep them that
way — a reader scanning a month should be able to follow the sequence without checking every
`<span class="date">`. Order runs on the event date, per *Dating a card* above, never on the date
something was disclosed.

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

Mark whole-window roundups explicitly: `<div class="ev" data-roundup="true">`. The CI
linter uses this marker to put them in group 2; a date span alone cannot distinguish a
summary from an event that lasted the whole window. Ordinary event cards have no marker.
The linter rejects definite inversions, including ones separated by an ambiguous date;
bounded dates are compared only when the bounds prove the order, and `~` dates remain for
human review. Unknown date formats fail rather than silently escaping the check.

New months are written in order, so this mostly costs nothing. It matters when backfilling:
an item added to a month that already exists goes at its date, not at the bottom. It applies
to every month, published or not. If you find one out of order, re-sort it.

### Checking a reorder

Put a reorder in its own commit, and make it a pure move with no card text changed. That
keeps the diff readable. If a reorder produces a diff with unequal insertions and deletions,
or changes the file's byte length, something other than order changed, and the diff needs
reading before it is pushed. A reorder is a `digest.html` content change, so it bumps
`revision` and leaves `coverage_start` / `coverage_end` alone.

## Sourcing a forward extension

Start from Zvi Mowshowitz's blog: the weekly `AI #NNN` roundups plus his standalone posts.
`https://thezvi.substack.com/api/v1/archive?sort=new&limit=25` lists them with dates, and
`/api/v1/posts/<slug>` returns a post's full body, so no browser is needed. Treat a post as a map
to primaries, not as the citation. Follow every item to its primary source before carrying it as
CONFIRMED.

- **A post's date is not the event's date, and neither is the primary's.** This has misdated
  cards more than once. Take the event date from the primary, which for an incident report is
  the date of the incident and not the date of the report. See *Dating a card*.
- **The roundups don't cover Brussels.** EU items have to be worked from the Commission's own
  releases, the Official Journal and national gazettes. The Commission press corner renders
  with JavaScript, but
  `ec.europa.eu/commission/presscorner/api/documents?reference=IP/26/NNNN&language=en` returns
  the full text.
- **The roundups lag the primaries.** The biggest items often reach lab feeds before Zvi covers
  them. Sweep these every time: the OpenAI RSS feed (`openai.com/news/rss.xml`), Anthropic's
  `/news` index, xAI's `docs.x.ai/developers/release-notes`, the Claude API release notes,
  METR's blog, and the Gemini API changelog, which is the fastest primary for any Google model
  date.
- **Check the artefact, not the write-up.** Repositories (`config.json`, licence, safetensors
  index), system cards and pricing tables have repeatedly contradicted coverage, and the errors
  are usually of *framing*, which survives fact-checking because each word is true. When a
  window is thick with AI-generated aggregators recycling each other, trace every card to a
  primary or a named outlet, and leave out what can't be traced.
- **Some sources date themselves.** An X post ID encodes its UTC time
  (`(id >> 22) + 1288834974657` ms), so X items can be dated without Grok. The Trump's Truth
  archive (`trumpstruth.org/statuses/<n>`) timestamps Truth Social posts. For a page that
  changes over time, check the Wayback CDX (`web.archive.org/cdx/search/cdx?url=...`) before
  attributing live content to an earlier date.
- **For X content, use the Grok courier.** Ask for URL, handle, UTC timestamp and verbatim text,
  and tell Grok to mark gaps "not found" rather than reconstruct them.
- **A 403 is bot protection, not a dead link.** `openai.com`, `axios.com`, `reuters.com`,
  `cnbc.com`, `washingtonpost.com`, `bloomberg.com`, `sec.gov`, `consilium.europa.eu`,
  `euractiv.com` and others refuse curl, and some refuse Playwright's own Chromium too. They
  load in a real browser (Brave driven over CDP on a virtual display, with a throwaway
  profile). `deploymentsafety.openai.com`, where OpenAI's system cards live, serves to curl.
  Axios gates its body after the lede in any browser; its Yahoo syndication carries the full
  text. Keep the citation either way.

## Non-negotiables

- **Everything tracked here is public, `dist/` included.** No credential in any committed file —
  and note that the bundles are built from `skills/`, so a token parked in a `SKILL.md` gets
  published on the next build. The write token lives in `.env` (gitignored) and is supplied at
  the moment of pushing, never stored.
- **CONFIRMED vs REPORTED is load-bearing.** Items are promoted only when corroboration actually
  appears. A digest full of unverified claims is worse than a stale one, because staleness is a
  gap the reader can be told about and a fabricated baseline isn't.
- **Fix cards in place.** When a card turns out to be wrong, stale, misdated, mis-ordered or
  badly framed, correct the card itself. Don't leave it standing and park the correction in
  the gaps box. Git is the history: the commit message says what changed and why, and
  `git log -p digest.html` shows the old text. The gaps box is for what is still open or
  unverified, so remove items from it once they are resolved. The comment block's instructions
  and coverage line, the `coverage-end` meta tag and the visible patch label are functional,
  and they survive every regeneration.
- **The digest records the current state only.** What changed and why goes in the commit
  message and the PR, never in the digest: no per-revision notes in the comment block, no
  "(backfilled at vN)" or "until vN this file said" in a card, no "(added at vN)" in the
  themes, and no revision-keyed paragraphs in the gaps box. The gaps box keeps three kinds of
  item: open, unverified or single-source, and deliberately not covered. Where a correction
  matters to a reader, for instance because a wrong date is in wide circulation, state the
  correction and leave out the revision: "coverage dates this Sep 9; the press release is
  Sep 3". Sourcing method that outlasts one revision goes in *Sourcing a forward extension*
  above.
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
