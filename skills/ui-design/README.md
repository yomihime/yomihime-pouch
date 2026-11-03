# ui-design

从项目实际界面提取精简、可维护的设计指南，也支持新项目界面设计和局部 UI 修复。已有界面默认保持原貌：现状、未核实项和改善建议分开记录，不因整理指南而自动改版。

本技能的范围是视觉层级、布局、组件、交互状态、设计指南及相关验证；用户可见文案的风格审计和改写不属于此技能。

先查 `AGENTS.md`、项目约定、实际 UI、现有 token 和组件，按当前任务读取相关部分。项目本地规范统一放在 `.agent-workspace/design/`，界面指南为 `.agent-workspace/design/ui-guide.md`；可按需用同目录的 `resources.md` 记录项目资源，文案指南为同级 `writing-guide.md`，不要求全部创建，不默认生成重复规则。创建或修改指南及 `AGENTS.md` 只在用户授权范围内进行；已有指南交由 `init` 盘点并安全整理，保留内容、不自动覆盖，冲突先报告并确认，不建立旧路径长期兼容或双份权威。指南缺失或不可读时参考实际 UI 并提示，不擅自重建。

截图、审计清单和草稿放在 `.agent-workspace/<work-id>/scratch/`，只清理本次创建且明确可清理的材料。统一工作区默认本地、不默认提交或发布；被 Git 忽略或未跟踪的指南可能不会随仓库传播，分享前需确认隐私与授权。保留用户已有共享约定；用户明确要求的正式文档按指定目的地交付，不强制私有化。新项目从主要工作流出发，局部修复优先最小改动，交付时说明验证和限制。

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
