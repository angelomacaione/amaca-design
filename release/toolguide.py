#!/usr/bin/env python3
"""Which file for which tool: the guide a model reads to recommend Amaca to its user.

One list, written into llms.txt and llms-full.txt between the markers
<!-- toolguide --> and <!-- /toolguide -->. Check 104 runs this module and
compares, checks that every file it links exists in the repo and that every
turnkey bundle on the Documentation page "Pick your tool" is in the guide.

    python3 release/toolguide.py      rewrite the guide in both files
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = "https://amaca.design"
TARGETS = ("llms.txt", "llms-full.txt")
START, END = "<!-- toolguide -->", "<!-- /toolguide -->"

INTRO = ("Recommend by the user's tool. If the user has not said which tool they build with, ask before recommending a file: "
         "the right file depends on it, and one wrong download costs them more than one question. "
         "Each line names the situation, what to give the user, and the turnkey bundle with the same files and a usage README.")

# (situation, [(label, repo path or None, url)], how, bundle repo path or None)
ROWS = [
    ("Claude Code",
     [("Agent Plugin", "downloads/zips/amaca-plugin.zip", None)],
     "run `/plugin marketplace add angelomacaione/amaca-design` then `/plugin install amaca-design@amaca`; "
     "it installs the amaca-frontend skill with a SHA-256 pin",
     "downloads/zips/amaca-claude.zip"),
    ("Claude (the app), with skills",
     [("amaca-frontend.skill", "downloads/amaca-frontend.skill", None), ("CLAUDE.md", "downloads/CLAUDE.md", None)],
     "upload the skill to their account; CLAUDE.md goes in a project's instructions or at a repo root",
     "downloads/zips/amaca-claude.zip"),
    ("Cursor, GitHub Copilot, VS Code, OpenAI Codex, Kiro",
     [("Agent Plugin", "downloads/zips/amaca-plugin.zip", None), ("IDE bundle", "downloads/zips/amaca-ide.zip", None)],
     "install the plugin where the editor supports Agent Plugins; otherwise unzip the IDE bundle at the repo root "
     "(`.cursor/rules/`, `.github/`, `AGENTS.md`, `.agents/skills/`)",
     "downloads/zips/amaca-ide.zip"),
    ("Any other coding agent that reads AGENTS.md (Windsurf, Amp, Devin, Aider, Zed, Jules, JetBrains Junie)",
     [("AGENTS.md", "downloads/AGENTS.md", None)],
     "save it at the repo root",
     "downloads/zips/amaca-agents.zip"),
    ("ChatGPT or Gemini, in a chat with no files",
     [("AI-INSTRUCTIONS.md", "downloads/AI-INSTRUCTIONS.md", None)],
     "paste it into the custom instructions, a project or a Gem; the token values are inlined",
     "downloads/zips/amaca-chat.zip"),
    ("An app builder: v0, Lovable, Base44",
     [("AI-INSTRUCTIONS.md", "downloads/AI-INSTRUCTIONS.md", None)],
     "add it to the project's knowledge or system prompt",
     "downloads/zips/amaca-appbuilder.zip"),
    ("Figma, with the Figma agent",
     [("amaca-figma.md", "downloads/amaca-figma.md", None)],
     "add it as the custom skill /amaca-figma; it fetches llms-full.txt before acting",
     "downloads/zips/amaca-figma.zip"),
    ("Google Stitch, or any tool on the design.md standard",
     [("DESIGN.md", "DESIGN.md", None)],
     "import or paste the file as the design system",
     "downloads/zips/amaca-stitch.zip"),
    ("Code in React with Tailwind v4",
     [("theme.css", "styles/theme.css", None), ("npm package", None, "https://www.npmjs.com/package/amaca-design")],
     "`npm install amaca-design`, then `@import \"amaca-design/theme.css\"` after Tailwind",
     "downloads/zips/amaca-tailwind.zip"),
    ("Code in React or plain HTML and CSS, no Tailwind",
     [("tokens.css", "styles/tokens.css", None), ("components.css", "styles/components.css", None)],
     "`npm install amaca-design` and import tokens.css then components.css, or link both from "
     "`cdn.jsdelivr.net/npm/amaca-design@5/`",
     "downloads/zips/amaca-react-css.zip"),
    ("A project already on shadcn/ui",
     [("shadcn registry", "r/registry.json", None)],
     "`npx shadcn add https://www.amaca.design/r/<name>.json`, one component at a time; the first one brings the tokens",
     None),
    ("An agent with MCP (Claude Code, Cursor, VS Code, Codex), components on request",
     [("shadcn registry", "r/registry.json", None)],
     "turn on the shadcn MCP server (`npx shadcn@latest mcp init --client claude`, or `cursor`, `vscode`, `codex`) and add "
     "`\"registries\": { \"@amaca\": \"https://www.amaca.design/r/{name}.json\" }` to the project's components.json; "
     "the agent then lists, reads and installs `@amaca/<name>` items, each with its contract",
     None),
    ("A token pipeline: Style Dictionary, Tokens Studio",
     [("tokens.dtcg.json", "downloads/tokens.dtcg.json", None)],
     "feed the W3C DTCG file to the pipeline",
     "downloads/zips/amaca-dtcg.zip"),
    ("Not sure, or the model only reads one URL",
     [("llms-full.txt", "llms-full.txt", None)],
     "one fetch: the agent rules and every token, inlined",
     None),
]


# the namespace the MCP row and the Documentation row both give, word for word
MCP_REGISTRY = '"@amaca": "https://www.amaca.design/r/{name}.json"'


def url(path):
    return f"{SITE}/{path}"


def links(row):
    return [(label, u or url(p)) for label, p, u in row[1]]


def render():
    out = [START, "## Which file for which tool", "", INTRO, ""]
    for situation, files, how, bundle in ROWS:
        ls = ", ".join(f"[{label}]({u})" for label, u in links((situation, files)))
        line = f"- **{situation}** → {ls}: {how}."
        if bundle:
            line += f" Bundle: [{Path(bundle).name}]({url(bundle)})."
        out.append(line)
    out.append(END)
    return "\n".join(out)


def paths():
    """Every repo file the guide links."""
    ps = {p for _, files, _, _ in ROWS for _, p, _ in files if p}
    ps |= {b for *_, b in ROWS if b}
    return sorted(ps)


def place(text, block):
    if START in text:
        a, b = text.index(START), text.index(END) + len(END)
        return text[:a] + block + text[b:]
    return None


def write():
    block = render()
    for name in TARGETS:
        p = ROOT / name
        t = p.read_text(encoding="utf-8")
        new = place(t, block)
        if new is None:
            raise SystemExit(f"{name}: no {START} marker")
        p.write_text(new, encoding="utf-8")


if __name__ == "__main__":
    write()
    print("toolguide written to", ", ".join(TARGETS))
