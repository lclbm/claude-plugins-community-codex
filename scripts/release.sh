#!/usr/bin/env bash
# Publish or resume this checkout's verified version before taking another update.
set -euo pipefail
mkdir -p artifacts
version=$(jq -r .version codex-upstream.lock.json)
tag="html-plan-codex-v$version"
zip_path="$(pwd)/artifacts/html-plan-codex-$version.zip"
(cd plugins/html-plan-codex && zip -qr "$zip_path" .)
(cd artifacts && shasum -a 256 "html-plan-codex-$version.zip" > "html-plan-codex-$version.zip.sha256")
if gh release view "$tag" --json isDraft,assets > artifacts/release.json; then
  if jq -e --arg file "html-plan-codex-$version.zip" '.isDraft == false and any(.assets[]; .name == $file) and any(.assets[]; .name == ($file + ".sha256"))' artifacts/release.json; then
    echo "Release already complete: $tag"
    exit 0
  fi
else
  gh release create "$tag" --target "$(git rev-parse HEAD)" --draft --title "HTML Plan for Codex $version" --notes-file README.md
fi
gh release upload "$tag" "$zip_path" "$zip_path.sha256" --clobber
gh release edit "$tag" --draft=false
