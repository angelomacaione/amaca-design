#!/usr/bin/env python3
"""
Amaca release gate — the git half of a release, made mechanical.

    python3 release/release.py preflight      # on the release branch, before the PR
    python3 release/release.py tag CODE       # on main, after the PR is merged
    python3 release/release.py bust           # after the last CSS edit: ?v = content hash

Why this exists. On 2026-09-23 v4.1.0 shipped through nine avoidable steps:
a release branch based on history that main had squashed away (a PR full of
false conflicts), a branch named exactly like the tag (every `git push v4.1.0`
refused as ambiguous), a push to a protected main, a commit made on a detached
HEAD, a tag published before the content was complete and moved three times.
None of it was a design mistake; all of it was the release procedure living
in chat instead of in a tool. Every failure below is one of those, turned into
a refusal with the fix printed next to it.

The contract between preflight and tag is the TREE. preflight records the
tree id of what was reviewed; tag refuses to tag a main whose tree differs.
Squash, merge commit or rebase all produce the same tree from a branch that
contains origin/main, so the check holds whatever button is pressed on GitHub
— and anything that slipped in after the review is caught, not tagged.

Stdlib only; runs on the macOS system python3. Never pushes a branch, never
merges: those stay human.
"""
import datetime
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATE = os.path.join(ROOT, ".release", "reviewed")
TAG_RE = re.compile(r"^v\d+\.\d+\.\d+$")


def git(*args, check=True):
    r = subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True)
    if check and r.returncode != 0:
        fail(f"git {' '.join(args)} failed:\n{r.stderr.strip()}")
    return r.stdout.strip()


def fail(msg, fix=None):
    print(f"\n  STOP  {msg}")
    if fix:
        print(f"  FIX   {fix}")
    print()
    sys.exit(1)


def ok(msg):
    print(f"  ok    {msg}")


def spec():
    text = open(os.path.join(ROOT, "DESIGN.md"), encoding="utf-8").read()
    v = re.search(r"^version:\s*(\S+)", text, re.M)
    d = re.search(r"^updated:\s*(\S+)", text, re.M)
    head = re.search(r"^## Changelog\s*\n+(### .+)$", text, re.M)
    if not v or not d:
        fail("DESIGN.md frontmatter has no version or updated field")
    return v.group(1), d.group(1), (head.group(1) if head else "(no changelog heading found)")


def today_rome():
    try:
        from zoneinfo import ZoneInfo
        return datetime.datetime.now(ZoneInfo("Europe/Rome")).date().isoformat()
    except Exception:
        return datetime.date.today().isoformat()


def remote_tag(tag):
    out = git("ls-remote", "origin", f"refs/tags/{tag}", f"refs/tags/{tag}^{{}}", check=False)
    shas = [l.split()[0] for l in out.splitlines() if l.strip()]
    return shas[-1] if shas else None


def preflight(args):
    print("\n  AMACA — release preflight\n")
    git("fetch", "--prune", "origin")
    ok("fetched origin (stale remote branches pruned)")

    branch = git("rev-parse", "--abbrev-ref", "HEAD")
    if branch == "HEAD":
        fail("you are on a detached HEAD — a commit here belongs to no branch",
             "git checkout -b release/X.Y.Z   (or git checkout main, then start a branch)")
    if branch == "main":
        fail("you are on main — main is protected and only changes through a pull request",
             "git checkout -b release/X.Y.Z")
    tags = set(git("tag", "-l").split())
    if TAG_RE.match(branch) or branch in tags:
        fail(f"branch '{branch}' has the name of a tag — every push and checkout becomes ambiguous",
             f"git branch -m {branch} release/{branch.lstrip('v')}")
    ok(f"on branch {branch}")

    if git("status", "--porcelain"):
        fail("uncommitted changes — the review must see exactly what will be published",
             "commit them (or stash them) and run preflight again")
    ok("working tree clean")

    if subprocess.run(["git", "merge-base", "--is-ancestor", "origin/main", "HEAD"], cwd=ROOT).returncode != 0:
        fail("this branch does not contain origin/main — the PR will show conflicts (squashed history)",
             "git merge origin/main   then resolve, run the harness, and run preflight again")
    ok("branch contains origin/main — the PR will merge clean")

    version, updated, heading = spec()
    tag = f"v{version}"
    if not heading.startswith(f"### {tag} "):
        fail(f"the top changelog entry is not {tag}: {heading}")
    ok(f"version {version}, top changelog entry matches")

    today = today_rome()
    if updated != today and "--date-ok" not in args:
        fail(f"DESIGN.md says updated: {updated}, today is {today}",
             "re-stamp the release date, or pass --date-ok if the date is deliberate")
    ok(f"release date {updated}")

    existing = remote_tag(tag)
    if existing and "--retag" not in args:
        fail(f"{tag} is already published on {existing[:7]} — this would rewrite a shipped release",
             "ship a new version, or pass --retag only if moving the tag is a decision already taken")
    ok(f"{tag} not yet published" if not existing else f"{tag} published — RETAG explicitly requested")

    r = subprocess.run([sys.executable, "verify-ds.py"], cwd=ROOT, capture_output=True, text=True)
    last = [l for l in r.stdout.splitlines() if "checks pass" in l]
    if r.returncode != 0:
        print(r.stdout[-3000:])
        fail("verify-ds.py is not green")
    ok(f"harness: {last[-1].strip() if last else 'green'}")

    tree = git("rev-parse", "HEAD^{tree}")
    commits = git("log", "--oneline", "origin/main..HEAD")
    files = git("diff", "--stat", "origin/main...HEAD")
    os.makedirs(os.path.dirname(STATE), exist_ok=True)
    with open(STATE, "w") as f:
        f.write(f"{tag}\n{tree}\n{branch}\n{today}\n")

    code = tree[:7]
    print(f"""
  ──────────────────────────────────────────────────────────────────────
  WHAT YOU ARE ABOUT TO PUBLISH — {tag}  ({updated})
  {heading}

  commits since main:
{chr(10).join('    ' + l for l in commits.splitlines()) or '    (none)'}

  files:
{chr(10).join('    ' + l for l in files.splitlines()[-40:])}

  REVIEW CODE  {code}
  ──────────────────────────────────────────────────────────────────────

  Before the PR, both of you look at the review sheet (rendered sections,
  changelog, this list) and agree it is what ships. Then:

    1. git push -u origin {branch}
    2. open the PR, merge it (any merge button)
    3. python3 release/release.py tag {code}

  The tag step refuses if main's tree is not the tree reviewed here.
""")


