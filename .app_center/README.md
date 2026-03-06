# .app_center

This folder is managed by **App Center** and is meant to live inside a project root.

Terminology note: when you (the user) say **"documents"**, you mean this `.app_center/` workspace.

## What belongs here

- `HOME.md`: your "project cockpit" landing page.
- `operator/`: operator-facing docs to review (concept maps, curated backlogs, summaries).
- `planning/`: roadmaps, checklists, current focus, decision logs.
- `docs/`: architecture and feature documentation.
- `protocol/`: rules, conventions, and principles for this project.
- `protocol/COMMIT_MODE.md`: commit/auto-commit policy used by App Center and agents.
- `notes/`: fast capture and scratch notes.
- `logs/`: agent runs, scan summaries, and other time-stamped outputs.
- `exec_plans/`: workflow runtime lanes (`active`, `pending`, `future`).
- `followups/commit_push/`: post-archive commit/push incident queue (`open`, `resolved`).
- `workflow_policy.json`: sticky workflow defaults for this repository.

- `changelog/`: canonical workflow archives (`000X 'Title'/exec_plan + record`) and `INDEX.jsonl`.

Legacy note:
- Existing docs/planning/protocol/notes/logs lanes remain supported for compatibility.

## Reading order (recommended)

1. `HOME.md`
2. `planning/CURRENT.md`
3. `planning/ROADMAP.md`
4. `docs/ARCHITECTURE.md`
5. `protocol/PRINCIPLES.md`
6. `protocol/COMMIT_MODE.md`
7. `workflow_policy.json`
8. `exec_plans/active/` (if a run is active)
9. `changelog/` (newest first)

## Agent rule (important)

- Before creating commits, agents should read `protocol/COMMIT_MODE.md`.
  - If it is missing or unparseable: default to **manual** (no automatic commits/pushes).
  - If it enables `commit_mode: agent`: agents may auto-commit, but should not auto-push unless explicitly enabled.

## Notes

- App Center will not overwrite existing files.
- You can safely commit this folder to your repo if you want it shared.
