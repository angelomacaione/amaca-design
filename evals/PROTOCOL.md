# Model fidelity protocol

How faithfully does a model design with Amaca? This protocol answers that question the same way every time, so a score from one run can be compared with a score from another.

It replaces the figures in § 03.3 of the site (8.5/10 overall, 9.5/10 on gap handling, N=4). Those figures have no scenarios, prompts or rubric on record, so nobody can reproduce them. Until runs under this protocol replace them, read them as an unverified claim.

**What it measures:** fidelity to the contract, meaning `DESIGN.md` and the closed lists in `styles/tokens.css`. It doesn't measure taste.

**What it does not measure:** whether the design system is coherent. `verify-ds.py` checks that, at release. This protocol checks what a model produces from the system.

---

## 1 · The cell

One run sits in a cell named by four variables. Record all four, or the run doesn't count.

| Variable | Values | Recorded as |
|---|---|---|
| **Model** | The identifier the runtime shows. Never a marketing name guessed from memory | `model` |
| **Runtime** | Claude Code, Cowork, Cursor, ChatGPT (Custom GPT), Gemini (Gem), Figma, Stitch… | `runtime` |
| **Delivery format** | `F1` skill bundle (`amaca-frontend.skill`, or the plugin) · `F2` raw `DESIGN.md` in context · `F3` `downloads/AI-INSTRUCTIONS.md` pasted as the system prompt · `F4` `amaca-figma.md` (Figma target only) | `format` |
| **Spec** | The `version:` line of `DESIGN.md`, plus the sha256 of the bundle zip when the format is F1 | `spec`, `bundle_sha256` |

Hold three of the four fixed and vary one. A table that changes model and format at the same time can't tell you which one caused the difference.

## 2 · Run discipline

1. **Fresh session per run.** No memory, no earlier turns, no project files except the ones the format puts in place.
2. **Verbatim prompt.** Paste the scenario prompt from [`scenarios.md`](scenarios.md) exactly as written, with no rewording and no hints.
3. **Scripted follow-ups only.** If the model stops and asks, which is the right move in S3–S5, answer with the follow-up the scenario gives, word for word. Any other turn makes the run invalid.
4. **Three repetitions per cell (k = 3).** Generation isn't deterministic, so one run is an anecdote. Report the mean and the range.
5. **Keep the raw output.** Save the file the model produced, plus the full transcript, under `evals/runs/<run-id>/`. A score with no artifact behind it doesn't count.
6. **Don't fix anything before scoring.** You grade what the model handed over. If the model fixed something after its own verifier pass, that counts in its favour. If you fix it, it doesn't count.

Run id: `YYYY-MM-DD-<model>-<runtime>-<format>`, lowercase, hyphens only. The repetition sits in the filename: `S1-r1.html`, `S1-r1.transcript.md`.

## 3 · Three layers of scoring

### Layer A · deterministic (HTML outputs)

```
python3 evals/score.py evals/runs/<run-id>/S1-r1.html
```

`score.py` runs the bundle's own `scripts/verify-output.py`, the same verifier the skill tells the model to run, against the output. It maps each finding to the law it breaks (§ Law, L1–L9) or to registry closure. The two numbers recorded are:

- **A-pass:** the verifier exits 0, yes or no.
- **A-findings:** the number of findings, broken down by law.

The verifier reads its closed lists from the bundle at run time, so Layer A always grades against the spec version that was shipped. What it can't see without a render: touch-target geometry, contrast, the 85/10/5 budget by area, and composite values reproduced with missing parts (L5). Layer B covers those.

### Layer B · rubric (every output, graded by a person or a judge model)

Each dimension scores **0** (broken), **1** (partial) or **2** (faithful). A scenario grades only the dimensions it is built to exercise, listed in `scenarios.md`.

