#!/usr/bin/env bash
# Re-sync every embedded copy of a repo file inside every download bundle.
#
# Ten bundles carry copies of DESIGN.md, the token files and the rules files.
# Until v3.5.0 the only thing keeping them current was the release checklist
# saying "re-bake last" — an instruction, not a guard. It failed twice in one
# session: a DESIGN.md edit staled five zips at once, and check 24 found
# tokens.dtcg.json inside amaca-dtcg.zip already 248 bytes behind, shipped that
# way and unnoticed.
#
# This script replaces members by BASENAME against the repo's canonical copy,
# preserving each bundle's own structure. It does not know what a bundle is for
# and does not need to: if a bundle carries a file this repo owns, that file is
# the repo's, verbatim.
#
# Run it LAST, after the final edit — then `python3 verify-ds.py` (check 24)
# proves it worked instead of taking your word for it.
#
# Usage:  cd downloads && bash refresh-bundles.sh
set -euo pipefail
cd "$(dirname "$0")"

# basename -> canonical path in this repo
declare -A SRC=(
  ["DESIGN.md"]="../DESIGN.md"
  ["tokens.css"]="../styles/tokens.css"
  ["theme.css"]="../styles/theme.css"
  ["tokens.dtcg.json"]="tokens.dtcg.json"
  ["AGENTS.md"]="AGENTS.md"
  ["CLAUDE.md"]="CLAUDE.md"
  ["AI-INSTRUCTIONS.md"]="AI-INSTRUCTIONS.md"
  ["amaca-figma.md"]="amaca-figma.md"
  ["amaca-frontend.skill"]="amaca-frontend.skill"
)

# The release date, as a zip timestamp — read from the spec, never typed here.
STAMP="$(sed -n 's/^updated:[[:space:]]*//p' ../DESIGN.md | head -1 | tr -d '-')0000"

refresh() {  # $1 = archive path
  local arch="$1" touched=0
  local stage; stage="$(mktemp -d)"
  unzip -q "$arch" -d "$stage"
  while IFS= read -r -d '' f; do
    local base; base="$(basename "$f")"
    local src="${SRC[$base]:-}"
    [ -n "$src" ] || continue
    [ -f "$src" ] || continue
    cmp -s "$src" "$f" && continue
    cp "$src" "$f"
    echo "    ↻ ${f#$stage/}"
    touched=1
  done < <(find "$stage" -type f -print0)

  if [ "$touched" -eq 1 ]; then
    # Deterministic: stamp every entry with the release date so identical content
    # yields identical bytes, and the published digests stop churning per bake.
    find "$stage" -exec touch -t "$STAMP" {} +
    ( cd "$stage" && zip -q -X -r "$stage/_out.zip" . -x '_out.zip' -x '*.DS_Store' )
    # write the bytes over the target instead of replacing the file: the tree may
    # live on a mount that allows writes but not unlinks.
    cat "$stage/_out.zip" > "$arch"
    echo "  refreshed $arch"
  else
    echo "  ok        $arch"
  fi
  rm -rf "$stage"
}

# The skill goes first: two bundles embed it, so refreshing it before them lets
# the same pass carry the new copy outward instead of needing a second run.
echo "skill:"
refresh "amaca-frontend.skill"
cmp -s amaca-frontend.skill amaca-frontend.zip || {
  cat amaca-frontend.skill > amaca-frontend.zip
  echo "  synced    amaca-frontend.zip (twin of the .skill)"
}

echo "bundles:"
for z in zips/*.zip; do
  # amaca-plugin.zip is not refreshed in place — it is BAKED from the skill, and
  # baking it here would produce a second, divergent way to build the same file.
  [ "$z" = "zips/amaca-plugin.zip" ] && continue
  refresh "$z"
done

echo "plugin:"
bash build-plugin-bundle.sh | sed 's/^/  /'

# Publish a digest for every bundle, not just the one the marketplace pins.
# Agent Plugins puts provenance and trust outside its contract, so integrity is
# the publisher's job — and a claim made for one bundle and not the others is
# not much of a claim. Check 24 recomputes these, so they cannot go stale.
echo "digests:"
( cd zips && shasum -a 256 *.zip > SHA256SUMS ) && echo "  wrote zips/SHA256SUMS"

echo
echo "now update the sha256 pin in ../.claude-plugin/marketplace.json, then run:"
echo "  python3 ../verify-ds.py"
