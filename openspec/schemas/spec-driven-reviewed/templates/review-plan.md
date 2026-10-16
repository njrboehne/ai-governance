# Plan Review

- **Reviewer:** <!-- name of the human who signed off -->
- **Date:** <!-- YYYY-MM-DD -->
- **Decision:** <!-- Approved | Changes requested -->

## Escalated (needs your decision)

<!-- One block per escalated finding, or "None." -->
<!--
### GOV-2 (major): <short title>
- **Why escalated:** unresolved after 3 rounds | reviewer deadlock | scope change
- **Reviewer position:**
- **Author position:**
- **Options:** A) ... B) ...
- **Author recommendation:**
- **Decision:**
-->

## Summary

Rounds run: <!-- 1-3 -->
Reviewer passes: <!-- e.g. R1: 4, R2: 2 (smaller model), R3: 1 -->
Skipped personas: <!-- name: reason, or "None" -->

| Persona | Fixed | Withdrawn | Escalated | Noted |
|---|---|---|---|---|
<!-- one row per persona -->

## Findings ledger

| ID | Severity | Persona | Finding | Rounds | Outcome | Resolution |
|---|---|---|---|---|---|---|
<!-- one row per finding; human may append "Override: <reason>" to Resolution -->

## Changes made during review

<!-- - file: what changed (finding IDs) -->

## Round log

<!-- ### Round 1 / Round 2 / Round 3: one or two lines per finding: finding → author → verdict -->

## Noted for later

<!-- nits and out-of-loop topics, or "None." -->

## Checked (human)
- [ ] Escalated findings each have a Decision
- [ ] Changes made during review match `git diff` and nothing in scope was dropped
- [ ] Every requirement has at least one WHEN/THEN scenario specific enough to write a test from
- [ ] Tasks include a final review group
