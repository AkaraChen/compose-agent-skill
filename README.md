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

将本仓库的 `SKILL.md` 放入宿主支持的 `compose-agent/` skill 目录，并按宿主的方式加载。Paseo 的操作参考由独立的 `paseo` skill 提供，本仓库不包含它。

例如：

> 在可用的 runtime 上安排一个 agent 处理这个任务，先确认模型、项目和 worktree。

## Cursor 权限默认值

**本 skill 默认要求在启动 Cursor ACP 会话后发送 `/run-everything`，不再逐次询问。** 这是本项目明确采用的全权限执行策略，并非 ACP 协议的通用默认值。采用本 skill 前请审阅这一规则；如果需要限制权限，应明确覆盖它。

该设置仅适用于 Cursor，不授权额外启动任务，也不允许在原生命令失败时通过批准循环或修改 Paseo 配置绕过问题。

## License

[MIT](LICENSE)
