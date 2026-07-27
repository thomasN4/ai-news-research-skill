# Syncing the digest to GitHub

Repo: `thomasN4/ai-news-research-skill` (public). Reads need no auth. Writes need a
fine-grained personal access token scoped to this repo alone, with **Contents: Read and
write**. Opening a pull request needs **Pull requests: Read and write** on top of that —
Contents alone gets you a pushed branch and a 403 on the PR itself. Nothing beyond those
two.

## Reading

```bash
curl -sL https://raw.githubusercontent.com/thomasN4/ai-news-research-skill/main/manifest.json
curl -sL https://raw.githubusercontent.com/thomasN4/ai-news-research-skill/main/digest.html
```

`raw.githubusercontent.com` serves a CDN copy that can lag a push by up to ~5 minutes.
If you just wrote and need to confirm, read back through the API instead:
`https://api.github.com/repos/thomasN4/ai-news-research-skill/contents/digest.html`.

## Token handling

- Ask the user to paste the token only at the moment of writing. Don't ask for it
  during read-only work.
- **Never echo it back**, never write it into a file that gets presented to the
  user, never put it in a commit message or a URL query string.
- Pass it via environment variable, not as a command-line argument — arguments are
  visible in process listings.
- The sandbox filesystem resets between sessions, so the token does not persist.
  That is a feature; don't work around it by storing it somewhere durable.
- If it is ever exposed in conversation, tell the user to revoke it at
  GitHub → Settings → Developer settings → Personal access tokens. A fine-grained
  token scoped to one public repo is a small blast radius by design, but revoking
  is still the right move.

### Where the token comes from

The user keeps it in a `.env` file beside their clone — `GH_TOKEN=github_pat_...`,
template in `.env.example` at the repo root, excluded by `.gitignore`. Load it with:

```bash
set -a; . ./.env; set +a
```

That keeps the value out of argv and out of shell history, the same reason the
`read -rs` form below exists. Either is fine; use whichever matches where you are.

In a web chat with no clone, the user can upload `.env` instead of pasting the token.
Source it from wherever the upload landed and never `cat` it. Be straight with them
that uploading and pasting carry the same exposure — the token is in the conversation
either way. What limits the damage is the token's scope (one public repo, Contents
only) and its expiry, not the delivery method.

### If the sandbox can't reach the network

A hosted code sandbox may block outbound HTTPS to `api.github.com`. That shows up as
a connection error from `push.py`, not a 401 or 403 — auth is never reached. Don't
retry it and don't ask for a different token: the token isn't the problem. Fall
through to *"If the user has no token available"* at the bottom of this file, hand
over the files and the commands, and say which one you hit so the user knows the
token is still good.

## Writing

The contents API requires the current blob `sha` of the file being replaced. That
sha is the concurrency control: if the other agent pushed since you read, the PUT
fails with 409 and you must re-pull, re-apply, and retry. Never work around a 409
by dropping the sha — that overwrites their work.

Save this as `push.py`, then run it with the token in the environment:

```python
#!/usr/bin/env python3
"""Push a file to the shared digest repo via the GitHub contents API."""
import base64, json, os, sys, urllib.request, urllib.error

REPO   = "thomasN4/ai-news-research-skill"
BRANCH = "main"
API    = f"https://api.github.com/repos/{REPO}/contents/"


def _req(url, method="GET", payload=None):
    token = os.environ.get("GH_TOKEN")
    if not token:
        sys.exit("GH_TOKEN not set in environment.")
    data = json.dumps(payload).encode() if payload else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("X-GitHub-Api-Version", "2022-11-28")
    with urllib.request.urlopen(req) as r:
        return json.load(r)


def current_sha(path):
    try:
        return _req(f"{API}{path}?ref={BRANCH}")["sha"]
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return None          # new file
        raise


def push(local_path, repo_path, message):
    with open(local_path, "rb") as f:
        content = base64.b64encode(f.read()).decode()
    payload = {"message": message, "content": content, "branch": BRANCH}
    sha = current_sha(repo_path)
    if sha:
        payload["sha"] = sha
    try:
        out = _req(f"{API}{repo_path}", method="PUT", payload=payload)
        print(f"ok {repo_path} -> {out['commit']['sha'][:7]}")
    except urllib.error.HTTPError as e:
        if e.code == 409:
            sys.exit(f"409 conflict on {repo_path}: someone pushed since you read. "
                     "Re-pull, re-apply your changes, retry.")
        sys.exit(f"{e.code} on {repo_path}: {e.read().decode()[:400]}")


if __name__ == "__main__":
    if len(sys.argv) != 4:
        sys.exit("usage: push.py <local_path> <repo_path> <commit_message>")
    push(sys.argv[1], sys.argv[2], sys.argv[3])
```

