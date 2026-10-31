# project-memory

维护项目本地的完整当前状态、代码地图与证据，改写前归档旧版，帮助主调度者恢复和子任务定点开工。

- `AGENTS.md`：短入口、稳定约束和按角色读取规则，保留人工指导。
- `.project-memory/current.md`：唯一完整现状；主调度者或单 Agent 恢复时全文读取。
- `.project-memory/references/`：按需保存代码地图、现状图纸和领域细节。
- `.project-memory/evidence/`：按需保留支撑长期结论的原始证据。
- `.project-memory/archive/`：改写前的原始旧版与恢复清单，正常恢复不读取。
- `.agent-work/`：可选协作工作区，任务包、回报、检查点和临时材料不成为第二份项目现状。

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

通用 Skill 可分发，实际项目记忆、工作区与缓存本地私有，不提交、上传或打包。复制技能目录不会自动初始化项目、更新已有 AGENTS、安装其他 Skill 或重载当前会话；已有布局与指导需按授权兼容。单 Agent 可独立完成维护，子 Agent 非必需。
