# Unattended loop pattern

Shape and decisions for running planner / executor / reviewer cycles with nobody watching.

## Shape

```text
state.json { task, issue, branch, base_branch, round, executor_session, pending_prompt, completed[] }

loop:
  if pending_prompt   -> one executor turn (blocking); store the returned session id
  review the branch   -> planner-style read-only turn
  accept              -> land the branch, apply issue-level findings,
                         plan the next sub-issue, queue its prompt
  request_changes     -> queue the feedback as the next executor turn; round += 1
```

## Rules

- **Store the next action, not the last one.** The state file holds the exact prompt about to be delivered and the session it goes to, written before the blocking call. A driver killed mid-turn then resumes without resending a turn or skipping a review. Never keep the pending prompt in memory only.
- **Iterate on the same executor session.** Fix rounds continue that conversation (a resumed Cursor turn, or a message sent to the same daemon-owned agent). A fresh session loses the branch context the reviewer just critiqued.
- **Block, never poll.** Every wait is owned by the tool that knows the answer: the synchronous headless turn, or the runtime's own wait command. Do not re-inspect status on a timer, and do not schedule a polling script from the scheduler.
- **Watch artifacts, not status.** To react to something outside the current call, block on the artifact (turn file, pushed branch, state transition) in one background process that notifies on exit and re-arms per event. A coarse check interval inside that process is fine; a foreground poll loop is not.
- **Cap the rounds, then escalate.** Bound review rounds per task (4 is a reasonable default). On the cap, persist the last verdict and stop with a report — do not silently accept, and do not keep looping.
- **Land durably, but no further than told.** Push the accepted branch so the work survives; do not merge or open a PR unless the user asked. When tasks are dependencies, stack the next branch on the accepted one and say so in the sub-issue.
- **Contain crashes.** Wrap the loop in a handler that writes the traceback and reports its last line; a driver that dies silently is indistinguishable from one that is still working.
- **One instance.** A pidfile with a liveness check stops two drivers fighting over the same checkout.

## Before leaving it unattended

Run the first full transition by hand: accept a task, let the driver create the next sub-issue, and confirm the next executor turn started. That seam — rebuilding the executor prompt from planner output whose key names are not the state's key names — is where unattended drivers crash, and it crashes *after* the accept, so the loop looks healthy right up to the moment it stops.
