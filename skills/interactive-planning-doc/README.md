# interactive-planning-doc

`interactive-planning-doc` 是一个 Codex 技能，用来把交互式功能、重构或发布讨论整理成可执行计划文档。🧭

适合只做计划、不改代码的场景：先确认范围、取舍、里程碑、提交分组、验证方式、验收流程和收尾事项，再交给之后的 agent 执行。

## 项目文件位置

本地协作计划统一使用 `.agent-workspace/<work-id>/plan.md`，草稿和截图放在 `.agent-workspace/<work-id>/scratch/`；复用同一任务的主计划，不默认生成重复规则或平行计划。正式文档仍按用户指定目的地交付，不强制私有化。

旧目录由 `yomihime-init` 盘点并安全整理，保留已有计划和人工编辑、不自动覆盖，冲突先报告并确认；不建立长期旧路径兼容。本地工作区不默认提交、发布或混入构建产物，保留用户已有共享约定，分享前检查授权和隐私。收尾只清理本次创建且明确可清理的中间材料，保留执行和恢复仍需使用的主计划。

## 🎀 文件

- `SKILL.md`：主入口，也是技能系统读取的核心文件。
- `SKILL.en.md`：英文镜像归档。
- `agents/openai.yaml`：UI 元数据。

## 🪄 安装

把整个目录复制到 Codex skills 目录：

```text
~/.codex/skills/interactive-planning-doc/
```

使用时可以这样触发：

```text
使用 $interactive-planning-doc，把这次讨论整理成里程碑、提交分组、验证检查和收尾事项。
```
