#!/usr/bin/env bash
# Bake the Agent Plugin bundle from a SINGLE source: amaca-frontend.skill.
#
# The package is DUAL by construction — one directory, two manifests, one skill:
#
#   amaca-design/
#   ├── plugin.json                 Agent Plugins 1.0  (Cursor, Codex, Copilot, VS Code, Kiro)
#   ├── .claude-plugin/plugin.json  Claude Code
#   ├── skills/amaca-frontend/      the skill, verbatim from amaca-frontend.skill
#   ├── README.md
#   └── LICENSE
#
# The two manifests live at different paths and never collide: Claude Code reads
# .claude-plugin/plugin.json and does not see the root plugin.json; Agent Plugins
# clients read the root one and ignore the dot-directory. Verified 2026-08-17
# against claude 2.1.229 — `claude plugin validate --strict` passes clean.
#
# Two rules this script exists to enforce, both learned the hard way:
#   1. The skill is copied VERBATIM from amaca-frontend.skill. It is never
#      re-authored here, so the plugin and the standalone skill cannot drift.
#   2. NO CLAUDE.md at the plugin root. Claude Code warns on it and --strict
#      fails: "CLAUDE.md at the plugin root is not loaded as project context."
#   3. NO package.json + lockfile at the plugin root, ever. Claude Code would
#      run `npm ci` / `bun install` on install, and it cannot be turned off.
#
# The spec ships INSIDE the skill (skills/amaca-frontend/DESIGN.md), not at the
# package root — unlike amaca-ide.zip, whose root IS the user's repo. A plugin
# root is an install directory nobody browses, so the spec belongs where the
# skill reads it. One copy, one place.
#
# Usage:  cd downloads && bash build-plugin-bundle.sh
set -euo pipefail
cd "$(dirname "$0")"

SRC="amaca-frontend.skill"
OUT="zips/amaca-plugin.zip"
PLUGIN_NAME="amaca-design"
SKILL_NAME="amaca-frontend"

[ -f "$SRC" ] || { echo "missing $SRC — bake the skill first"; exit 1; }
[ -f "../DESIGN.md" ] || { echo "missing ../DESIGN.md"; exit 1; }

# The version is read from the spec, never typed here: one version, one source.
VERSION="$(sed -n 's/^version:[[:space:]]*//p' ../DESIGN.md | head -1)"
[ -n "$VERSION" ] || { echo "could not read version from ../DESIGN.md"; exit 1; }

stage="$(mktemp -d)"
root="$stage/$PLUGIN_NAME"
mkdir -p "$root/skills" "$root/.claude-plugin"

# 1 — the skill, verbatim
unzip -q "$SRC" -d "$stage/_skill"
[ -d "$stage/_skill/$SKILL_NAME" ] || { echo "$SRC does not contain $SKILL_NAME/"; exit 1; }
cp -R "$stage/_skill/$SKILL_NAME" "$root/skills/$SKILL_NAME"
rm -rf "$stage/_skill"

# the directory name must equal the frontmatter name — Agent Plugins discovers by
# directory, and no external linter checks this (verified: claude plugin validate
# passes on a mismatch). Check it here, at the only moment it can be caught.
fm_name="$(sed -n 's/^name:[[:space:]]*//p' "$root/skills/$SKILL_NAME/SKILL.md" | head -1)"
[ "$fm_name" = "$SKILL_NAME" ] || {
  echo "skill frontmatter name is '$fm_name' but the directory is '$SKILL_NAME'"; exit 1; }

