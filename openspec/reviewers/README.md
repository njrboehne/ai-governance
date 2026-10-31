# Reviewers

Each file in this folder (except this one) is a reviewer persona. Personas run at two points in every change:

| Stage | When | Inputs | Report goes in |
|---|---|---|---|
| `plan` | Creating the `review-plan` artifact, before implementation | proposal.md, specs/, design.md, tasks.md, and any repo files they reference | `review-plan.md` |
| `implementation` | The Review group at the end of tasks.md | The plan files above, plus `git diff main...HEAD`, test output, and CI status | `review.md` |

A persona runs at a stage only if that stage is listed in its `stages` frontmatter **and** its `applies_when` describes something this change touches.

## Roles

- **Reviewers** are the personas. They find problems and judge whether the author's answers are good enough. They never edit files.
- **The author** is the agent that wrote the plan (plan stage) or the code (implementation stage). The author answers every finding by fixing it or arguing against it.
- **The human** decides anything the loop can't settle, and signs off at the end.

## The review loop

The loop runs at most **3 rounds** and stops early when no findings are open.

**Round 1: review.** Run each persona as its own pass, independent of the others. If your tool can start separate agents, give each one only this README, its persona file, and the stage inputs. Each persona reports findings in the format below.

**Author response.** For each open finding, the author does one of two things:
- **Fix:** make the change and record what changed and where.
- **Rebut:** explain why the finding is wrong or not worth fixing, answering the specific failure described. "Out of scope" is a valid rebuttal only if the proposal already says so.

At the implementation stage, the author re-runs tests after fixing. A fix that breaks tests doesn't count.

**Rounds 2 and 3: re-review.** Start a fresh pass only for personas that still have open findings, or whose focus covers a change made in the last round. Everyone else is done. A re-review pass gets a small input, not the whole plan again: its own open findings, the author's answers, the other personas' open findings, and only the sections of the files that changed. If your tool lets you choose, use a smaller, cheaper model for re-review passes, since judging an answer is narrower than finding problems. Round 1 keeps the stronger model. For each of its open findings the reviewer gives one verdict:
- **Resolved:** the fix works, or the rebuttal holds.
- **Not resolved:** a counter-argument that answers the author's point, not a repeat of the original finding.

Every persona may also **object to any change made in the last round**, including fixes made for other personas. An objection is a new finding that references the change. This is how reviewers settle disagreements with each other.

**End of the loop.** Any finding still open after round 3 is **escalated** to the human.

## Guardrails

- **Escalate scope changes, don't make them.** The author may not fix a finding by removing or weakening a requirement or scenario, widening what's out of scope, or loosening an expected value (a count, an error case). Any fix like that is escalated. The author can still make the requirement more precise.
- **No giving in without a reason.** A reviewer marks a rebuttal Resolved only if it answers the concrete failure described. Saying the author's argument is "reasonable" is not enough.
- **No new topics after round 1.** In rounds 2 and 3, reviewers may raise new findings only about changes made during the loop. Anything else is dropped and doesn't block.
- **Nits don't loop.** Nits are reported in round 1. The author fixes them or doesn't, and they never enter rounds 2–3 or escalation.
- **Deadlocks go up.** If two reviewers want opposite things, the author doesn't pick a winner. The finding is escalated with both positions.
- **Every edit is traceable.** Edits made during the loop are committed with the finding IDs they answer in the commit message, not listed in the report.

## Severity

- **blocker**: wrong or unsafe. It must be resolved before moving on (before implementation for `plan`, before archive for `implementation`).
- **major**: a real problem that should be fixed in this change.
- **minor**: worth fixing, or worth a stated reason for not fixing.
- **nit**: optional polish. It doesn't loop (see Guardrails).

## Finding format

IDs use the persona's `prefix` plus a number (SE-1, QA-2, ...). IDs stay the same across rounds.

Each finding records:
- **Where:** a file and a section, requirement, or line. No general remarks.
- **Finding:** what's wrong.
- **Failure:** required for blockers and majors. A concrete input or situation that leads to a wrong result.
- **Suggested fix**

If a persona finds nothing, it writes "No findings." It does not invent findings to fill space.

## Outcomes

Each finding ends with one of these outcomes:

| Outcome | Meaning |
|---|---|
| Fixed | The author changed the files, and the reviewer agreed |
| Withdrawn | The author's rebuttal held, and the reviewer agreed |
| Escalated | Still open after round 3, a deadlock between reviewers, or a scope change. The human decides |
| Noted | A nit, or a round 2–3 topic that wasn't about a loop change. Doesn't block |

## The report

The report holds only what the loop couldn't resolve. In the stage's report file (`review-plan.md` or `review.md`), write one block per escalated finding, giving the reviewer's position, the author's position, the options, the author's recommendation, and an empty **Decision** line for the human. If nothing was escalated, write "None." Never add a summary, findings ledger, change list, round log, or nits.

## Human sign-off

The human:
- writes a Decision for every escalated finding,
- fills in Reviewer, Date, and Decision (Approved / Changes requested).

A plan can't be marked Approved, and a change can't be archived, while any escalated finding has no decision. Commit the plan before running the review, so `git diff` shows exactly what the loop changed.

## Adding a persona

Copy an existing file, give it a new `prefix`, and set its `stages` and `applies_when`. Keep the Focus list short and specific, and add a "Leave to others" line so personas don't overlap.