def tag_cmd(args):
    print("\n  AMACA — release tag\n")
    if not os.path.exists(STATE):
        fail("no review on record — run preflight on the release branch first")
    tag, tree, branch, day = open(STATE).read().split("\n")[:4]
    code = next((a for a in args if not a.startswith("--")), None)
    if code != tree[:7]:
        fail("the review code does not match the one preflight printed",
             "copy the REVIEW CODE from the preflight output — it is how you confirm you saw it")

    if git("rev-parse", "--abbrev-ref", "HEAD") != "main":
        git("checkout", "main")
    if git("status", "--porcelain"):
        fail("uncommitted changes on main", "git stash, then run tag again")
    git("pull", "--ff-only", "origin", "main")
    ok("main up to date with origin")

    now = git("rev-parse", "HEAD^{tree}")
    if now != tree:
        fail(f"main's content is not what was reviewed (tree {now[:7]}, reviewed {tree[:7]})",
             "something merged that was not in the review — run preflight again on a branch with it, review, then tag")
    ok("main is exactly the reviewed tree")

    version = tag[1:]
    v, _, _ = spec()
    if v != version:
        fail(f"DESIGN.md on main says {v}, the review was for {version}")

    existing = remote_tag(tag)
    head = git("rev-parse", "HEAD")
    if existing and existing != head and "--retag" not in args:
        fail(f"{tag} is already published on {existing[:7]}",
             "pass --retag only if moving the published tag is a decision already taken")
    git("tag", "-f", "-a", tag, "-m", f"{tag}")
    if existing:
        git("push", "-f", "origin", f"refs/tags/{tag}")
    else:
        git("push", "origin", f"refs/tags/{tag}")
    if remote_tag(tag) != head:
        fail("the tag did not land on main's head — check GitHub before announcing anything")
    ok(f"{tag} published on {head[:7]}")

    if branch and branch != "main":
        git("branch", "-D", branch, check=False)
        git("push", "origin", "--delete", branch, check=False)
        ok(f"release branch {branch} removed (local and remote)")
    git("fetch", "--prune", "origin")
    os.remove(STATE)
    print(f"\n  Released {tag}. The review record is cleared.\n")


# --- cache-bust -------------------------------------------------------------
# v4.2.0 changed components.css and tokens.css and shipped them under the same
# ?v=82 / ?v=27 as v4.1.0: a returning visitor kept the old hover ring, and one
# holding the old tokens.css with the new components.css had the three
# --ring-* tokens undefined, so every focus ring vanished. A hand-bumped counter
# had already stood still once for four commits. The ?v is now the file's own
# content hash: it changes exactly when the bytes do, and verify-ds.py check 40
# recomputes it, so a stale one cannot ship. Touches only the HTML; never git.
# Only a <link> tag loads a stylesheet; the changelog quotes old keys as text (v4.3.0).
LINK_RE = re.compile(r'(<link\b[^>]*\bhref="(?:\./)?styles/([\w.-]+\.css))(?:\?v=[^"]*)?"')
SKIP_DIRS = {".git", ".release", "Claude outputs", "node_modules"}


def css_hash(name):
    import hashlib
    with open(os.path.join(ROOT, "styles", name), "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()[:8]


def site_html():
    for d, dirs, files in os.walk(ROOT):
        dirs[:] = [x for x in dirs if x not in SKIP_DIRS]
        for f in files:
            if f.endswith(".html"):
                yield os.path.join(d, f)


def bust(args):
    print("\n  AMACA — cache-bust\n")
    changed = 0
    for path in site_html():
        text = open(path, encoding="utf-8").read()

        def sub(m):
            name = m.group(2)
            if not os.path.exists(os.path.join(ROOT, "styles", name)):
                fail(f"{os.path.relpath(path, ROOT)} loads styles/{name}, which does not exist")
            return f'{m.group(1)}?v={css_hash(name)}"'
        new = LINK_RE.sub(sub, text)
        if new != text:
            with open(path, "w", encoding="utf-8") as fh:
                fh.write(new)
            changed += 1
        for m in LINK_RE.finditer(new):
            ok(f"{os.path.relpath(path, ROOT)}: styles/{m.group(2)}?v={css_hash(m.group(2))}")
    print(f"\n  {changed} file(s) rewritten.\n")


if __name__ == "__main__":
    cmds = {"preflight": preflight, "tag": tag_cmd, "bust": bust}
    if len(sys.argv) < 2 or sys.argv[1] not in cmds:
        print(__doc__)
        sys.exit(2)
    cmds[sys.argv[1]](sys.argv[2:])
