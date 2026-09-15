# Prompt shapes

The roles are filled by whichever agents the user names; the shapes below are what stays constant.

## Environment

```bash
export PATH="$HOME/.local/bin:$HOME/.grok/bin:$HOME/.local/share/fnm/node-versions/v24.20.0/installation/bin:$PATH"
ssh <remote-builder>
cursor-agent --print --mode plan --model <planner-model> --workspace <repo> --output-format json "Reply with PONG only. Do not edit files."
paseo ls --json          # only when a daemon-owned agent is part of the flow
```

The Grok provider needs its own bin directory on `PATH`; the Node install path is what `paseo` needs. If a headless Cursor turn exits non-zero with no output, stop and ask the user to log in on that machine — do not keep probing around the failure.

## Register the repo (Paseo)

```bash
paseo clone <owner/repo> --dir ~/Developer --protocol https --json   # -> checkout path + workspace id
```

## Planner writes the plan, then one sub-issue at a time

Prompt requirements: modify no files; output only the Markdown issue body; sections for summary, work to complete, likely files, estimated changes, acceptance criteria, out of scope, dependencies.

```bash
cursor-agent --print --mode plan --trust --force \
  --model <planner-model> --workspace <repo> --output-format json \
  "$(cat /tmp/plan-prompt.md)"
```

Take the answer from the result field, strip leftover commentary, then `gh issue create --body-file`. Read-only mode is what stops the planner from editing code while it writes issues.

## Executor implements one sub-issue

```bash
paseo run --title "<sub-issue>" --provider <provider/model> \
  --workspace <wks_id> --background "$(cat /tmp/goal-prompt.md)"
```

The goal prompt carries: sub-issue title and URL, parent plan URL, acceptance criteria, hard constraints, the branch to create or check out, the instruction to commit incrementally without pushing, and the report format. A headless executor replaces the agent with one blocking `--print --force` turn, and fix rounds continue that same session.

Two things that break remote invocations: quoting the prompt inline instead of passing it as a file (base64 the file over SSH rather than `$(cat ...)`), and assuming a daemon-owned agent has a `/goal` subcommand — it does not; the whole initial prompt is the goal.

## Review (read-only, strict)

Ask for a verdict with citations and nothing else:

```json
{"verdict": "accept | request_changes | reject", "summary": "...", "reasons": [], "requested_changes": [], "blockers": []}
```

Split the outcome: branch-level items go back to the same executor session; issue-level items (a new gap issue, a corrected issue body) belong to the planner and are applied by the orchestrator with `gh`, since a read-only turn cannot run it. Back up an existing body before replacing it.

## Standing rules

- Never author the artifact the user assigned to an agent, and never restructure the prescribed sequence.
- One sub-issue at a time; the next sub-issue is written only after the current one resolves.
- A `Status: error` immediately after a send usually means provider billing (402/403) — read the runtime's logs before debugging the orchestration.
