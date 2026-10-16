# Tasks

## 1. <!-- Task Group Name -->

- [ ] 1.1 <!-- Task description -->
- [ ] 1.2 <!-- Task description -->

## 2. <!-- Task Group Name -->

- [ ] 2.1 <!-- Task description -->
- [ ] 2.2 <!-- Task description -->

## 3. Review <!-- Keep this group last. Renumber if you add implementation groups -->

- [ ] 3.1 Every spec scenario has a passing test; scenario → test mapping recorded in review.md
- [ ] 3.2 CI is green on the branch (ruff check, ruff format --check, pytest)
- [ ] 3.3 Diff read end to end; findings and resolutions recorded in review.md
- [ ] 3.4 `openspec validate <change> --strict` passes
- [ ] 3.5 Code does nothing the specs don't describe; any extra behavior is either removed or added to the specs
- [ ] 3.6 No source documents, data/, secrets, or .env files in the diff (git status / git diff --stat)
- [ ] 3.7 Any new dependency is justified in design.md and locked in uv.lock
- [ ] 3.8 README updated if setup or usage changed
- [ ] 3.9 If an eval set exists: precision/recall recorded in review.md and not worse than the last archived change. Otherwise note "N/A: no eval set" in review.md
- [ ] 3.10 Implementation-stage review loop (openspec/reviewers/README.md) run and its report is in review.md; every escalated finding has a human Decision. If no personas exist, note "N/A: no personas" in review.md

