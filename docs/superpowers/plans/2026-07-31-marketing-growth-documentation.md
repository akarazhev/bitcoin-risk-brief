# Marketing And Growth Documentation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:executing-plans` to implement this plan task by task.

**Goal:** Publish a founder-executable, evidence-led four-week marketing and growth playbook for the current Bitcoin Risk Brief pilot.

**Architecture:** Keep the work documentation-only. Add one canonical playbook, link it from the existing documentation entry points and Phase 9 roadmap, and record the design and implementation artifacts in the Superpowers index. The playbook must distinguish current product behavior from dependencies tracked in GitHub issues #41-#45.

**Tech Stack:** Markdown, Git, `rg`, existing Bitcoin Risk Brief documentation.

## Global Constraints

- Preserve the current small-pilot boundary and no-financial-advice posture.
- Treat the public web product, waitlist, readiness state, freshness, and methodology v1.1 exactly as documented.
- Do not claim that campaign attribution, alert-specific signup, email sends, or paid access already exist.
- Do not add runtime code, configuration, generated assets, private analytics, raw contacts, or secrets.
- Use English as the primary acquisition language and Russian as the secondary language.
- Keep competitor statements factual, dated, and linked to the reviewed public product pages.

---

### Task 1: Create the canonical marketing and growth playbook

**Files:**

- Create: `docs/marketing-and-growth.md`
- Reference: `docs/pilot-learning-loop.md`
- Reference: `docs/risk-methodology.md`
- Reference: `docs/waitlist.md`
- Reference: `docs/superpowers/specs/2026-07-31-marketing-growth-design.md`

**Step 1: Establish scope and positioning**

Document the playbook status, four-week launch hypothesis, primary and secondary ICP, non-target users, job to be done,
category, positioning statement, main objections and honest responses, and differentiation from Glassnode, CryptoQuant,
BitcoinRisk.net, and manual chart workflows.

**Step 2: Define the message system**

Add a message hierarchy, proof points, EN/RU headline and subheadline variants, current-risk publishing rules, and prohibited claims. Keep all language descriptive of modelled risk rather than predictive of price or prescriptive of allocation.

**Step 3: Define channels and attribution vocabulary**

Specify founder outreach, X, and permission-based Telegram communities as the first three channels. Define one campaign name, a small source allowlist, content tags, and a clear note that issue #45 is required for first-party product analytics while issue #43 is required for an alert-specific CTA.

**Step 4: Define the four-week experiment and scorecard**

Add a week-zero readiness gate, four weekly themes, channel cadence, funnel stages, denominator rules, and numeric strong/continue/adjust/stop criteria for qualified visits, alert-interest leads, repeat-use evidence, feedback conversations, and paid intent.

**Step 5: Add ready-to-use campaign assets**

Include reusable EN/RU landing-page copy, short EN/RU social posts, Telegram/community posts, one-to-one founder outreach
messages, a weekly digest template, a short methodology explainer outline, and a paid-intent interview question. Use
explicit template fields such as `[report date]` instead of ambiguous placeholders.

**Step 6: Add the operator workflow and dependencies**

Define pre-publication checks, an evidence log compatible with the Pilot Learning Loop, privacy rules, the end-of-cycle decision record, and the relationship to GitHub issues #41-#45.

**Step 7: Review the completed file**

Run:

```bash
sed -n '1,660p' docs/marketing-and-growth.md
rg -n "\b[T]BD\b|\b[T]ODO\b|[f]ill in|[i]mplement later|we guarantee|returns are guaranteed" docs/marketing-and-growth.md
```

Expected: all planned sections and assets are present; the ambiguity scan returns no unresolved work or prohibited return claims.

### Task 2: Link the playbook from canonical documentation entry points

**Files:**

- Modify: `README.md`
- Modify: `docs/README.md`
- Modify: `docs/production-roadmap.md`

**Step 1: Add the root documentation link**

Add `Marketing and Growth` beside the other operator-facing documents in the root README documentation list.

**Step 2: Add the documentation-index link**

Add the playbook to `docs/README.md` under Core Documents with a one-sentence description of its ICP, channels, campaign assets, scorecard, and promotion safeguards.

**Step 3: Connect the playbook to Phase 9**

Add the playbook immediately after the Pilot Learning Loop link in Phase 9 of `docs/production-roadmap.md`. Do not mark Phase 9 complete.

**Step 4: Verify every relative target exists**

Run:

```bash
test -f docs/marketing-and-growth.md
rg -n "Marketing and Growth" README.md docs/README.md docs/production-roadmap.md
```

Expected: the file exists and all three canonical entry points contain the link.

### Task 3: Record the documentation artifacts in the Superpowers index

**Files:**

- Modify: `docs/superpowers/README.md`

**Step 1: Add the approved design**

Add `specs/2026-07-31-marketing-growth-design.md` to the specification table as the approved design for issue #44.

**Step 2: Add the completed implementation plan**

Add `plans/2026-07-31-marketing-growth-documentation.md` to the plan table and describe the playbook and documentation-link work as completed after verification.

**Step 3: Verify the archive entries**

Run:

```bash
rg -n "2026-07-31-marketing-growth" docs/superpowers/README.md
```

Expected: one entry for the design and one for the implementation plan.

### Task 4: Perform documentation-only verification and create the local commit

**Files:**

- Verify: `README.md`
- Verify: `docs/README.md`
- Verify: `docs/production-roadmap.md`
- Verify: `docs/marketing-and-growth.md`
- Verify: `docs/superpowers/README.md`
- Verify: `docs/superpowers/plans/2026-07-31-marketing-growth-documentation.md`

**Step 1: Stage and inspect the final diff and whitespace**

Run:

```bash
git add README.md docs/README.md docs/production-roadmap.md docs/marketing-and-growth.md docs/superpowers/README.md docs/superpowers/plans/2026-07-31-marketing-growth-documentation.md
git diff --cached --check
git diff --cached --stat
git diff --cached -- README.md docs/README.md docs/production-roadmap.md docs/marketing-and-growth.md docs/superpowers/README.md docs/superpowers/plans/2026-07-31-marketing-growth-documentation.md
sed -n '1,660p' docs/marketing-and-growth.md
sed -n '1,220p' docs/superpowers/plans/2026-07-31-marketing-growth-documentation.md
```

Expected: only the planned documentation files are staged, both additions appear in the cached diff and direct reads,
and no whitespace errors appear.

**Step 2: Run terminology and boundary checks**

Run:

```bash
rg -n "financial advice|investment advice|readiness|freshness|#4[1-5]|small pilot" docs/marketing-and-growth.md
rg -n "\b[T]BD\b|\b[T]ODO\b|[f]ill in|[i]mplement later" README.md docs/README.md docs/production-roadmap.md docs/marketing-and-growth.md docs/superpowers/README.md docs/superpowers/plans/2026-07-31-marketing-growth-documentation.md
git status --short
```

Expected: trust boundaries and dependencies are explicit, the placeholder scan is empty, and Git shows only the intended documentation changes.

**Step 3: Create the local documentation commit**

Run:

```bash
git commit -m "docs: add marketing growth playbook"
```

Expected: a local commit is created. Do not push or close issue #44 without separate confirmation.
