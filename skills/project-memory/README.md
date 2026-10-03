# project-memory

项目本地工程记忆技能：用简短 AGENTS.md 入口和按需参考，保存目标、约束、环境、架构、调试知识与当前检查点，减少跨会话重复扫描。

把整个目录复制到你的技能目录（例如 `~/.codex/skills/project-memory/`），按当前客户端的技能发现方式加载。不会更改全局配置，也不会自动初始化当前仓库的记忆。

```text
使用 $project-memory，为这个项目初始化最小的本地工程记忆，保留人工指导。
使用 $project-memory，只读检查当前记忆的鲜度、加载冲突和发布风险。
使用 $project-memory，先恢复目标与检查点，再继续当前修复。
```

- `SKILL.md`：操作入口与边界
- `references/privacy-and-loading.md`：本地 exclude、已有 tracked/staged 冲突、真实加载语义与发布检查
- `references/memory-schema.md`：六类工程事实和短检查点的候选结构
- `references/maintenance.md`：增量复核、恢复、精简与行为验证
- `agents/openai.yaml`：技能展示元数据

本包可提交的是通用方法。使用后生成的 AGENTS.md、override、记忆和缓存全部留在项目本地，不得提交或上传；已有追踪冲突需要明确处理，ignore 无法解决。不要存密钥值，技能也不是秘密保险库。它不能保证启动自动执行、无限上下文或自动压缩恢复。
