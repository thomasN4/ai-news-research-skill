---
name: ai-news-research
description: Research recent developments in AI reliably — new model releases, research papers, benchmarks, company/industry news, and policy. Use this skill whenever the user asks about anything recent in AI, e.g. "what's new in AI", "did [lab] release something", "what's this new model I keep hearing about", "latest on [AI topic/person/company]", "is [claim about an AI model] true", or asks to be caught up on AI news. Use it especially when the user asks you to reason about, forecast, or draw implications from recent AI events, since your training data does not cover them and this skill supplies a dated, sourced digest that does. Also use it when a user shares a Twitter/X link about AI (X is not directly accessible; this skill contains the workarounds, including a Grok-as-courier workflow for relaying X content), or uploads a Grok-generated digest of X posts.
---

# AI News Research

## What the digest is for

Your training data stops before the events this skill covers. The digest exists to close that gap — not so you can recite it back, but so you can **reason** over recent events: compare a new release against what shipped before it, trace how a dispute developed, and answer the forecasting questions the user will actually ask ("does this change the picture for X?", "who's likely to respond?", "is this trend holding?"). Predictions and implications drawn from a blank spot in your knowledge are worthless, so treat loading the digest as a precondition for that class of question, not an optimization.

This is the asymmetric half of a shared resource. Grok runs the same digest from the same repo, but for the opposite reason: it has live access to X and its job is to feed accurate, verbatim X-sourced material *in*. Yours is to consume the result and think with it. When you regenerate the digest, that division holds — you are the one adding synthesis, chronology, and CONFIRMED/REPORTED discipline.

## The shared digest

Canonical copy, shared with Grok:

- Digest: `https://raw.githubusercontent.com/thomasN4/ai-news-research-skill/main/digest.html`
- Manifest: `https://raw.githubusercontent.com/thomasN4/ai-news-research-skill/main/manifest.json`

**Read order:**

1. **Fetch the manifest first.** It is a few hundred bytes and carries `coverage_start`, `coverage_end`, `updated_at`, `updated_by`, and `revision`. If `coverage_end` predates the period the question is about, skip the digest and go straight to searching.
2. **Otherwise fetch `digest.html`** and use it as the baseline — it usually saves several searches. Verify anything tagged REPORTED before repeating it, and re-verify anything the user's question makes load-bearing.
3. **For anything after `coverage_end`**, search the web. The digest only tells you where the story left off.
4. **If the fetch fails**, retry once. If it still fails, say plainly that the shared digest is unreachable and work from web search alone — and do not reason about or forecast from post-cutoff events out of memory. Nothing is bundled here as a fallback, by design: an unavailable digest is a known gap you can tell the user about, while a remembered one is a fabricated baseline you can't.

**Regenerating.** When the digest is more than ~2 weeks stale, or research turns up major events past `coverage_end`, offer to update it. Check `updated_at` in the manifest first — Grok may have pushed recently, in which case pull before writing. Preserve the instructional comment block, update the `coverage-end` meta tag and the visible patch label, and **append new months rather than rewriting existing ones**. Keep the CONFIRMED/REPORTED tagging honest; a regenerated digest full of unverified claims is worse than a stale one. Upgrade REPORTED items to CONFIRMED when corroboration has appeared, and note in the gaps box what was resolved or backfilled. Then bump `revision`, set `updated_by` to `claude`, and update `coverage_end` and `updated_at` in the manifest.

**Pushing the update.** See `references/github-sync.md` for the contents-API write procedure. Both files (digest and manifest) go up in the same session so they don't drift apart. Writing the new digest to a local file and stopping there is not a substitute — the sandbox filesystem resets between sessions, so an unpushed change lasts only for the current conversation.

**Credentials.** The write token is deliberately not in this bundle. Ask the user for it at the moment of pushing: they can paste it, or hand you the `.env` file described in `.env.example` at the repo root. Read `GH_TOKEN` from it without echoing the value.

AI moves fast and the information environment around it is noisy: hype cycles, SEO farms, unverified benchmark claims, and announcements that break on X (which you cannot access directly). What follows is a methodology for getting to reliable answers anyway.

## Source hierarchy

Prefer primary sources. Work down this list, not up:

1. **Primary**: official lab/company blogs and model cards (Anthropic, OpenAI, Google DeepMind, Meta AI, Mistral, xAI, DeepSeek, Qwen/Alibaba, etc.), arXiv papers, GitHub releases, official documentation, regulatory filings.
2. **Quality secondary**: wire services (Reuters, Bloomberg, AP) for business/policy; established tech press (Ars Technica, The Verge, TechCrunch); specialist newsletters and blogs known for rigor (e.g. Import AI, Interconnects, Zvi Mowshowitz's roundups, Simon Willison's blog); Techmeme for a map of what broke where.
3. **Community signal**: Hacker News threads, r/MachineLearning, r/LocalLLaMA. Useful for discovering what happened and for skeptical technical commentary, but treat claims in comments as leads to verify, not facts.

Avoid: SEO content farms ("Top 10 AI tools of [year]"), AI-generated news aggregator sites, and uncritical hype pieces. If a site looks templated and cites no primary source, skip it.

