# multi-agent-engineering

可复用的多 agent 工程协作技能：用通用角色、任务卡和按风险选择的模型，推进实现、验证和独立审查。适合跨步骤修复、重构与交付，也尊重“只调查、不改代码”的边界。

把整个目录复制到你的技能目录（例如 `~/.codex/skills/multi-agent-engineering/`），按当前客户端的技能发现方式加载。不会安装自定义 agent，也不会自动更改模型设置。

```text
使用 $multi-agent-engineering，按 economy 档调查并修复这个问题。
先确认实际可用模型和生效配置；保留现有架构，用小切片实现，给出验证证据。
```

- `SKILL.md`：入口与协作闭环
- `references/model-policy.md`：运行时发现、预算、模型选择及刷新
- `references/task-cards.md`：任务卡和需求—证据链
- `references/desktop-audio-example.md`：带日期的桌面音频示例，不是固定型号策略
- `agents/openai.yaml`：技能展示元数据

没有子 agent 能力时可顺序执行，但会明确未完成独立审查。没有设备、权限、遥测或实际运行证据时会保留未知与待验项；技能本身不保证硬费用上限。
