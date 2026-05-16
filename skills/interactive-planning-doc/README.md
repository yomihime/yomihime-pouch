# interactive-planning-doc

`interactive-planning-doc` 是一个 Codex 技能，用来把交互式功能、重构或发布讨论整理成可执行计划文档。🧭

适合只做计划、不改代码的场景：先确认范围、取舍、里程碑、提交分组、验证方式、验收流程和收尾事项，再交给之后的 agent 执行。

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
