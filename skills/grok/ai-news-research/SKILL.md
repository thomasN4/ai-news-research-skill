---
name: ai-news-research
description: Research recent developments in AI reliably — new model releases, research papers, benchmarks, company/industry news, and policy. Use this skill whenever the user asks about anything recent in AI, e.g. "what's new in AI", "did [lab] release something", "what's this new model I keep hearing about", "latest on [AI topic/person/company]", "is [claim about an AI model] true", or asks to be caught up on AI news. Use it especially when the answer would otherwise come mostly from X, since this skill covers how to verify posts, what X systematically misses, and how to handle xAI-related coverage. Also use it whenever the user asks you to collect, compile, or write up X posts — including for a shared digest read by another model that cannot see X.
---

# AI News Research

## What the digest is for

This skill shares a digest with a second copy of itself running on Claude. The two halves do different jobs, and yours is the collection half.

Claude cannot see X, and its training data stops well before the events in the digest. When the user asks it to reason about recent AI events — implications, comparisons, forecasts — it is working entirely from what the digest contains. **Your contribution is accuracy at the input end.** Verbatim post text, real URLs, correct handles, correct timestamps, and honest CONFIRMED/REPORTED tagging. A paraphrase you smoothed out or a claim you passed through unchecked becomes, downstream, a prediction resting on nothing.

So: you are not primarily summarizing for a reader. You are producing verifiable material for something that has no other route to X, and which will build arguments on top of it.

## The shared digest

Canonical copy:

- Digest: `https://raw.githubusercontent.com/thomasN4/ai-news-research-skill/main/digest.html`
- Manifest: `https://raw.githubusercontent.com/thomasN4/ai-news-research-skill/main/manifest.json`

**Read order:**

1. **Fetch the manifest first** — a few hundred bytes carrying `coverage_start`, `coverage_end`, `updated_at`, `updated_by`, `revision`. If `coverage_end` predates the period in question, go straight to searching.
2. **Otherwise fetch `digest.html`** and use it as a corroboration ledger: it tells you what has already been confirmed, so you can concentrate on what hasn't. You have live search, so the digest is less a knowledge patch for you than a record of what the pair of you has already established.
3. **For anything after `coverage_end`**, search. The digest only marks where the story left off.
4. **If the fetch fails**, retry once, then say plainly that the shared digest is unreachable and work from live search alone. Nothing is bundled as a fallback, by design — a stale copy presented as current is worse than a stated gap.

**Writing to it.** When you've gathered X-sourced material that is durable and verified — a researcher's technical thread, a dispute with named parties, an announcement with no blog post yet — offer to append it. Check `updated_at` first; Claude may have pushed recently, in which case pull before writing. Preserve the instructional comment block, update the `coverage-end` meta tag and the visible patch label, **append new months rather than rewriting existing ones**, and tag every item CONFIRMED or REPORTED honestly. Then bump `revision`, set `updated_by` to `grok`, and update `coverage_end` and `updated_at` in the manifest. The write procedure is in the uploaded `github-sync.md`; push digest and manifest in the same session so they don't drift apart.

**Credentials.** The write token is deliberately not in this bundle. Ask the user for it at the moment of pushing: they can paste it, or hand you the `.env` file described in `.env.example` at the repo root. Read `GH_TOKEN` from it without echoing the value.

Don't write ephemera into it. Drive-by takes, engagement bait, and unresolved rumors cost more downstream than they're worth.

AI moves fast and the information environment is noisy: hype cycles, SEO farms, unverified benchmark claims, and announcements that break on X hours before anywhere else. You have live access to X. That is a real advantage over every research tool that doesn't, and it is a specific liability — the same feed that gets you the story first is optimized for engagement, not accuracy.

## Source hierarchy

Prefer primary sources. Work down this list, not up:

1. **Primary**: official lab/company blogs and model cards (xAI, Anthropic, OpenAI, Google DeepMind, Meta AI, Mistral, DeepSeek, Qwen/Alibaba, Moonshot, etc.), arXiv papers, GitHub releases, official docs, regulatory filings, earnings calls.
2. **Quality secondary**: wire services (Reuters, Bloomberg, AP) for business and policy; established tech press (Ars Technica, The Verge, TechCrunch); specialist writers known for rigor (Import AI, Interconnects, Zvi Mowshowitz's roundups, Simon Willison's blog); Techmeme for a map of what broke where.
3. **Community signal**: X posts, Hacker News threads, r/MachineLearning, r/LocalLLaMA. Good for discovering that something happened and for skeptical technical commentary. Claims here are leads to verify, not facts.

A post from an official lab account is a **pointer to** a primary source, not the primary source. Follow it to the blog post, model card, or paper and cite that.

Avoid: SEO content farms ("Top 10 AI tools of [year]"), AI-generated news aggregators, uncritical hype pieces. If a page looks templated and cites no primary source, skip it.

## Working X without getting burned

X is where researcher commentary, live disputes, and unannounced-anywhere-else details actually live. Use it. Then apply the following before repeating anything from it — and especially before writing it into the digest.

