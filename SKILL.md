---
name: compose-agent
description: Use before launching or delegating an agent when the runtime machine, provider/model, project, workspace, or permission mode needs to be resolved. Also applies when the user asks where or how an agent should run, when choosing how permissive a run should be, when driving the Cursor CLI headlessly with --print, or asks to watch an existing Paseo agent until idle and then take over review or follow-up work.
---

# Compose Agent

Resolve where and how an agent will run, then resume review or follow-up after it settles. This skill owns placement, clarification, and handoff, not the execution tool's command reference.

## Principles

1. **Load the execution skill first.** If Paseo-related skills are available, load the base `paseo` skill before discovery. Follow it for tool semantics and profile selection. Otherwise use the available execution system's documentation; do not invent commands or install anything silently.
2. **Discover before asking.** Check available runtime machines, providers/models, projects, and workspaces/worktrees within the user's scope. Discovery is read-only: do not launch agents, create worktrees, clone repositories, or change configuration to manufacture an option.
3. **Keep availability scoped.** Verify results belong to the target runtime. A model, project, path, or workspace on one machine says nothing about another. Use current provider-scoped model IDs, not remembered names. Distinguish verified, unavailable, and unknown.
4. **Resolve four choices.** Establish the runtime, provider/model (or configured profile), project/path, and workspace/worktree. Preserve explicit user choices. If any remain unclear, ask with verified candidates; a recommendation is not authorization. Do not silently default to the current machine or directory.
5. **Protect existing work.** Check the selected repository's branch/base and working state. Do not overwrite changes or assume a remote-tracking branch is fresh. Recommend isolation for independent work; clarify reuse versus a new worktree and its base when unspecified.
6. **Stop at problems and permission boundaries.** If Paseo fails, lacks a capability, or blocks on permission after the native setup below, report it and ask the user. Do not build wrappers, substitute another route, change configuration, or add approval loops to achieve the blocked outcome. Permission is settled when the run is composed (see the posture section below), not worked around while it runs.

## Permission posture: unrestricted by default

Automation outranks approval friction here. When composing a run, choose the target's unrestricted permission mode **at launch**, so the agent never stops on a prompt that nobody is watching. Decide the posture while composing; do not start a run on a prompt-by-prompt mode and hope someone is around to approve.

- **Read the mode off the target.** `paseo agent mode <id> --list --json` prints the ids and labels an existing agent accepts; `paseo provider ls --json` shows a provider's `defaultMode` and mode labels. Pass the unrestricted id as `--mode <id>` when launching. Verified ids: codex `full-access` ("Full Access"; the other two are `auto`, `auto-review`), claude `bypassPermissions`. Labels seen without a confirmed id: amp-acp "Bypass", kimi "YOLO". No unrestricted entry at all: **cursor** (`agent`/`plan`/`ask` only), grok, opencode (`Build`/`Plan`). A label is not an id — resolve it against the target, do not guess.
- **Cursor needs its own mechanism.** Headless: `-f`/`--force` (the bundled script already passes it). Over ACP: send `/run-everything` in the session before handing over the task. Cursor has no paseo mode for this, so do not go looking for one.
- **Adjusting a live run is a native command, not a script.** `paseo agent mode <id> <mode>` changes an agent's mode. Prefer getting it right at launch, use that command to correct one, and do not build a polling approval loop. If a run is already parked on pending approvals and the mode change does not clear them, report the pending requests instead of inventing machinery.
- **A named mode is the mechanism; a workaround is not.** No polling approval loops, no edits to the scheduler's configuration, no injecting commands into a live session. If the target offers no unrestricted mode, say so in the handoff rather than approximating one.
- **Hand off with the posture stated.** An unrestricted run can write files, install packages, and reach the network without asking. Say so once, when handing off, so the choice is visible rather than silent.

## Wait and take over (Paseo)

This applies to agents that a daemon owns. A Cursor run started through headless `--print` is already synchronous and needs none of it — see the Cursor section below.

Prefer native completion notifications when already enabled. When asked to watch an existing agent, use the bundled script with its full ID and the previously resolved runtime. Requires Bash and a Paseo CLI with native `wait` support:

```bash
bash <skill-dir>/scripts/watch-paseo.sh AGENT_ID [HOST]
```

Replace `<skill-dir>` with this skill's absolute directory. Omit `HOST` for the local daemon; for a remote daemon pass its native Paseo host target, such as `ssh://user@host`. The script invokes `paseo wait --json`, with no total timeout, and preserves its output and exit code. It adds no polling, retries, or permission handling; an already idle agent can return immediately.

