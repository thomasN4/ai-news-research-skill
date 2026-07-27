# Installing

Two skills, two different platforms. **You almost certainly want one of them, not both** —
pick the section for whichever assistant you're installing into.

They're two halves of one arrangement. Grok can see X and has live search, so its job is to
push accurate, verbatim X-sourced material *into* the shared digest. Claude can't see X and
its training data stops before the events in the digest, so its job is to read the digest and
reason with it. Neither copy is useful to the other's platform: Claude's tells it how to work
around having no X access, Grok's tells it how not to get burned by having it.

Both fetch the same two files at runtime, and reading them needs no account and no token:

```
https://raw.githubusercontent.com/thomasN4/ai-news-research-skill/main/manifest.json
https://raw.githubusercontent.com/thomasN4/ai-news-research-skill/main/digest.html
```

A token is only needed to *push* an updated digest — see [`.env.example`](.env.example). Skip
that entirely if you just want the read side working.

---

## Claude (web app)

1. Download **[`dist/ai-news-research-claude.skill`](dist/ai-news-research-claude.skill)** — use the
   "Download raw file" button, not "Save page as".
2. In Claude, go to **Customize → Skills**, click **+**, then **+ Create skill → Upload a skill**.
   (On older builds this lives at **Settings → Capabilities → Skills**.)
3. Pick the zip. Claude reads the `SKILL.md` inside and shows you a summary of what it does.
4. The skill appears in your list as a toggle. Leave it on; it activates by itself when a
   question matches its description.

Test it with a fresh chat: *"what's new in AI?"* You should see it fetch the manifest, then the
digest, before answering.

**Things that make the upload fail:**

- **The zip must contain exactly one top-level folder, named `ai-news-research`** — matching the
  `name:` field in the frontmatter. That's why both bundles use the same inner folder name even
  though the zip filenames differ. If you re-zip by hand, zip the *folder*, not its contents:
  `zip -r out.zip ai-news-research`.
- **The Claude bundle is named `.skill`.** That extension is what makes the web app's "save
  skill" button appear, including when Claude hands you a rebuilt bundle in-chat after running
  the `github-sync.md` procedure. If the **Upload a skill** file picker won't select it, rename
  your copy to `.zip` — it is an ordinary zip archive and nothing inside changes. The Grok
  bundle stays `.zip`: Grok has no skill uploader, so there is no button for it to trigger.
- **Don't install both bundles into one Claude account.** They share the inner folder name and
  the skill name, so the second collides with the first. The Grok bundle is for Grok.

Custom skills are private to your account (Team/Enterprise sharing aside).

---

## Grok (web app)

Grok has no skill uploader. The equivalent is a **Workspace** — its own conversation history,
its own uploaded files, and its own custom instructions that override your global ones.

1. Download **[`dist/ai-news-research-grok.zip`](dist/ai-news-research-grok.zip)** and unzip it
   locally. The zip is only a download container here; Workspace files are flat, so you upload
   the two files individually. You can also grab them straight from
   [`skills/grok/ai-news-research/`](skills/grok/ai-news-research/) and
   [`skills/common/references/`](skills/common/references/).
2. Create a Workspace (**Workspaces → Add New**), name it something like *AI news research*.
3. Upload both files into it: **`SKILL.md`** and **`github-sync.md`**.
4. Put a short bootstrap in the Workspace's custom-instructions box:

   > For anything about recent AI developments — releases, papers, benchmarks, company news,
   > policy — follow the uploaded ai-news-research SKILL.md. It covers the shared digest, source
   > hierarchy, and how to verify X posts. The digest write procedure is in the uploaded
   > github-sync.md.

5. Use that Workspace for AI-news questions. Outside it, the instructions don't apply.

**Why the file plus a pointer, rather than pasting the whole thing into the box:** the
instructions box has a character limit in the low thousands and that `SKILL.md` is around 12 KB.
It won't fit, and truncating it silently drops the verification discipline — which is the part
that matters. Uploaded files have no such limit.

Note that the Grok copy refers to `github-sync.md` by filename, not by path. Workspace uploads
have no directory structure, so there is no `references/` folder to speak of on that side.

---

## Keeping the copies current

The skills fetch `digest.html` live, so **a digest update never requires reinstalling anything**.
That's the whole reason it isn't bundled.

You only need to reinstall when a `SKILL.md` or `github-sync.md` changes here. After editing
those, rebuild the bundles and re-upload:

```bash
bash scripts/build-skills.sh
```

The build is reproducible — identical content produces identical zips, so `git status` stays
clean if nothing actually changed.
