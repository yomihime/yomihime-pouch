# 示例与目录

## 先看同源示例

[assets/demo.json](../assets/demo.json) 是随技能分发的虚构订单处理示例，不是用户项目现状。它在同一源里演示总体、模块逐层下钻和当前切片流程视角，以及接口、失败/恢复路径、架构状态与独立研发进度。不要把示例路径或行为当作真实项目证据。

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

可按视图切换总体/模块/流程，通过选择节点或关系查看职责、证据、接口输入/输出、错误、状态转换和样例；有明确下钻目标的内部节点可继续进入下一层，上下文节点只查看。研发进度来自源中独立的 progress 声明，不由架构状态、父流程或动效推断。页面的查看和缩放不修改规范源。渲染器不会执行示例中的业务请求或读取证据路径。

## 在页面里逐层查看与演示路径

- 点击声明了 `drilldownViewId` 的内部节点，进入对应模块；卡片的“详情”按钮查看该节点契约，详情内也可选“展开内部结构”。没有下钻目标或属于 context 的节点只查看详情，不跳到不相关页面。
- 用面包屑或“返回上一层”回到上层，也可按 Alt+Left。直接从侧栏进入模块时可“返回总览”；逐层返回会恢复该层搜索、缩放、滚动和选中，并将焦点交还原节点。
- “路径演示”默认折叠、静态。展开后选择起点，可播放、暂停、单步或重置；遇到多条出边暂停，让查看者选择一条分支，不自行猜业务条件或随机执行。
- 每条关系/转移在一次演示中至多展示一次，避免循环无尽播放。这是查看器的防循环展示策略，不说明真实业务只能执行一次，也不证明算法会终止。
- 隐藏页面、收起演示、切换视图或打印时自动暂停。系统启用 `prefers-reduced-motion` 时禁用连续播放，仍可静态单步。

演示只读取当前 HTML 已嵌入的图纸修订，不调用业务接口、写文件或从外部取得运行状态；动画亮起不等于正在开发，走到出口也不等于验收通过。

## 项目材料的默认目录

```text
project/
  AGENTS.md                         既有有效入口，保留人工指导
  src/                              真实源码仅示意，不强制项目采用此目录
  tests/                            真实测试仅示意
  .agent-workspace/                  本地私有，按需创建
    memory/
      current.md                    唯一完整当前状态，直接写关键事实
      references/                   可选，较长知识；已有有效规范源仍原位复用
      evidence/                     可选，长期必要原始证据
      archive/                      按记忆协议保留的历史，不是活跃源
    architecture/                   按需，跨任务保留，不随任务清理
      architecture.json             没有既有有效源时，新增长期唯一规范源
      views/                        可选，可重建的离线只读快照
        architecture-<revision>.html
    <work-id>/
      plan.md                       复用已有主计划，引用规范源路径/修订/对象 ID
      architecture-<revision>.html   可选，任务内只保留派生快照
      jobs/                         按需的角色任务、原始回报和现场证据
      artifacts.md                  可选，关键交付物和保留去向
```

这是位置约定，不要求预建整棵树。长期源通过有效 AGENTS 或项目记忆入口跨任务发现。若 `memory/references/`、旧任务目录或别处已有有效唯一源，在原位置复用并由入口指向实际路径，**不再创建默认位置的副本**。多个独立范围确需分别建模时可放 `architecture/<scope-id>/architecture.json`，共享接口优先留在同一源。

长期源、入口及必要证据不随任务清理；旧源仍在任务目录也不能因任务完成删除。尚未建立持久入口的活跃源同样受保护，不能当作无引用临时文件清理。迁移要另有授权，更新引用并验证后才能处理旧位置。旧网页可以留作明确标注修订的快照，但不是已确认现状，也不自动跟随源更新。历史源按已有归档规则管理，不由渲染器处理。

获准维护的短入口可以写成：“长期架构源：`.agent-workspace/architecture/architecture.json`；覆盖订单处理与库存边界；当前源修订 `<revision>`，现状核验基准 `<candidate>`。新任务先复用此源，计划与已实现对象分别标注；图纸与必要证据不属于任务清理范围。”示例中的范围/修订/基准必须替换为真实信息；采用项目记忆时 current.md 仍须直接说明关键事实，不仅粘贴这段链接。

## 从需求到当前切片

- 新项目说“做一个本地工具”：先确认离线、数据所有者和部署约束，选最小可行架构；总体只含已知边界，先把一个用户动作细化成模块契约和流程，不预建远期服务。
- 已有项目说“增加一个导出格式”：先核对当前导出入口、数据模型和测试，再只设计格式选择、序列化及写入失败处理。外围系统未调查就标 unknown，不假造完整调用图。
- 用户说“改一个拼写”：已有上下文足够时直接修复，不触发全仓建图、架构师评审或新的图纸工作区。

可开工的交接至少能回答：哪个源修订、哪些对象 ID、从哪里开始、输入/输出及失败规则是什么、改哪些位置、用什么候选和样例验收。工程角色继续沿用已有任务包，不因图纸另起一套协议或进度表。