# 2 — the Agent Plugins 1.0 manifest. Schema is CLOSED: only the ten permitted
# top-level fields, and `author` may carry only name/email/url. A malformed
# optional field is fatal; an absent one is not. When in doubt, omit.
cat > "$root/plugin.json" <<JSON
{
  "\$schema": "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json",
  "name": "$PLUGIN_NAME",
  "version": "$VERSION",
  "description": "Amaca design system — token-only rules for AI agents, across HTML/CSS, React (Tailwind v4 @theme) and Figma Variables.",
  "author": { "name": "Angelo Macaione", "url": "https://amaca.design" },
  "homepage": "https://amaca.design",
  "repository": "https://github.com/angelomacaione/amaca-design",
  "license": "MIT",
  "keywords": ["design-system", "design-tokens", "amaca", "tailwind", "figma"]
}
JSON

# 3 — the Claude Code manifest. Schema is OPEN (unknown fields are warnings),
# but a recognized field with the wrong type stops the plugin from loading.
cat > "$root/.claude-plugin/plugin.json" <<JSON
{
  "\$schema": "https://json.schemastore.org/claude-code-plugin-manifest.json",
  "name": "$PLUGIN_NAME",
  "version": "$VERSION",
  "description": "Amaca design system — token-only rules for AI agents, across HTML/CSS, React (Tailwind v4 @theme) and Figma Variables.",
  "author": { "name": "Angelo Macaione", "url": "https://amaca.design" },
  "homepage": "https://amaca.design",
  "repository": "https://github.com/angelomacaione/amaca-design",
  "license": "MIT",
  "keywords": ["design-system", "design-tokens", "amaca", "tailwind", "figma"]
}
JSON

cp ../LICENSE "$root/LICENSE"

cat > "$root/README.md" <<'MD'
# Amaca — Agent Plugin

One package, two manifests, one skill. The `amaca-frontend` skill installs on
Claude Code through `.claude-plugin/plugin.json`, and on every Agent Plugins 1.0
client — Cursor, OpenAI Codex, GitHub Copilot, VS Code, Kiro — through the
`plugin.json` at the root. Same file, no rewrites.

## Install

**Claude Code** — add this repo as a plugin marketplace, then install:

    /plugin marketplace add angelomacaione/amaca-design
    /plugin install amaca-design@amaca

**Agent Plugins 1.0 clients** — install from your client's plugin UI or catalog,
pointing at this package.

**By hand, anywhere** — unpack `skills/amaca-frontend/` into the skills path your
tool reads: `.agents/skills/` (vendor-neutral, read by Cursor 2.4+ and Codex),
`.claude/skills/`, or `.cursor/skills/`.

## Then

    build a pricing card with Amaca

The skill reads `DESIGN.md` first, every time, and generates token-only output —
`var(--magenta-500)`, never a raw hex. It self-audits before handing back.

## What's inside

    plugin.json                  Agent Plugins 1.0 manifest
    .claude-plugin/plugin.json   Claude Code manifest
    skills/amaca-frontend/       the skill: SKILL.md + DESIGN.md + HTML/REACT/FIGMA.md + tokens

The spec lives inside the skill, in one copy. On conflict with the published
repo, the repo wins — the bundled copy is a frozen offline fallback and the
version pin.

— Amaca · MIT · https://amaca.design
MD

# Deterministic bake: every entry carries the release date, so identical content
# always produces identical bytes. Without this the digest changes on every run,
# and a SHA-256 pin that churns for no reason is not an integrity claim — it is
# noise that teaches people to ignore it.
STAMP="$(sed -n 's/^updated:[[:space:]]*//p' ../DESIGN.md | head -1 | tr -d '-')0000"
find "$root" -exec touch -t "$STAMP" {} +

# Zip into the staging area, then write the bytes over the target. Writing in
# place would need to delete first, and the published tree may sit on a mount
# that allows writes but not unlinks — this way the bake works anywhere.
( cd "$stage" && zip -q -X -r "$stage/_out.zip" "$PLUGIN_NAME" -x '*.DS_Store' )
cat "$stage/_out.zip" > "$OUT"
rm -rf "$stage"

echo "baked $OUT — plugin $PLUGIN_NAME v$VERSION"
echo "sha256: $(shasum -a 256 "$OUT" | cut -d' ' -f1)"
