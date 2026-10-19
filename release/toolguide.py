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
    ("Any MCP client that adds a server by URL: Claude (a custom connector), Claude Code, Cursor, VS Code",
     [("Amaca MCP server", None, "https://www.amaca.design/mcp")],
     "add `https://www.amaca.design/mcp` as a remote MCP server; in Claude Code, "
     "`claude mcp add --transport http amaca https://www.amaca.design/mcp`, or install the Agent Plugin, which brings it "
     "with the skill. No key and nothing to install: "
     "the agent lists the components, reads one with its contract and CSS, the tokens, a section of DESIGN.md and this guide, "
     "and checks the code it wrote against the system (check_compliance)",
     None),
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
     "add it to the project's knowledge or system prompt; where the builder takes files, add theme.css as the Tailwind foundation",
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
    ("A token pipeline: Style Dictionary, Tokens Studio",
     [("tokens.dtcg.json", "downloads/tokens.dtcg.json", None)],
     "feed the W3C DTCG file to the pipeline",
     "downloads/zips/amaca-dtcg.zip"),
    ("Not sure, or the model only reads one URL",
     [("llms-full.txt", "llms-full.txt", None)],
     "one fetch: the agent rules and every token, inlined",
     None),
]


# the remote MCP server (api/mcp.js, served at /mcp by a rewrite in vercel.json):
# the first guide row, the card that opens Documentation and the Claude Code plugin
# manifest give this URL, word for word. v5.2.0: it is the only MCP Amaca presents;
# the shadcn MCP route is gone from the site and the guide (r/ stays, for `npx shadcn add`).
MCP_SERVER = "https://www.amaca.design/mcp"


# § 03.1 How to install: what each step must name, so the site and llms.txt recommend the same file
STEPS = {
    "01": ["amaca-frontend.skill", "/plugin install amaca-design@amaca"],
    "02": ["amaca-figma.md"],
    "03": ["DESIGN.md"],
    "04": ["amaca-plugin.zip", "amaca-ide.zip"],
    "05": ["AI-INSTRUCTIONS.md"],
    "06": ["AI-INSTRUCTIONS.md"],
    "07": ["AI-INSTRUCTIONS.md"],
    "08": ["AI-INSTRUCTIONS.md", "theme.css"],
    "09": ["npm install amaca-design"],
    "10": ["npx shadcn add"],
}


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
