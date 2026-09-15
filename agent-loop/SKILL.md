---
name: agent-loop
description: Drive planner, executor and review rounds unattended. Use when a task should be split into per-task issues authored by a planner, implemented one at a time by an executor, and accepted or returned by a read-only reviewer — including when the user hands over full authority and stops supervising the run.
---

# Agent Loop

One task at a time moves through three roles: a planner writes the issue, an executor implements it, a reviewer accepts or returns it. This skill owns the loop, its artifacts, and its stop conditions. Placement, permission posture, and how a single run is launched belong to `compose-agent`; the loop starts after a run has been composed.

## Roles

- **Planner — issues authored in a read-only turn.** Plan and every sub-issue are written with the planner unable to edit code (Cursor: `--print --mode plan`). Nowhere else does the contract come from. One sub-issue at a time: write the next one only after the current one resolves.
- **Executor — one sub-issue per turn.** The prompt carries the sub-issue URL, the parent plan URL, the acceptance criteria, hard constraints (files not to touch, defaults not to switch), the branch to create or check out, and the report format. It commits incrementally and does not push.
- **Reviewer — a verdict over the diff.** Read-only turn, judged against the sub-issue's acceptance criteria, output a verdict object and little else. Prefer a model family different from the executor's; when both roles share one family, say so in the handoff rather than presenting the review as independent.

## Artifacts

- **The issue text is the contract.** Summary, work to complete, likely files, estimated change size, acceptance criteria, out of scope. Everything the reviewer judges comes from it, so an issue edited mid-loop invalidates the review.
- **One branch per task**, cut from the stated base. When tasks depend on each other, stack the next branch on the accepted one and say so inside the sub-issue.
- **A state file** that survives a killed driver: `{task, issue, branch, base_branch, round, executor_session, pending_prompt, completed[]}`.
- **A verdict object** from the review turn: `{"verdict": "accept | request_changes | reject", "summary", "reasons", "requested_changes", "blockers"}`.

## The loop

1. **Plan.** The planner writes the parent plan issue. Follow its split; do not invent extra tasks to look thorough. Done when a plan URL exists.
2. **Queue exactly one sub-issue.** Planner turn → issue body → `gh issue create`. Done when the URL is in the state file.
3. **Run the executor turn.** Deliver the queued prompt and keep the returned session id; for a daemon-owned agent keep its agent id instead. Done when the turn returns (synchronous mode) or the agent goes idle (daemon mode).
4. **Wait natively.** The wait belongs to whatever owns the answer: the blocking call itself, or the runtime's own `wait` command. No timer polls, no scheduled job re-running a status script. Done when the turn has actually ended.
5. **Review.** Read-only turn over the branch, verdict with reasons and citations. Idle or exit 0 is not acceptance, and the executor's own report is not evidence — run the required verification yourself before believing a green summary. Done when a verdict is stored.
6. **Branch on the verdict.**
   - `accept` → land the branch (push; merge or open a PR only if the user asked), record the acceptance and the reviewer's scope statement, then return to step 1 for the next sub-issue.
   - `request_changes` → send the requested changes back to the **same** executor session; a fresh session loses the branch context the reviewer just critiqued. `round += 1`; past the cap (4 is a reasonable default), persist the last verdict and stop with a report.
   - `reject` → stop and report. Do not keep looping.

## Unattended rules

- **One long-lived driver, not a poll.** The loop is a single process that blocks on each turn. A scheduled job that re-runs a polling script every N minutes is a different, worse design.
- **Write state before every blocking call.** Store the exact prompt about to be delivered and the session it goes to. A driver killed mid-turn then resumes without resending a turn or skipping a review.
- **Watch artifacts, not status.** To react to something outside the current call, block on the artifact (turn file, pushed branch, state transition) in one background process that notifies on exit and re-arms per event. A coarse check interval inside that process is fine; a foreground poll loop is not.
- **Cap and escalate.** Bound the rounds per task; on the cap, persist the last verdict and stop with a report instead of looping forever or accepting silently.
- **Contain crashes.** Wrap the loop in a handler that writes the traceback to a file and reports its last line. A driver that dies silently looks exactly like one that is still working.
- **One instance.** A pidfile with a liveness check keeps two drivers from fighting over the same checkout.
- **Report on events only** — accept, a new round, stop, error. The driver's own log is the progress record; per-tick chatter is noise.

## Pitfalls

- **The accept → next-task seam is the crash-prone part**, and it fails *after* the accept, so the loop looks healthy right up to the moment it stops. Exercise one full transition by hand — accept a task, let the driver write the next sub-issue, confirm the next executor turn started — before leaving it unattended. The usual cause is rebuilding the executor prompt from planner output whose key names differ from the state file's.
- **`git diff --shortstat origin/main...<branch>` inflates under squash merges.** The branch's local copies of already-merged commits carry different SHAs. Count the branch's own work, or quote the reviewer's scope statement, and flag the inflated baseline before anyone opens a PR from that branch.
- **Back up an issue body before a rewrite.** A correction replaces the whole body; save the current text to a file first so a bad rewrite is one command to undo.
- **`Status: error` right after a send is usually provider billing, not the agent.** The reason only appears in the runtime's logs, and a 402/403 there blocks the whole loop no matter how correct the orchestration is. Check status right after the first send.
- **A read-only planner can hide its answer in a tool call.** The result field sometimes holds only narration ("I'll record those actions now") while the real plan sits in a tool-call input in the session transcript. Deep-search the transcript before declaring the turn failed.
- **Issue-level findings are the planner's, not the executor's.** Split the verdict: branch-level items go back to the executor session; a missing gap or a wrong issue body goes back to the planner, applied by the orchestrator, because a read-only turn cannot run `gh`.

## Verification

- Every task in the state file has an issue URL, a branch, a stored verdict, and a recorded acceptance.
- The review was independent: the diff was read against the acceptance criteria and the required checks were run, not quoted from the executor's report.
- The driver log shows a round count per task, and no task ended without a verdict.
- The crash file is empty on success; a traceback in it means the loop stopped early.
- Landing is confirmed where it happened (branch exists, PR state read back), not assumed from the push output.
