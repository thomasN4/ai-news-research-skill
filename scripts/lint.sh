#!/usr/bin/env bash
# Run the same checks locally and in GitHub Actions.
set -euo pipefail

repo="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo"

# Pin the CLI version without adding a Node package to this content repository.
npx --yes markdownlint-cli2@0.23.3
npx --yes html-validate@11.16.2 digest.html index.html
shellcheck scripts/*.sh
python3 scripts/lint-digest.py
python3 -m unittest discover -s tests

printf 'Markdown, HTML, shell scripts, and digest checks passed.\n'
