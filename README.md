# Compose Agent Skill

在启动 agent 前，先确定在哪台机器、用哪个 provider/model、在哪个项目和 workspace/worktree 中执行。

这是一个偏原则的调度前置 skill，不重复执行工具的命令手册。有 Paseo 相关 skill 时先加载 `paseo`，再只读检查可用资源；用户没说清楚的选择，带着真实候选询问，不替用户默选。

## 内容

- 加载执行系统的 skill，遵循其工具语义与 profile 选择规则。
- 只读发现 runtime、模型、项目和 workspace/worktree，按机器核实可用性。
- 明确四项执行选择，保护已有代码与工作区。
- Paseo 出问题时停下报告，不自行实现替代方案。
- Cursor 默认走 headless `--print`：一次调用一轮，命令自己阻塞到结束，多步工具循环在同一轮内完成，多轮靠 `--resume <session_id>`。
- 仅当目标是 daemon 托管的会话时才走 Cursor ACP，那时仍按 `/run-everything` 初始化权限并做排障。

完整内容见 [SKILL.md](SKILL.md)。

## 使用

将本仓库的 `SKILL.md` 和 `scripts/` 一起放入宿主支持的 `compose-agent/` skill 目录，并按宿主的方式加载。Paseo 的操作参考由独立的 `paseo` skill 提供，本仓库不包含它。

例如：

> 在可用的 runtime 上安排一个 agent 处理这个任务，先确认模型、项目和 worktree。

## 等待与接力

原 `watch-paseo` 已并入本 skill，无需另外安装。使用 Paseo 原生等待，不自写轮询：

```bash
bash /path/to/compose-agent/scripts/watch-paseo.sh AGENT_ID
```

第二个参数可传远端 `HOST`（例如 `ssh://user@host`）。依赖 Bash 和支持 `wait` 的 Paseo CLI，默认无限等待，错误原样返回。Alma 中后台执行且不设总 timeout，完成事件恢复会话后，读日志、核对产物、独立验证，再按原授权接力；**idle 不代表验收通过**。

测试：`PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests`。测试覆盖参数、远端参数透传、阻塞等待、错误退出和非法参数，不需要真实 daemon 或 Cursor CLI。

## Cursor：headless `--print`

只要宿主能跑一条阻塞命令（本机、SSH、调度器），Cursor 就默认走 headless print 模式，不占用 Paseo 的会话等待：

```bash
bash /path/to/compose-agent/scripts/cursor-headless.sh PROMPT [SESSION_ID]
```

脚本跑一轮、带上预授权的全权限标志、把 JSON 结果打到 stdout，并原样传递退出码；第二个参数传上一轮的 `session_id` 即续接同一会话。不轮询、不重试、不处理权限。

- **一次调用一轮，轮内多步。** 单次调用里 agent 会跑完整个工具循环（读、写、跑 shell）再返回；多轮 = 多次调用。
- **等待是自带的。** `cursor-agent -p` 同步阻塞到该轮结束，不需要也不该再套 Paseo `wait`、watcher 或状态轮询。
- **读 JSON 而不是控制台。** `--output-format json` 返回一个对象，取 `.result` 作为答案、`.session_id` 作为下一轮的句柄；`text`（默认）只打最终答案，`stream-json` + `--stream-partial-output` 用于实时进度。
- **退出码即结论。** 0 成功、非 0 失败；不要用部分输出判断成功。无头模式下工作区未受信任会立刻退出 1，因此需要写入的调用要显式带上 `--force`/`--yolo` 或 `--trust`。
- **不要把「没带 `--force`」当成沙箱。** 写入是否放行也受 CLI 自身审批模式与本地配置影响，可能照样自动批准。

以上行为在 macOS 上用 cursor-agent 2026.09.10 实测：单次 `-p --force --output-format json` 调用在建文件、读回、跑 shell 后才退出 0；`--resume <session_id>` 能回忆上一轮内容；未受信任目录在不带 `--force`/`--trust` 时立刻退出 1。

## Cursor 权限默认值

**headless 模式下默认带 `-f/--force`（`--yolo` 同义），这是 ACP 那条 `/run-everything` 在无头场景的对应物。** 在 ACP 会话里则默认要求在启动后发送 `/run-everything`，不再逐次询问。两者都是本项目明确采用的全权限执行策略，并非各协议的通用默认值。采用本 skill 前请审阅这一规则；如果需要限制权限，应明确覆盖它。

该设置仅适用于 Cursor，不授权额外启动任务，也不允许在原生命令失败时通过批准循环、切换执行方式或修改 Paseo 配置绕过问题。

## License

[MIT](LICENSE)