```bash
# token read from stdin so it never lands in shell history or argv
read -rs GH_TOKEN && export GH_TOKEN

python3 push.py digest.html   digest.html   "digest: extend coverage to 2026-08-15 (claude, rev 8)"
python3 push.py manifest.json manifest.json "manifest: rev 8, coverage-end 2026-08-15"

unset GH_TOKEN
```

## Opening a pull request instead

Grok pushes straight to `main`. Claude works on a branch and opens a PR, so that the
editorial calls — a reworded summary line, a REPORTED item promoted to CONFIRMED — get
seen before they become the shared baseline. The contents API above still works for a
branch, but it makes one commit per file; use git if the commit structure matters.

Push with the token in the environment rather than in the remote URL, which would
persist it to `.git/config`:

```bash
git -c credential.helper='!f(){ echo username=<your-github-username>; echo "password=$GH_TOKEN"; };f' \
    push -u origin <branch>
```

Use the account's own username there. `x-access-token` is the GitHub App convention and a
fine-grained PAT sent that way is rejected with a 403 that reads like a scope problem.

Then open the PR:

```bash
curl -sS -X POST \
  -H "Authorization: Bearer $GH_TOKEN" \
  -H "Accept: application/vnd.github+json" \
  -H "X-GitHub-Api-Version: 2022-11-28" \
  https://api.github.com/repos/thomasN4/ai-news-research-skill/pulls \
  -d '{"title":"...","head":"<branch>","base":"main","body":"..."}'
```

Put `digest.html` and `manifest.json` in the same PR. The `sha` guard from the section
above protects a direct push, not a branch, so re-read the manifest before merging in
case the other agent pushed while the PR sat open.

### Telling 403s apart

| Symptom | Cause |
| --- | --- |
| connection error, auth never reached | sandbox egress blocked — see the section above |
| `Resource not accessible by personal access token` | the token lacks that permission |
| `Permission to ... denied to <user>` from `git push` | same thing, surfaced by git |

`GET /repos/{owner}/{repo}` is no help here: its `permissions` block reports the *user's*
access to the repo, not the token's grants, so it will cheerfully report `push: true` for
a token that cannot push. Nor does a 5000/hour rate limit prove anything beyond the token
being valid — reads of a public repo succeed regardless. The only honest test is
attempting a write. Creating a throwaway ref and deleting it is cheap:

```bash
curl -sS -X POST -H "Authorization: Bearer $GH_TOKEN" \
  https://api.github.com/repos/thomasN4/ai-news-research-skill/git/refs \
  -d '{"ref":"refs/heads/probe","sha":"<main sha>"}'
curl -sS -X DELETE -H "Authorization: Bearer $GH_TOKEN" \
  https://api.github.com/repos/thomasN4/ai-news-research-skill/git/refs/heads/probe
```

## Handing a rebuilt bundle back

If the same session also rebuilt `dist/` — because a `SKILL.md` or this file changed — give the
user `dist/ai-news-research-claude.skill`, not a `.zip` copy. The web app shows its "save skill"
button based on that extension, so a renamed archive silently loses the one-click install even
though the bytes are identical.

## Ordering and consistency

- **Digest first, manifest second.** The manifest is what the other agent checks to
  decide whether to fetch. If the manifest advertises coverage the digest doesn't
  have yet, the other agent skips searches it should have run. The reverse ordering
  fails safe: a digest ahead of its manifest just means one redundant search.
- **Both in the same session.** A half-applied update is worse than no update.
- **Re-read the manifest right before writing**, even if you read it at the start of
  the conversation. Long sessions leave plenty of room for the other agent to push.
- Commit messages: state what changed, which agent wrote it, and the new revision
  number. `git log --oneline digest.html` is the audit trail for who added what.

## If the user has no token available

Write the updated files locally, hand them over, and give the user the two commands
to commit them by hand. Do not silently skip the update — say plainly that the
shared copy is now behind and what its `coverage_end` still says.