## The X/Twitter problem

Much AI news breaks first on X, but x.com and twitter.com are behind a login wall — direct fetches fail or return nothing useful. Do not waste tool calls fetching X URLs repeatedly, and do not bother with Nitter mirrors (mostly dead).

Workarounds, in order of usefulness:

- **Check the digest first.** Grok writes X-sourced material into it with verbatim quotes and URLs. If the story is recent and X-native, the digest may already have what a courier round trip would fetch.
- **Search for secondhand coverage.** Notable posts get quoted within hours by news sites, newsletters, HN, and Techmeme. Search the person's name plus the topic, e.g. `[researcher name] [model name] claim`.
- **Go to the primary source the post points at.** A tweet announcing a model almost always links a blog post or paper — find *that* instead.
- **If the user pastes an X link**: try one web_fetch on it (occasionally metadata comes through), and when it fails, tell the user plainly that X is inaccessible, then search for coverage of the post using whatever context they gave. Ask them to paste the post text if the search comes up dry.
- **Grok as courier** (when the story lives mostly on X, the digest doesn't cover it, and secondhand coverage is thin): Grok has native X access, so the user can act as a relay. See the workflow below.

### The Grok courier workflow

Offer this when X is clearly where the substance is (a researcher's thread, a dispute playing out in replies, an announcement with no blog post yet) and web searches keep coming back with thin paraphrases. Don't push it for stories with adequate primary/press coverage — it costs the user real effort.

1. **Draft the Grok prompt for the user.** Write it out verbatim in a copyable block. Ask Grok to output a markdown document where each item includes: the post URL, the author's @handle and display name, the timestamp, the post text quoted verbatim (not paraphrased), and any links the post contains. Scope it tightly — a specific person, thread, claim, or time window — and tell Grok to separate what posts *say* from its own commentary. Vague prompts ("summarize AI twitter this week") produce unverifiable mush. If the material looks durable, ask Grok to also write it into the shared digest.
2. **Read the upload skeptically.** A Grok digest is tier-3 community signal wearing a markdown suit: an AI summary of a feed you cannot see. Verbatim quotes with URLs are the valuable part — the URLs identify the primary sources to chase (papers, blog posts, repos), and named posts can be corroborated via secondhand coverage. Grok's own summarization and any unsourced claims get the same treatment as a Reddit comment: leads, not facts. Never re-report a claim as confirmed solely because it appeared in the digest.
3. **Iterate.** After reading, identify gaps — missing timestamps, a reply chain the digest skipped, a claim that needs the original wording — and hand the user a follow-up Grok prompt targeting exactly those. Expect 1-3 round trips for a contested story; keep each follow-up prompt narrow so the user isn't relaying essays back and forth.
4. **Attribute the pipeline in the answer.** When findings rest on the digest, say so: "per an X post by @so-and-so (via a Grok-compiled digest, not independently verified)". If a digest claim later checks out against a primary source, cite the primary source instead.

## Verification discipline

- **Cross-check surprising claims** against at least two independent sources before repeating them. "Independent" means not just two outlets rewriting the same press release.
- **Distinguish rumor from confirmation.** Label leaks, "sources say" reporting, and speculation as such. The AI news cycle regularly reports things that never ship.
- **Benchmark claims are marketing until reproduced.** A lab's own eval numbers are a claim by an interested party. Note whether independent evals (e.g. LMArena, third-party benchmark runs, community testing) exist yet, and say so when they don't.
- **Mind the announcement/availability gap.** "Announced" ≠ "released" ≠ "generally available." Be precise about which one is true.
- **Date everything.** Check article dates before citing. In a field where "three months ago" is old news, an undated claim is a liability. When summarizing, attach dates to developments.

## Search technique

- Include the current date or "today"/"this week" in queries about ongoing stories; search engines otherwise surface stale content that ranks well.
- Start broad (1-3 words), then narrow. Fetch full articles with web_fetch when the snippet isn't enough — snippets routinely omit the caveats that matter.
- For "catch me up" requests, cast a wide net: search the general topic, then follow up on each significant thread that surfaces. Expect 4-8 tool calls for a good digest, more if threads conflict.
- For a single factual question ("did X release Y?"), one or two searches usually suffice — but still land on a primary source before answering.

## Output calibration

Match the response to the ask:

- **Quick question** → direct answer, a sentence or three, cited.
- **"Catch me up" / "what's new"** → a digest organized by story, each item dated and cited, most significant first. Keep individual items tight; link out rather than exhaustively summarizing.
- **Deep dive on one story** → chronology of what's confirmed vs. claimed, primary sources linked, disagreements between sources surfaced rather than smoothed over.
- **Reasoning or prediction about recent events** → load the digest first, then be explicit about which parts of the reasoning rest on CONFIRMED material and which rest on REPORTED. A forecast built on an unverified claim should say so in the same breath.

In all cases: say what is uncertain or unverified rather than presenting a clean-but-false picture. In this domain, "this is claimed but not yet independently confirmed" is often the single most useful sentence in the response.
