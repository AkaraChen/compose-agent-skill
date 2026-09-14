---
name: compose-agent
description: Use before launching or delegating an agent when the runtime machine, provider/model, project, or workspace needs to be resolved. Also applies when the user asks where or how an agent should run, or asks to watch an existing Paseo agent until idle and then take over review or follow-up work.
---

# Compose Agent

Resolve where and how an agent will run, then resume review or follow-up after it settles. This skill owns placement, clarification, and handoff, not the execution tool's command reference.

## Principles

1. **Load the execution skill first.** If Paseo-related skills are available, load the base `paseo` skill before discovery. Follow it for tool semantics and profile selection. Otherwise use the available execution system's documentation; do not invent commands or install anything silently.
2. **Discover before asking.** Check available runtime machines, providers/models, projects, and workspaces/worktrees within the user's scope. Discovery is read-only: do not launch agents, create worktrees, clone repositories, or change configuration to manufacture an option.
3. **Keep availability scoped.** Verify results belong to the target runtime. A model, project, path, or workspace on one machine says nothing about another. Use current provider-scoped model IDs, not remembered names. Distinguish verified, unavailable, and unknown.
4. **Resolve four choices.** Establish the runtime, provider/model (or configured profile), project/path, and workspace/worktree. Preserve explicit user choices. If any remain unclear, ask with verified candidates; a recommendation is not authorization. Do not silently default to the current machine or directory.
5. **Protect existing work.** Check the selected repository's branch/base and working state. Do not overwrite changes or assume a remote-tracking branch is fresh. Recommend isolation for independent work; clarify reuse versus a new worktree and its base when unspecified.
6. **Stop at problems and permission boundaries.** If Paseo fails, lacks a capability, or blocks on permission after the native setup below, report it and ask the user. Do not build wrappers, substitute another route, change configuration, or add approval loops to achieve the blocked outcome.

## Wait and take over (Paseo)

Prefer native completion notifications when already enabled. When asked to watch an existing agent, use the bundled script with its full ID and the previously resolved runtime. Requires Bash and a Paseo CLI with native `wait` support:

```bash
bash <skill-dir>/scripts/watch-paseo.sh AGENT_ID [HOST]
```

Replace `<skill-dir>` with this skill's absolute directory. Omit `HOST` for the local daemon; for a remote daemon pass its native Paseo host target, such as `ssh://user@host`. The script invokes `paseo wait --json`, with no total timeout, and preserves its output and exit code. It adds no polling, retries, or permission handling; an already idle agent can return immediately.

- **Keep the wait attached to the host.** In Alma, start it using Bash with `run_in_background: true` and no `timeout`. Retain `bash_id` and use blocking BashOutput reads. A read deadline is not process completion. If still running with no other work, yield and let the background completion event resume the conversation. Do not use `nohup` or rapid status polling. The host delivers the event; the script does not send messages or launch follow-up agents.
- **Check the outcome.** On nonzero exit, connection failure, permission blockage, or unexpected Paseo behavior, report and stop. Do not substitute a watcher implementation or work around the failure.
- **Review before continuing.** Idle means the turn stopped, not that the task passed. Read the target's latest logs and task artifacts, identify failures or pending permissions, and independently run the required verification. Detached tests may still be running; check that specific test run separately.
- **Respect the original stopping rule.** Continue or return defects to the same agent only within existing authorization. At a human checkpoint or a new decision, report evidence and wait. Never expose credentials from raw logs.

## Exception: cursor-agent over ACP

**Enable `/run-everything` by default when starting cursor-agent over ACP.** The user has pre-authorized this native permission mode; do not ask for separate approval. This standing instruction applies to Cursor, not other providers, and does not authorize launching agents for draft-only requests.

- **Session setup:** send `/run-everything` inside the target Cursor session before handing over the task, unless the user explicitly requests restricted permissions. This is a Cursor-specific slash command, not a generic ACP setting or a Paseo launch parameter to guess. Check the session response rather than assuming it took effect.
- **When apparently stuck:** check pending permissions before blaming model reasoning. An agent can show `running` while waiting for approval; report the actual pending requests, not a diagnosis based only on elapsed time or zero writes.
- **No workaround:** if the native command fails or cannot be delivered through the supported interface, stop and report. Do not add approval loops, modify Paseo configuration, or substitute repeated one-shot approvals.

Treat this as a setup-specific operational lesson. Recheck current documented capabilities when versions change; a missing string in an application bundle does not prove a capability is impossible.
