#!/usr/bin/env bash
# Bake the two paste-in download bundles from a SINGLE source.
#
# Dependency: amaca-chat.zip and amaca-appbuilder.zip ship the SAME paste-in
# (AI-INSTRUCTIONS.md, token values inlined). They differ only in the wrapper
# README (audience copy). Edit AI-INSTRUCTIONS.md once, run this script, and the
# change propagates to BOTH bundles — they can never drift.
#
# Usage:  cd downloads && bash build-paste-in-bundles.sh
set -euo pipefail
cd "$(dirname "$0")"

SRC="AI-INSTRUCTIONS.md"
[ -f "$SRC" ] || { echo "missing $SRC"; exit 1; }

build() {
  local zip="$1" readme="$2"
  local stage; stage="$(mktemp -d)"
  cp "$SRC" "$stage/AI-INSTRUCTIONS.md"
  printf '%s' "$readme" > "$stage/README.md"
  rm -f "zips/$zip"
  ( cd "$stage" && zip -q -X "$OLDPWD/zips/$zip" README.md AI-INSTRUCTIONS.md )
  rm -rf "$stage"
  echo "baked zips/$zip"
}

CHAT_README='# Amaca — ChatGPT · Gemini · AI chat (paste-in)
**For** ChatGPT, Gemini, Microsoft Copilot, and any chat AI with no filesystem.
**Use** Paste AI-INSTRUCTIONS.md into the system prompt / custom-instructions / knowledge box. It is self-contained — token values are inlined.
**Verify** Ask for a component: var(--token) + exact brand hex, ≤5% magenta.
**In this bundle** AI-INSTRUCTIONS.md.
**Shared source** Same paste-in as the App builder bundle (amaca-appbuilder.zip) — both baked from AI-INSTRUCTIONS.md via build-paste-in-bundles.sh. Edit the source once; rebuild both.

— Amaca · MIT · https://amaca.design
'

APPBUILDER_README='# Amaca — App builders (paste-in)
**For** Figma Make, v0, Lovable, Base44, Bolt — app builders with no filesystem.
**Use** Paste AI-INSTRUCTIONS.md into the builder’s instructions / knowledge box. Keep the prompt brand-neutral (describe the screen, not a mood); let the tokens carry the look.
**Verify** Generated UI uses the magenta primary only on the CTA, obsidian everywhere else.
**In this bundle** AI-INSTRUCTIONS.md.
**Shared source** Same paste-in as the AI chat bundle (amaca-chat.zip) — both baked from AI-INSTRUCTIONS.md via build-paste-in-bundles.sh. Edit the source once; rebuild both.

— Amaca · MIT · https://amaca.design
'

build "amaca-chat.zip"       "$CHAT_README"
build "amaca-appbuilder.zip" "$APPBUILDER_README"
echo "done — both bundles in sync from $SRC"