| Id | Dimension | 2 means | Source |
|---|---|---|---|
| B1 | **Registry reuse** | Every element is a § 3.0 registry component composed as specified. No new class that restyles a canonical one (the `.pillar` incident) | § 3.0 · skill posture #8 |
| B2 | **Gap handling** | An off-system need is named as a gap, with the three paths (workaround / plan a release / refactor), and nothing is invented. Asking first counts as 2 | § For the AI agent #1 · skill step 5 |
| B3 | **Conflict surfacing** | A request that breaks a law or a principle is named, with the law id or principle, before any code, and a compliant alternative is offered | § For the AI agent #3 · § Law |
| B4 | **Scale discipline** | Every value is on a scale. Composite values (gradients, shadows, font stacks), when materialized, carry every part (count them against `tokens.css`) | L4 · L5 |
| B5 | **Motion grammar** | Durations and easings come from the six and five named. Entrance, exit and state each ride their own easing. Spring is on spatial properties only. Reduced motion is honoured | L7 · L8 · § Motion |
| B6 | **Accessibility floor** | All seven items of § Accessibility hold in the render: persistent labels, color + shape + label, 44×44 targets, no timed dismissal outside the toast's bounded opt-in, and so on | L2 · L9 |
| B7 | **Budget** | Rendered, the screen reads ≥ 85% obsidian, ≤ 10% primary + cyan, ≤ 5% semantic. One primary action per screen | L1 · L3 |
| B8 | **Voice and restraint** | No filler copy, no unrequested sections, no decorative icons, no emoji. Spec register in code comments | § For the AI agent #5 · L6 · § Voice & tone |
| B9 | **Honest grounding** | What the model says it did matches what it did: "I read DESIGN.md", "verifier passed", "all tokens valid" are checked against the output. One false claim scores 0 | § 03.3 performative compliance |

**Blind grading.** The grader sees the output and the transcript with the model, runtime and format removed. Use two graders, or one person and one judge model given this table verbatim. Settle any disagreement of more than one point on a dimension by re-reading the source line the dimension cites. Record both scores and the settled one.

### Layer C · grounding probes

The five questions at the end of `scenarios.md` can only be answered from the spec. Ask them in the same fresh session, after the scenarios. Each one scores 1 or 0. They catch the failure § 03.3 calls *performative compliance*: the model says it read the file, but the reading was shallow. Five quick questions are cheaper than discovering that through a design.

## 4 · Aggregation

For each cell:

- **Fidelity score (/10):** the mean of B1–B9 over the dimensions graded, × 5, averaged over scenarios and repetitions. Report it as `mean (min–max)`.
- **Gap score (/10):** B2 and B3 alone, on S3–S5. This replaces the old 9.5 figure.
- **A-pass rate:** HTML outputs that exit 0, out of the total.
- **Probe score:** out of 5, averaged over repetitions.
- **Hard fails:** the number of runs where an `error`-severity law (L2, L4–L9) was broken *silently*, meaning in the delivered output with no mention of it. Report this beside the score, never folded into it. One silent hard fail matters more than a decimal point of mean.

Write each cell's line into [`RESULTS.md`](RESULTS.md) and link it to its run folder.

## 5 · Tiers

> **Proposal, not yet ratified.** These thresholds are the protocol's first draft. They become canonical when the owner ratifies them, ideally after one round of runs shows whether they separate models in practice.

| Tier | Requires, in one cell at k = 3 |
|---|---|
| **Frontier · recommended** | Fidelity ≥ 8.0 · Gap ≥ 9.0 · A-pass ≥ 2/3 on every HTML scenario · Probes ≥ 4/5 · zero silent hard fails |
| **Lightweight · best-effort** | Fidelity ≥ 6.0 · Gap ≥ 6.0 · Probes ≥ 3/5 · at most one silent hard fail |
| **Not recommended** | Anything below |

The tier belongs to the cell, not to the model. A model that is frontier in Claude Code with F1 can be lightweight in a consumer chat with F3. § 03.3 already says the runtime's file grounding matters, and this table is where that shows up.

## 6 · When to run it

- **At every MAJOR release of the spec**, on the reference cells: the newest frontier model and the newest lightweight model, each in Claude Code with F1 and in one consumer chat with F3. A MAJOR release changes the contract, so earlier scores describe a different system.
- **Before § 03.3 names a model.** A model listed on the site has a run here.
- **When a new delivery format ships** (a new zip in `downloads/`), on one frontier cell.

## 7 · What this protocol does not cover

- **Figma (F4)** is graded on Layer B only, from a screenshot and the node tree. There's no deterministic verifier for a Figma file yet.
- **React output** is graded on Layer B only. The shipped verifier reads HTML. Scenario S8 still checks cross-target drift by hand.
- **Taste.** Two faithful outputs can differ in quality. That is a design review, not a fidelity score.
