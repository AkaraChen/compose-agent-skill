# Compose Agent Skill

在启动 agent 前，先确定在哪台机器、用哪个 provider/model、在哪个项目和 workspace/worktree 中执行。

这是一个偏原则的调度前置 skill，不重复执行工具的命令手册。有 Paseo 相关 skill 时先加载 `paseo`，再只读检查可用资源；用户没说清楚的选择，带着真实候选询问，不替用户默选。

## 内容

- 加载执行系统的 skill，遵循其工具语义与 profile 选择规则。
- 只读发现 runtime、模型、项目和 workspace/worktree，按机器核实可用性。
- 明确四项执行选择，保护已有代码与工作区。
- Paseo 出问题时停下报告，不自行实现替代方案。
- 单独说明 Cursor ACP 的 `/run-everything` 权限初始化与排障。

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

测试：`PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests`。测试覆盖参数、远端参数透传、阻塞等待、错误退出和非法参数，不需要真实 daemon。

## Cursor 权限默认值

**本 skill 默认要求在启动 Cursor ACP 会话后发送 `/run-everything`，不再逐次询问。** 这是本项目明确采用的全权限执行策略，并非 ACP 协议的通用默认值。采用本 skill 前请审阅这一规则；如果需要限制权限，应明确覆盖它。

该设置仅适用于 Cursor，不授权额外启动任务，也不允许在原生命令失败时通过批准循环或修改 Paseo 配置绕过问题。

## License

[MIT](LICENSE)
