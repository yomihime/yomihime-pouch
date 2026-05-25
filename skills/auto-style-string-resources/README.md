# auto-style-string-resources

`auto-style-string-resources` 是一个 Codex 技能，用来审计、归类并分批风格化程序字串和 UI 文案。🧵

适合整理 i18n 文案、硬编码显示文本、提示语、警告、导入/导出说明和用户可见消息的场景：先建立 UI/UX 字串树、归纳目标风格、给出 `style_score` 和处理等级，再在用户确认的范围内应用改写。

## 🎀 文件

- `SKILL.md`：主入口，也是技能系统读取的核心文件。
- `scripts/draft_string_tree.py`：辅助生成字串树草稿。
- `scripts/check_string_constraints.py`：检查改写前后是否保留占位符、路径、HTML/Markdown 等约束。
- `agents/openai.yaml`：UI 元数据。

## 🪄 安装

把整个目录复制到 Codex skills 目录：

```text
~/.codex/skills/auto-style-string-resources/
```

使用时可以这样触发：

```text
使用 $auto-style-string-resources，审计当前项目的 UI 文案，整理字串树并给出低风险改写候选。
```
