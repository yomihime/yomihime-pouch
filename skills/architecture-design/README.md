# Architecture Design · 架构设计

先根据约束选择合适的架构，再用一份标准化源表达总体、模块和当前实施流程。新项目先搭最小骨架再逐步细化；已有项目先核实现状，只展开这轮要改的部分。避免为了画图而全仓测绘或过度设计。它是 project-memory 的架构补充（plus）：集中保存长期图纸并逐步细化，不替代完整当前状态，也可独立安装。

## 使用

将整个 `architecture-design/` 目录安装到客户端支持的技能目录，保留脚本、Schema、资源和 LICENSE。调用 `$architecture-design` 或在架构设计、架构梳理、需要明确边界的工程变更中使用。具体规则见 [SKILL.md](SKILL.md)。

可单独安装，不要求同时安装其他技能。可用时与 project-memory 的完整当前状态、multi-agent-engineering 的角色任务、development-pipeline 的原有计划和验收衔接；不自动安装、迁移项目、修改权限、提交、推送或发布。

示例请求：

> 先让架构师按我们当前的规模、部署和数据约束选择合适架构。整理已有实现的证据，再为这轮功能细化模块、接口、错误、规则、状态变化和验收样例。使用一份 JSON 同时给执行 Agent 和离线图纸页面读取。

## 看一张实际示例图

Python 3.9+，仅标准库，无需安装依赖。按[示例与目录](references/examples.md)中的命令在仓库根生成离线示例页面。HTML 从 [虚构示例源](assets/demo.json) 生成，只维护 JSON 与 viewer 源，不手工修改 HTML。

完整的 Windows PowerShell 与 macOS/Linux 命令、目录条件及页面操作见 [示例与目录](references/examples.md)。输出文件必须尚不存在；不删除或覆盖旧文件，选择受控且稳定的目录。POSIX 拒绝祖先符号链接与 `..`；Windows 后备路径仅经模拟回归，未做原生 Windows 实测。写入失败可能留下部分新文件，先核对再换新名称重试。

页面是带源修订的只读快照，不自动同步或写回；动效不代表实时运行或验收通过。规范源、状态、入口与清理保护以 [SKILL.md](SKILL.md) 和 [结构规范](references/source-contract.md) 为准。

## 文件与唯一来源

```text
architecture-design/
  SKILL.md                         Agent 入口与关键边界
  README.md                        安装与示例命令
  LICENSE                          MIT
  agents/openai.yaml               客户端展示元数据
  schemas/architecture.schema.json  标准化机器源结构
  scripts/render_architecture.py   校验及离线只读渲染
  assets/demo.json                 虚构示例，唯一示例数据源
  assets/viewer.html               网页模板
  assets/viewer.css                离线样式
  assets/viewer.js                 只读交互
  references/                     按需工作方式、规范与交接说明
  tests/                          结构、语义与渲染回归
```

没有既有有效源时，新的长期规范源按需放 `.agent-workspace/architecture/architecture.json`；已有唯一源原位复用，不自动迁移、覆盖或另建权威。Markdown 等既有权威的转换须先确认范围。入口保留实际路径与修订，`memory/current.md` 仍直接记录完整当前状态。

每个范围一名 writer，现状与计划分别标注。源、入口与必要证据跨任务保留，旧任务目录中的有效源也受保护。HTML 是可重建的只读快照；可重建不等于获准删除。项目材料默认本地私有，迁移、清理和共享须有相应授权。完整位置、维护及交接规则见[规范源契约](references/source-contract.md#唯一来源与位置)，实际目录树见[示例与目录](references/examples.md#项目材料的默认目录)。

- [选择架构与工作方式](references/workflow.md)
- [机器源、状态、证据和渲染契约](references/source-contract.md)
- [能直接实施的交接深度](references/implementation-handoff.md)
- [项目目录和示例用法](references/examples.md)

Schema/脚本能检查字段、引用和部分状态约束，不能判断证据是否真实、设计是否合理、行为是否通过测试。方案采用、实现、验证和用户授权分别对待。完整结果需报告实际基准、范围和未验证项。

## 检查

可运行 Python 测试和可选的 Node.js 18+ 查看器测试：

```sh
python -m unittest discover -s skills/architecture-design/tests -v
node skills/architecture-design/tests/test_viewer_dom.cjs
```

后者使用模拟 DOM，不能代替真实浏览器排版、截图或 CSP 验证。原生 Windows 运行和真实浏览器视觉验收仍需在目标环境核验。

## 参考与致谢

交互思路参考 [tt-a1i/archify](https://github.com/tt-a1i/archify)，包括从总体查看模块细节的图形交互。本技能、规范、渲染器及查看器独立撰写，未复制 Archify 的代码或素材，也不代表获得其官方背书。

2026-11-03 核对时，Archify 的主许可为 [Apache-2.0](https://github.com/tt-a1i/archify/blob/main/LICENSE)；其 [NOTICE](https://github.com/tt-a1i/archify/blob/main/NOTICE) 说明历史许可与例外，并保留 [历史 MIT 许可](https://github.com/tt-a1i/archify/blob/main/LICENSE-MIT)，第三方组件另见 [第三方声明](https://github.com/tt-a1i/archify/blob/main/THIRD_PARTY_NOTICES.md)。这里仅提供参考链接，不把上游或第三方许可扩展到本项目；后续若引入其代码/素材，需另行核对并遵守对应条款。

## 许可

本技能使用 [MIT License](LICENSE)，可单独分发。示例为虚构数据，不包含项目私有材料。

## 运行条件与触发边界

渲染器需要 Python 3.9+ 标准库和同目录 Schema/assets。 具体触发正反例、平台限制与实测范围见 [SKILL.md](SKILL.md#触发示例与运行要求)。
