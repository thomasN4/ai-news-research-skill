#!/usr/bin/env bash
# Assemble the installable skill bundles in dist/ from skills/.
#
# Each bundle gets the agent's own SKILL.md plus the shared github-sync.md. The digest
# is deliberately not bundled — both skills fetch it from the raw URL — so a digest
# push never invalidates these zips. Rerun this only when a SKILL.md or github-sync.md
# changes.
#
# The archive root must be a folder named ai-news-research, matching the `name:` in the
# frontmatter, or Claude's skill uploader rejects it.

set -euo pipefail

repo="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
mkdir -p "$repo/dist"

for agent in claude grok; do
  stage="$(mktemp -d)"
  trap 'rm -rf "$stage"' EXIT

  mkdir -p "$stage/ai-news-research/references"
  cp "$repo/skills/$agent/ai-news-research/SKILL.md" "$stage/ai-news-research/"
  cp "$repo/skills/common/references/github-sync.md" "$stage/ai-news-research/references/"

  # zip records mtimes, so without this a rebuild produces different bytes for
  # identical content and dirties dist/ on every run. Fixed stamp = reproducible zip.
  find "$stage" -exec touch -t 202001010000 {} +

  # Extension is per-agent and load-bearing. Claude's bundle is a skill: the web app
  # only offers its "save skill" button for a `.skill` file, including when an agent
  # hands the bundle back in-chat at the end of the github-sync.md procedure. Grok has
  # no skill uploader — its bundle is just a download container the user unzips — so
  # naming it `.skill` would imply an install path that doesn't exist. Both are
  # ordinary zip archives; only the name differs.
  case "$agent" in
    claude) ext=skill ;;
    *)      ext=zip   ;;
  esac

  out="$repo/dist/ai-news-research-$agent.$ext"
  rm -f "$out"                       # rebuild from scratch so deletions don't linger
  # zip -r walks the staging directory in filesystem order, which differs between
  # machines. That reordered entries — and so changed the archive bytes — even with
  # mtimes pinned, dirtying dist/ for whoever rebuilt next. Feed zip an explicitly
  # sorted list instead; -@ reads paths from stdin and preserves the order given.
  ( cd "$stage" && find ai-news-research | LC_ALL=C sort | zip -qX "$out" -@ )

  rm -rf "$stage"
  trap - EXIT
  printf 'built %s (%s)\n' "${out#"$repo"/}" "$(du -h "$out" | cut -f1)"
done
