# multi-agent-engineering

按任务依赖组织工程协作，用可开工任务包、相关地图/图纸和受控写入推进并行实现、验证与独立验收。

主对话是主调度者；实现者、架构师、设计师、顾问、测试员、审查官按需承担工作，交互验证员、记忆维护员和 cleaner 在有明确需求时介入。同任务优先原线程，独立审查使用新上下文，容量以实际运行时为准。

采用 project-memory 时，主调度者完整恢复当前快照，再定向提取子任务知识。普通子 Agent 不默认加载全体记忆；收到任务包后确认 ready/gap，从精确入口补读实际材料并工作。没有 project-memory 或子 Agent 工具时也能按相同职责顺序执行，但不能冒充独立审查。

```text
使用 $multi-agent-engineering，按 economy 调查并修复这个问题。
复用相关代码地图和契约，给各子任务可开工输入，按依赖并行并提供原始验证证据。
```

- `SKILL.md`：角色、启动与交付边界。
- `references/task-cards.md`：task-handoff-v1、角色例外、点对点通信和回报。
- `references/coordination.md`：容量、实例工作目录、生命周期、产物和清理。
- `references/model-policy.md`：实际模型发现、预算与能力选型。
- `references/desktop-audio-example.md`：能力与真实集成证据示意。
- `agents/openai.yaml`：技能展示元数据。

整个目录可复制到技能目录加载。不会安装自定义 Agent、修改模型或全局配置，也不自动迁移实际项目记忆；任务包、归档和协作材料保持项目本地私有。示例候选不保证账户可用、实际参数生效或硬费用上限。