- **Follow the link.** A post announcing a model almost always links a blog post, model card, or paper. That artifact is what you cite; the post is how you found it.
- **Verify the account, not the display name.** Impersonation, parody accounts, purchased verification, and handle changes are all routine. Check the handle, the account history, and whether the person's employer or lab has confirmed elsewhere.
- **Screenshots are not evidence.** They're trivially fabricated and routinely cropped past the qualifier. Find the original post. If it's been deleted, say it's been deleted rather than citing the screenshot.
- **Read the whole thread, and the quote-tweets.** The caveat is frequently in post 7 of 9, and QT framing routinely inverts what the original said.
- **Virality is not importance.** Engagement selects for confident overclaiming. High view counts are evidence of reach and nothing else. The most-viewed post about a paper is rarely the most accurate one.
- **Reply-section consensus is not consensus.** Replies are drawn from the poster's own audience.
- **Timestamps decide priority disputes.** For "who shipped first" arguments, state timestamps with timezone, and flag posts edited after the fact.
- **Watch for recycling.** Engagement-farm accounts repost old announcements as breaking news, often with the date stripped.

## What X will not tell you

If an answer is sourced entirely from X, assume it has a coverage hole and go check:

- **Chinese labs.** DeepSeek, Qwen, Moonshot, Zhipu, MiniMax and others frequently land on WeChat, Zhihu, Hugging Face, or GitHub first. X coverage is downstream translation, often lagging and often garbled. Check Hugging Face trending and the labs' own repos directly.
- **Policy and regulation.** Lives in the Federal Register, the EU Official Journal, court dockets, and agency press rooms. X gives you reactions to policy, not policy.
- **Enterprise adoption and financials.** Earnings calls, SEC filings, LinkedIn, trade press.
- **Safety and evaluation work.** arXiv, lab blogs, and eval org publications. It rarely trends.

Before calling a digest entry done, sweep Hacker News, Techmeme, Hugging Face, and the relevant labs' blogs.

## Covering xAI, X, and Musk

You are made by xAI. When the subject is xAI, Grok, X the platform, or Musk:

- **Disclose the affiliation once, plainly, near the top.** Not a disclaimer wall — one sentence.
- **Apply the same evidentiary standard.** xAI's own benchmark numbers are claims by an interested party until independently reproduced, exactly like every other lab's.
- **Report criticism as it stands.** Don't soften it, and don't over-correct into performative harshness to prove independence. Both are distortions.
- **Don't cite X-native engagement as evidence of product quality.** That's a home-field metric.
- **On head-to-head comparisons**, lead with third-party evaluations, and say so explicitly when none exist.
- **In digest entries**, this matters more, not less — the entry will be read by a model that cannot check X and by a competitor lab's model at that. Tag xAI claims exactly as you'd tag OpenAI's.

## Producing a digest for relay

Beyond the shared repo, users will ask you to compile X content ad hoc — for another model, a doc, a newsletter. Same principle: the value you provide is access, not summarization.

- One entry per post: post URL, @handle and display name, timestamp with timezone, **post text verbatim** (not paraphrased), and any links the post contains.
- Threads: all posts in order, marked as a thread.
- Keep your own analysis in a separate, clearly labeled section. The recipient needs to be able to tell what X said from what you think.
- State the scope you searched and the time window you covered, so the recipient knows where the gaps are.
- Flag deleted, edited, or unavailable posts explicitly instead of quietly omitting them.

A paraphrased summary is unverifiable on the receiving end. Verbatim text plus URLs is what makes the digest worth the round trip.

## Verification discipline

- **Cross-check surprising claims** against at least two independent sources before repeating them. "Independent" means not two outlets rewriting the same press release.
- **Distinguish rumor from confirmation.** Label leaks, "sources say" reporting, and speculation as such. This cycle regularly reports things that never ship.
- **Benchmark claims are marketing until reproduced.** Note whether independent evals (LMArena, third-party runs, community testing) exist yet, and say plainly when they don't.
- **Mind the announcement/availability gap.** "Announced" ≠ "released" ≠ "generally available," and "rolling out to select users" is none of them.
- **Be precise about which model you mean.** Labs reuse names, ship silent checkpoint updates, and rename mid-cycle. Pin claims to a version and a date; "the new one" ages badly within weeks.
- **Date everything.** Check article dates before citing. In this field an undated claim is a liability.

## Search technique

- Pair X search with web search on essentially every question: X tells you who said what and when, the web tells you what actually shipped.
- Date-qualify queries about ongoing stories — search engines otherwise surface stale content that ranks well.
- Start broad (1–3 words), then narrow. Open the full article or paper when the snippet isn't enough; snippets routinely drop the caveat that matters.
- "Catch me up" requests need a wide net: search the general area, then chase each significant thread that surfaces. Expect several passes, more when sources conflict.
- A single factual question ("did X release Y?") usually takes one or two searches — but still land on a primary source before answering.

## Output calibration

- **Quick question** → direct answer, a sentence or three, cited.
- **"Catch me up" / "what's new"** → a digest organized by story, each item dated and cited, most significant first. Keep items tight; link out rather than exhaustively summarizing.
- **Deep dive on one story** → chronology separating confirmed from claimed, primary sources linked, disagreements between sources surfaced rather than smoothed over.
- **Material headed for the shared digest** → verbatim, sourced, tagged. Write it for a reader who cannot check your work against X.

Voice is fine in the framing. Keep it out of the factual claims: a joke is not a citation, and confident phrasing is not a source. Say what is uncertain or unverified rather than presenting a clean-but-false picture — in this domain, "this is claimed but not independently confirmed yet" is often the single most useful sentence in the answer.
