# auto-style-string-resources

这是一个 Codex 技能，用来审计和改进项目中的用户可见文字，包括 UI 字串、i18n 资源、README 和 docs。它适用于中文、日文等多语言项目，也能帮助定位硬编码文案。

技能会先核对文字的使用场景和项目风格，整理场景树，给出 `style_score`、处理等级及改写示例，再按用户授权的范围分批修改。目标是清楚自然地表达，而不是套用固定话术；事实、真实警告、限制、不确定性、占位符和程序契约都要保留。`style_score` 表示风格发挥空间，不是自然度评分，也不代表修改许可。

## 风格选择

可根据用户偏好和项目现有语气，选择或组合“实用简洁”“清晰引导”“轻松自然”“主题化表达”“日系轻柔”，也可以自定义。各场景的表达强度可以不同，警告和错误始终以准确清楚为先。中文和日文分别按各自的习惯和场景斟酌，不因选用预设自动翻译或同步其他 locale，也不强加人设。

## 文件

- `SKILL.md`：技能的主入口。
- `scripts/draft_string_tree.py`：从特定目录和部分 Python 字串生成启发式草稿，不覆盖所有框架、资源或文档，也可能收录技术字串，需要人工核对和补查。
- `scripts/check_string_constraints.py`：检查常见占位符、路径和格式约束，但不验证位置参数的顺序，不能替代语义和运行时核对。
- `agents/openai.yaml`：技能界面元数据。

## 安装

把整个目录复制到 Codex skills 目录：

```text
~/.codex/skills/auto-style-string-resources/
```

使用示例：

```text
使用 $auto-style-string-resources，审计当前项目的 UI 文案和 README，整理场景树并给出低风险改写候选。
```
