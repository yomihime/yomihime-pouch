# project-memory

维护项目本地的完整当前状态、代码地图与证据，改写前归档旧版，帮助主调度者恢复和子任务定点开工。

- `AGENTS.md`：短入口、稳定约束和按角色读取规则，保留人工指导。
- `.agent-workspace/memory/current.md`：唯一完整现状；主调度者或单 Agent 恢复时全文读取。
- `.agent-workspace/memory/references/`：按需保存代码地图、现状图纸和领域细节。
- `.agent-workspace/architecture/`：按需保存跨任务的稳定架构源。采用 architecture-design 并确认 JSON 权威后，同一范围一份标准 JSON，已有有效源原位复用；`memory/references/architecture.md` 保留有证据的现状说明，并引用机器源路径、修订与对象 ID，不复制契约表。既有权威 Markdown 未经获准转换不能自动降级。
- `.agent-workspace/memory/evidence/`：按需保留支撑长期结论的原始证据。
- `.agent-workspace/memory/archive/`：改写前的原始旧版与恢复清单，正常恢复不读取。
- `.agent-workspace/<work-id>/`：按需保存任务计划、回报、检查点和临时材料，不成为第二份项目现状，也不存源码 checkout。源码默认在主仓库主 checkout，按互不重叠文件分工；跨仓库确需 worktree 时只设一个共享且在主仓库根目录下可见的 worktree。成功交接并接收后先回收 Agent，再按授权安全清理。

项目本地材料统一使用 `.agent-workspace/`，设计指南位于 `design/`，运行时缓存位于 `runtime.md`，观察器索引位于 `index.html`。旧项目下次开工时由 yomihime-init 盘点并安全整理，保留来源、冲突和恢复依据，不覆盖已有内容；日常恢复不维护旧目录回退或双写。

`architecture` 与 `memory`、`design`、`plans`、`work` 一样是保留目录名，不可用作 work-id。采用 architecture-design 并确认 JSON 权威后，任务目录只保留架构建议、差异、报告及派生快照，不因新任务另建同范围权威源。迁移或覆盖既有源须有授权；活跃源、现状说明和仍被引用的证据不属于普通临时清理。

普通已委派子任务取得适用约束和相关地图/图纸后定点读取，不默认重复加载全体记忆；测试、审查、维护和清理仍需各自必需材料。记忆 writer 全文读当前快照与待改文件，按已接收事实批次维护，并返回归档/核验回执。

```text
使用 $project-memory，为项目初始化最小记忆，保留人工指导。
使用 $project-memory，恢复当前项目并为指定子任务提取相关知识。
使用 $project-memory，只读检查地图鲜度、加载冲突和发布风险。
使用 $project-memory，归并这些已确认事实，维护前归档并核验结果。
```

- `SKILL.md`：入口、角色读取与边界。
- `references/privacy-and-loading.md`：真实加载、本地排除与发布检查。
- `references/memory-schema.md`：受管目录、完整当前快照和知识资料。
- `references/maintenance.md`：归档更新、恢复与迁移。
- `references/collaboration.md`：知识摘录、地图/图纸、事实批次与证据固化。
- `agents/openai.yaml`：技能展示元数据。

通用 Skill 可分发，实际项目记忆、工作区与缓存本地私有，不提交、上传或打包。复制技能目录不会自动初始化项目、更新已有 AGENTS、安装其他 Skill 或重载当前会话；旧材料整理和有效指导修改须在授权范围内进行。单 Agent 可独立完成维护，子 Agent 非必需。

## 运行条件与触发边界

本技能无运行脚本，无 Python、Node.js 或特定操作系统依赖；实际执行依赖宿主文件工具与任务所需能力。 具体触发正反例、平台限制与实测范围见 [SKILL.md](SKILL.md#触发示例与运行要求)。