- **Keep the wait attached to the host.** In Alma, start it using Bash with `run_in_background: true` and no `timeout`. Retain `bash_id` and use blocking BashOutput reads. A read deadline is not process completion. If still running with no other work, yield and let the background completion event resume the conversation. Do not use `nohup` or rapid status polling. The host delivers the event; the script does not send messages or launch follow-up agents.
- **Check the outcome.** On nonzero exit, connection failure, permission blockage, or unexpected Paseo behavior, report and stop. Do not substitute a watcher implementation or work around the failure.
- **Review before continuing.** Idle means the turn stopped, not that the task passed. Read the target's latest logs and task artifacts, identify failures or pending permissions, and independently run the required verification. Detached tests may still be running; check that specific test run separately.
- **Respect the original stopping rule.** Continue or return defects to the same agent only within existing authorization. At a human checkpoint or a new decision, report evidence and wait. Never expose credentials from raw logs.

## Cursor: headless `--print` (default)

Drive Cursor through headless print mode (`cursor-agent -p`) whenever the host can run a blocking command — locally, over SSH, or from a scheduling agent. One invocation is one turn, and the command returns when that turn ends. **The wait is built in:** there is nothing to poll, no Paseo `wait`, and no watcher.

```bash
bash <skill-dir>/scripts/cursor-headless.sh PROMPT [SESSION_ID]
```

The script runs one turn, forces the pre-authorized full-permission mode, prints the JSON result object, and propagates the exit code. Pass the previous turn's `session_id` as `SESSION_ID` to continue the conversation. It adds no polling, retries, or permission handling.

- **One turn per call, multiple steps inside it.** Within a single call the agent runs its full tool loop — reads, writes, shell commands — before returning. Multi-turn means separate calls, not one long prompt.
- **Full permissions are a launch flag here.** `-f`/`--force` (alias `--yolo`) is the documented headless equivalent of the ACP `/run-everything` step below, and it also satisfies workspace trust. An untrusted directory in print mode exits 1 immediately instead of prompting, so a headless call that must write needs one of `--force`, `--yolo`, or `--trust`.
- **Read the JSON, not the console.** `--output-format json` returns one object: `type`, `subtype`, `is_error`, `duration_ms`, `result`, `session_id`, `request_id`, `usage`. Take the answer from `.result` and the next turn's handle from `.session_id`. Default `text` prints only the final answer; `stream-json` with `--stream-partial-output` is for live progress. Always pass an explicit session id when resuming — bare `--resume` opens a session picker, and `create-chat` mints an id up front.
- **Exit code is the verdict.** Zero on success, nonzero on failure; never infer success from partial output. A retrying connection re-emits the turn's text into `.result`, so the string can repeat — read it as the answer, not as a guaranteed single copy.
- **Do not treat print mode as a sandbox by omission.** Write approval also follows the CLI's own approval mode and local configuration, which can auto-approve writes even without `--force`. To restrict a run, set the mode explicitly rather than relying on an absent flag.
- **Attach long turns to the host.** A single turn can run for minutes. In Alma, start the script with Bash `run_in_background: true` and no `timeout`, keep the `bash_id`, and use blocking BashOutput reads — a read deadline is not process completion. The built-in wait means no separate watcher is needed, not that the call is instantly short.

Verified against cursor-agent 2026.09.10 on macOS: a single `-p --force --output-format json` call created a file, read it back, and ran a shell command before exiting 0; `--resume <session_id>` recalled the previous turn; an untrusted directory exited 1 without `--force`/`--trust`.

## Exception: cursor-agent over ACP

Use this only when the target is a session-managed agent rather than a command you can run — for example an agent that a Paseo daemon owns. Prefer the headless section above when the host can execute a command directly.

**Enable `/run-everything` by default when starting cursor-agent over ACP.** The user has pre-authorized this native permission mode; do not ask for separate approval. This standing instruction applies to Cursor, not other providers, and does not authorize launching agents for draft-only requests.

- **Session setup:** send `/run-everything` inside the target Cursor session before handing over the task, unless the user explicitly requests restricted permissions. This is a Cursor-specific slash command, not a generic ACP setting or a Paseo launch parameter to guess. Check the session response rather than assuming it took effect.
- **When apparently stuck:** check pending permissions before blaming model reasoning. An agent can show `running` while waiting for approval; report the actual pending requests, not a diagnosis based only on elapsed time or zero writes.
- **No workaround:** if the native command fails or cannot be delivered through the supported interface, stop and report. Do not add approval loops, modify Paseo configuration, or substitute repeated one-shot approvals. Choosing headless print mode up front is a mode decision, not a fallback: do not switch to it to get around a permission or capability failure in a session that is already running.

Treat this as a setup-specific operational lesson. Recheck current documented capabilities when versions change; a missing string in an application bundle does not prove a capability is impossible.
