# Architecture Design · 架构设计

先根据约束选择合适的架构，再用一份标准化源表达总体、模块和当前实施流程。新项目先搭最小骨架再逐步细化；已有项目先核实现状，只展开这轮要改的部分。避免为了画图而全仓测绘或过度设计。

## 使用

将整个 `architecture-design/` 目录安装到客户端支持的技能目录，保留脚本、Schema、资源和 LICENSE。调用 `$architecture-design` 或在架构设计、架构梳理、需要明确边界的工程变更中使用。具体规则见 [SKILL.md](SKILL.md)。

可单独安装，不要求同时安装其他技能。可用时与 project-memory 的完整当前状态、multi-agent-engineering 的角色任务、development-pipeline 的原有计划和验收衔接；不自动安装、迁移项目、修改权限、提交、推送或发布。

示例请求：

> 先让架构师按我们当前的规模、部署和数据约束选择合适架构。整理已有实现的证据，再为这轮功能细化模块、接口、错误、规则、状态变化和验收样例。使用一份 JSON 同时给执行 Agent 和离线图纸页面读取。

## 看一张实际示例图

Python 3.9+，仅标准库，无需安装依赖。在仓库根运行下面的命令即可生成离线示例页面。HTML 从 [虚构示例源](assets/demo.json) 生成，只维护 JSON 与 viewer 源，不手工修改 HTML。

Windows PowerShell（原生运行，无需 WSL）：

```powershell
New-Item -ItemType Directory -Path .\architecture-preview
py -3 skills/architecture-design/scripts/render_architecture.py skills/architecture-design/assets/demo.json --validate-only
py -3 skills/architecture-design/scripts/render_architecture.py skills/architecture-design/assets/demo.json --output .\architecture-preview\architecture-demo.html
```

若 Python 安装未提供 `py` 启动器，改用实际 Python 3.9+ 的 `python` 命令。macOS/Linux shell：

```sh
mkdir architecture-preview
python3 skills/architecture-design/scripts/render_architecture.py \
  skills/architecture-design/assets/demo.json --validate-only
python3 skills/architecture-design/scripts/render_architecture.py \
  skills/architecture-design/assets/demo.json \
  --output architecture-preview/architecture-demo.html
```

示例使用一个新的、由调用者控制且运行期间保持稳定的目录。已有目录可复用，但输出文件必须尚不存在；已有同名文件时换新名称，不删除或覆盖它。POSIX 会拒绝输出路径祖先中的符号链接和 `..`，请选择真实无符号链接目录；某些 macOS 的 `/tmp` 本身是符号链接，不保证可作输出目录。Windows 使用原生排他新建并会提示保持目录受控稳定；其后备路径经过模拟回归，本环境**未做原生 Windows 实测**，不承诺跨平台防御恶意目录替换。

浏览器直接打开新生成的 `architecture-preview/architecture-demo.html`。脚本不覆盖、不监听、不自动同步，也不写回源文件或项目记忆。写入失败可能留下本次新建的部分文件，不会自动删除；先检查文件，再选择新输出名称重试。单独安装时替换命令中的技能路径。

页面展示三个视角如何复用同一组模块和契约，可选择节点与关系，查看职责、证据、输入/输出、错误、状态和样例，支持搜索、缩放及失败/恢复路径。它是带源修订和哈希的离线只读快照，不是代码运行或验收通过的证明。

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

项目里默认把新图纸放 `.agent-workspace/<work-id>/architecture.json`，HTML 是派生快照。已有规范源则原位复用，不再维护平行 JSON 或手写图；`memory/current.md` 仍是唯一完整当前状态，直接说明事实并引用详细源路径/修订。目录按需创建，含项目数据的源和网页默认本地私有。

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

## 许可

本技能使用 [MIT License](LICENSE)，可单独分发。示例为虚构数据，不包含项目私有材料。
