# 示例与目录

## 先看同源示例

[assets/demo.json](../assets/demo.json) 是随技能分发的虚构订单处理示例，不是用户项目现状。它在同一源里演示总体、模块和当前切片流程视角以及接口、失败/恢复路径和状态区分。不要把示例路径或行为当作真实项目证据。

使用下面命令生成离线示例页面。HTML 是生成物，不是第二份可手工维护的源码；源修订变化后需要显式重新生成。

在仓库根执行，单独安装时替换技能路径。Windows PowerShell 原生示例：

```powershell
New-Item -ItemType Directory -Path .\architecture-preview
py -3 skills/architecture-design/scripts/render_architecture.py skills/architecture-design/assets/demo.json --validate-only
py -3 skills/architecture-design/scripts/render_architecture.py skills/architecture-design/assets/demo.json --output .\architecture-preview\architecture-demo.html
```

若没有 `py` 启动器，使用实际 Python 3.9+ 的 `python`。macOS/Linux shell 示例：

```sh
mkdir architecture-preview
python3 skills/architecture-design/scripts/render_architecture.py \
  skills/architecture-design/assets/demo.json --validate-only
python3 skills/architecture-design/scripts/render_architecture.py \
  skills/architecture-design/assets/demo.json \
  --output architecture-preview/architecture-demo.html
```

选择运行期间稳定、由自己控制的真实目录。输出父目录必须已存在，输出文件必须尚不存在；若同名文件已存在，改用新名称，不删除或覆盖旧文件。POSIX 拒绝输出祖先路径中的符号链接和 `..`，部分 macOS 的 `/tmp` 是符号链接，应改用真实无符号链接目录。Windows 支持原生排他新建，不要求 WSL；后备路径仅做了模拟回归，尚未原生 Windows 实测，也不提供跨平台恶意目录隔离保证。

写入失败可能留下部分新文件，渲染器不会自动删除，以免误删并发替换的文件；先核对现场，重试时选新输出名称。浏览器打开生成的 HTML 即可看图，不需要服务、CDN 或网络。详见 [渲染与失败边界](source-contract.md#渲染与失败边界)。

可按视图切换总体/模块/流程，通过选择节点或关系查看职责、证据、接口输入/输出、错误、状态转换和样例。页面的查看和缩放不修改规范源。渲染器不会执行示例中的业务请求或读取证据路径。

## 项目材料的默认目录

```text
project/
  AGENTS.md                         既有有效入口，保留人工指导
  src/                              真实源码仅示意，不强制项目采用此目录
  tests/                            真实测试仅示意
  .agent-workspace/                  本地私有，按需创建
    memory/
      current.md                    唯一完整当前状态，直接写关键事实
      references/                   可选，较长知识及已固化规范源
      evidence/                     可选，长期必要原始证据
      archive/                      按记忆协议保留的历史，不是活跃源
    <work-id>/
      plan.md                       复用已有主计划
      architecture.json             没有既有有效源时，本轮唯一规范源
      architecture.html             显式生成的只读快照
      architecture-<revision>.html   需要新快照时用新的输出名
      jobs/                         按需的角色任务、原始回报和现场证据
      artifacts.md                  可选，关键交付物和保留去向
```

这是位置约定，不要求预建整棵树。若 `memory/references/` 或别处已有有效规范源，在原位置复用并由 current.md 指向它，**不同时再创建本轮 architecture.json 副本**。旧网页可以留作明确标注修订的快照；不能让多个 JSON 声称同一范围的最新事实。历史源按已有归档规则管理，不由渲染器处理。

## 从需求到当前切片

- 新项目说“做一个本地工具”：先确认离线、数据所有者和部署约束，选最小可行架构；总体只含已知边界，先把一个用户动作细化成模块契约和流程，不预建远期服务。
- 已有项目说“增加一个导出格式”：先核对当前导出入口、数据模型和测试，再只设计格式选择、序列化及写入失败处理。外围系统未调查就标 unknown，不假造完整调用图。
- 用户说“改一个拼写”：已有上下文足够时直接修复，不触发全仓建图、架构师评审或新的图纸工作区。

可开工的交接至少能回答：哪个源修订、哪些对象 ID、从哪里开始、输入/输出及失败规则是什么、改哪些位置、用什么候选和样例验收。工程角色继续沿用已有任务包，不因图纸另起一套协议或进度表。
