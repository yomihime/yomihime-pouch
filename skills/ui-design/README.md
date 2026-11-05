# ui-design

从项目实际界面提取精简、可维护的设计指南，也支持新项目界面设计和局部 UI 修复。已有界面默认保持原貌：现状、未核实项和改善建议分开记录，不因整理指南而自动改版。

本技能的范围是视觉层级、布局、组件、交互状态、设计指南及相关验证；用户可见文案的风格审计和改写不属于此技能。

指南统一使用 `.agent-workspace/design/ui-guide.md`，同目录的 `resources.md` 记录资源，同级的 `writing-guide.md` 记录文案；按需使用，不要求全部创建，不默认生成重复规则。工作流、指南发现与授权边界统一见 [SKILL.md](SKILL.md)。沿用实际 UI、token 和组件；不因审计擅自创建指南、迁移旧材料或覆盖用户内容。`.agent-workspace/` 默认本地，不自动提交或发布；正式交付物遵循用户指定位置，分享前核对隐私与授权，只清理明确获准的自建临时材料。

- `SKILL.md`：工作流、授权边界和视觉验证。
- `references/examples.md`：按场景选择的设计和检查例子。
- `references/resources.md`：官方参考链接目录；按需选择并核对来源、版本、许可证。
- `agents/openai.yaml`：技能界面元数据。
- `LICENSE`：本技能的 Apache-2.0 许可证。

将整个目录复制到 Codex skills 目录，例如 `~/.codex/skills/ui-design/`。使用示例：

> 使用 $ui-design 审计当前项目的实际界面，提出一份保留现有视觉风格的精简设计指南，区分现状与建议，先不要修改文件。

## 灵感与来源

本技能独立撰写；界面设计工作流的探索参考了 [Anthropic frontend-design](https://github.com/anthropics/skills/tree/main/skills/frontend-design) 的思路，未复制其文本、代码或素材。该技能单独使用 [Apache-2.0 许可证](https://github.com/anthropics/skills/blob/main/skills/frontend-design/LICENSE.txt)；这是对上游的致谢，不代表本技能包含上游作品。其他官方资料仅以链接列于资源目录，其软件、文档、字体和示例可能有不同条款。

本 `ui-design` 技能以 [Apache-2.0](./LICENSE) 发行。资源目录中第三方软件、文档、字体和素材各自适用其许可证，本技能许可证不覆盖这些第三方内容。

## 运行条件与触发边界

本技能无运行脚本，无 Python、Node.js 或特定操作系统依赖；实际执行依赖宿主文件工具与任务所需能力。 具体触发正反例、平台限制与实测范围见 [SKILL.md](SKILL.md#触发示例与运行要求)。
