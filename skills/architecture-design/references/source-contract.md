# 规范源与视图契约

## 唯一来源与位置

结构以 [schemas/architecture.schema.json](../schemas/architecture.schema.json) 为准，语义引用由 [render_architecture.py](../scripts/render_architecture.py) 补充校验。`schemaVersion` 当前为字符串 `"1.0"`；进度、下钻和连线语义是可选扩展，未使用这些字段的旧版 1.0 源仍有效。`revision` 是这份设计源的显式修订，不是 Skill 的版本，也不是代码已通过验证的证明。

新的长期规范源默认按需创建在 `.agent-workspace/architecture/architecture.json`，与可清理的任务材料分离。已存在有效唯一源时复用其实际位置，包括 `memory/references/` 或旧任务目录中的源，不为套默认路径自动搬迁或复制。发现多个相互冲突的“最新源”时先报告并核实有效入口，不按文件时间自行选一个覆盖其他内容。

先确认既有权威的格式与范围。已有合规 JSON 可原位读取、维护和渲染；若既有权威是 `architecture.md` 等非 JSON 正式材料，则保留原状，先协调唯一权威与获准转换范围，不默认将它降级为摘要或旁建竞争 JSON。只有确认 JSON 是唯一详细架构源后，原有 Markdown 才能按授权改为证据核验的现状摘要与路径/修订指引，不复制契约表。未完成转换时继续使用既有材料，报告标准渲染尚不可用；格式迁移不由渲染器自动完成。

一个设计范围只指定一份活跃源和一个 writer。不同独立范围确需分开时可按需使用 `.agent-workspace/architecture/<scope-id>/architecture.json`，在现有入口注明范围与实际位置；不要求每个模块各建文件。本格式的 ID 引用不跨文件，涉及共享接口时优先在同一规范源建立不同范围的视图，避免复制后独立演化。

- 长期 `architecture.json`：详细架构、契约、已确认现状与规划目标的标准化机器源；Agent 按当前任务范围读取，跨任务沿用。
- `.agent-workspace/architecture/views/architecture-<revision>.html`：可选的离线只读快照，也可输出到当前任务产物目录；源、原始证据和有效入口都不依赖它才能恢复。
- `memory/current.md`：项目唯一完整当前状态，直接写恢复必需事实、有效决定、基准、进度和下一步，并指向实际源路径与修订；不只留一个链接，也不复制完整契约表。
- 有效 AGENTS：没有项目记忆时可作为获准的短图纸入口；已有项目记忆入口时复用其指向，不再维护相互竞争的架构索引。
- 任务 `plan.md` 与任务包：引用长期源路径、修订和相关对象 ID，不因增加架构图再创建平行计划或完整图纸副本。

### 发现、维护与清理保护

1. **发现**：开始新任务先读取有效入口，按其中实际路径找到规范源，核对作用域、修订与证据基准；仅在确无相关源且任务需要长期图纸时创建默认位置。缺少入口或链接失效时进行有界定位并报告，不能默默用新空图替代已有知识。
2. **建立入口**：新增长期源后，在允许修改的既有 AGENTS 或项目记忆入口记录真实路径、覆盖范围、源修订和现状核验基准；保留人工指导和已有恢复规则。只保留必要短指引，不把全图贴入 AGENTS。入口写入未获准或失败时说明交接缺口，不声称已能自动跨任务发现。没有 project-memory 也可以使用获准的 AGENTS 入口，不自动安装其他技能。
3. **维护**：主调度者指定本批唯一图纸 writer；图纸 writer 与记忆 writer 若都需修改同一源或入口，必须串行交接写入权，不能各自并发更新。writer 先读当前源、有关事实与证据，更新前核对源未被并发改写。改动限定在本轮涉及对象，保留其他有效事实及其原核验日期；增加源修订，校验后回读，并更新获准入口中的引用。发现并发冲突时停止覆盖，先协调同一新修订。采用 project-memory 时沿用其归档与单 writer 协议；没有它时保留既有记忆，不擅自迁移或改写。
4. **分开现状与目标**：同一源可包含 current、planned、proposed、unknown，但每项声明与证据基准明确。方案采纳仅影响 decision，实施和验证依实际候选证据分别记录；任务结束、渲染成功或清理不能把计划升级成已确认现状。过期目标按实际决定更新，不能无声覆盖仍有效现状。
5. **完成任务**：回报规范源实际位置/修订、入口可达性、更新范围、证据和剩余未知。任务包与流水线只引用同一源，不复制一份“最终架构”作为另一真源。临时备选草稿若确需保留，明确标为非规范源，不用它替换有效入口。
6. **清理保护**：长期规范源、有效入口及仍支撑结论的必要证据，不属于任务 scratch 或 Agent 临时材料。清理前解析有效入口和引用；旧规范源即使仍位于任务目录，只要仍有效、正在交接或被引用就受保护。尚未建立任何持久入口时，已识别的活跃源和必要证据仍必须保留，不能因“无入口引用”将其判为可清理孤立文件；先报告入口缺口并完成获准交接。在明确授权迁移、更新全部有效入口并验证可达性之前，不删除或搬走它。历史归档不是活跃源，按原有保留政策处理，不能由普通任务 cleaner 清理。

默认路径只是新建约定，不授予迁移、覆盖、删除、修改 Git 忽略或发布权限。HTML 可由源重建，但不代表可以未经授权删除；旧网页保留时标清源修订，不声称自动更新。页面与脚本不自动参与任何归并、同步、迁移或清理。

## 根字段

| 字段 | 要求与语义 |
| --- | --- |
| `schemaVersion` | 必填，`"1.0"` |
| `revision`、`title` | 必填非空字符串；源修订和可读名称 |
| `summary` | 可选；范围、非目标、当前基准和关键未知项 |
| `architecture` | 必填，含 `style`、`rationale`；可选 `alternatives: [{style, reason}]` |
| `elements` | 必填非空数组，系统/模块/数据等元素 |
| `relationships`、`contracts`、`flows` | 必填数组；不涉及的类型可为空 |
| `views` | 必填非空数组，至少一个 overview；module/flow 按当前任务需要添加 |
| `changes` | 可选，本轮变更、采用状态与验收 |
| `extensions` | 可选对象，承载真正需要的自定义数据；不能替代必需字段 |

未知属性会报错，避免拼写错误被静默忽略。普通字段不能随意写 null 代替未知；使用对象状态与描述。内置大小限制用于避免意外超大输入，不是全仓建模目标。只接受合法 UTF-8 JSON；重复对象键会被拒绝。整数限于 JavaScript 安全范围 `-9007199254740991` 到 `9007199254740991`（含端点）。小数若在浮点文本往返转换中丢失精度、发生下溢或成为非有限值，会被拒绝；大整数标识符、精确金额和高精度小数应编码为字符串，而不是 JSON 数值。示例与 extensions 也受这些限制。输入最多 5 MiB、60 层嵌套和 100000 个值，详细集合大小限制以 Schema 为准。

## 对象、引用和状态

顶层 `elements`、`relationships`、`contracts`、`flows`、`views`、`changes` 的 `id` 必须全局唯一，采用 `^[A-Za-z][A-Za-z0-9_.:-]{0,127}$`。流程步骤 ID 仅需在所属流程内唯一。保留稳定 ID，不因改名随意更换引用。

元素、契约、流程和变更都必填 `id`、`name`、`status`、`description`。关系必填 `id`、`from`、`to`、`label`、`kind`、`status`，`description` 可选。这些对象支持 `evidence`。

| 状态 | 用法 |
| --- | --- |
| `current` | 已在所述代码/运行基准存在；需证据。与“已验收”不同 |
| `planned` | 选定但尚未实现的目标；不是发布/迁移授权 |
| `proposed` | 仍待选择或采纳的建议 |
| `unknown` | 未调查、证据不足或冲突尚未解决；描述缺什么证据 |

`evidence` 是 `{path, lines?, note?}` 的数组。`path` 使用仓库根相对 POSIX 路径，禁止绝对路径、`..`、反斜杠、URL scheme 和控制字符；`lines` 是字符串 `"12"` 或升序 `"12-27"`；在 `note` 写候选、日期、覆盖与限制。不要写秘密值或私有访问链接。

渲染器**不读取证据文件、不联网、不证明引用存在或内容属实**。无证据的 current 以及 `implemented`/`verified` 变更都会被拒绝。Agent 仍需自行核对基准、未提交改动、证据与声明是否相符。页面上显示证据不等于验证通过。

### 研发进度不是现状或验收

以下对象可选 `progress`、`progressEvidence`、`progressNote`：元素、关系、契约、流程、变更，以及流程步骤/转移。视图自身没有进度字段。

| `progress` | 页面含义 | 记录边界 |
| --- | --- | --- |
| `completed` | 已完成 | 指声明范围内研发工作完成；不自动等于已验收、已发布或 status=current |
| `in_progress` | 正在开发 | 有来源表明该工作在推进；不是页面监控到活进程 |
| `incomplete` | 未完成 | 已知工作尚未完成；不要由缺少字段推断 |
| `unknown` 或省略 | 未声明 | 无足够来源或尚未记录，不伪造完成百分比 |

非 unknown 进度必须附非空 `progressEvidence`，其 `{path, lines?, note?}` 结构与路径安全约束与普通 evidence 相同。来源可以是任务记录、流水线事件或代码文件，应在 `progressNote`/证据 note 说明作用域、报告时间、候选和限制；不要求把进度来源伪装成测试证据。渲染器只检查结构和引用格式，不读取这些文件、不确认其内容真实。

进度与 `status`（架构事实/计划）、`decision`（方案采用）、`verification`（实现/验证）分别维护。不得凭 accepted、current、绿色节点或动画推导 completed，也不得凭 completed 升级为 verified。父元素/流程的进度不向孩子、步骤或转移继承；省略就是未声明，没有自动汇总或同步。后续任务只按新的实际来源更新同一规范源。

### 元素与关系

`elements` 另含必填 `kind`，按项目使用可读类型，如 system/module/store/external，不强制技术架构形式。可选：

- `parentId`：父元素；必须存在，不能循环。
- `responsibilities`、`rules`：字符串数组，职责与必要边界。
- `contractIds`：引用唯一契约表。
- `drilldownViewId`：可选，指向以本元素为 focus 的模块视图；详细层级约束见下文。

`relationships.from/to` 都指向元素，`kind` 说明依赖/调用/读写等含义，`label` 用动词说明方向和行为。可选 `contractIds` 引用协议；禁止凭图形连线暗示未核实调用。

### 契约

`contracts` 必填 `inputs`、`outputs` 数组；不涉及数据的方向可为空。字段对象必填 `name`、`type`，可选 `required` 布尔值、`description`、`constraints` 字符串数组。输入/输出各自不能有重名字段。

其余按需字段：

- `errors: [{code, description, recovery?}]`，错误码不能重复。
- `rules: [string]`，副作用、顺序、并发、事务、信任等相关规则。
- `stateTransitions: [{from, to, trigger, description?}]`，状态名是文字，不是元素 ID。
- `examples: [{name, input, output}]`，input/output 可以是符合本节数值和大小限制的任意 JSON；错误样例的预期错误放 output，不会因此执行请求。

详度按 [实施交接](implementation-handoff.md) 判断，不因 schema 允许省略就省略本轮真正需要的规则。

### 流程与视图

`flows` 必填 `steps`（非空）与 `transitions`（可为空）数组。步骤必填 `id`、`name`、`elementId`；可选 `description`、`contractIds`、`outcome`、`status`、`evidence`。转移必填 `from`、`to`（同一流程内的步骤 ID），可选 `label`、`condition`、`outcome`、`status`、`evidence`。`outcome` 为 `normal`、`failure` 或 `recovery`，不等于对象是否 current。步骤/转移未写 `status` 时继承所在流程的状态。显式提供 `evidence`（包括空数组）会覆盖流程证据；仅在自身 `status` 与 `evidence` 都省略时才继承流程证据。显式设置 `status: current` 必须附自身非空证据；继承 current 却显式写 `evidence: []` 也会报错。混合现状与目标的流程要逐项覆盖状态，不能把规划边画成现有行为。

视图必填 `id`、`name`、`kind`，可选 `description`：

- `overview` / `module`：必须提供 `elementIds`（非空）和 `relationshipIds`（可为空），禁止 `flowId`。所选关系两端都必须出现在该视图元素集合。
- `flow`：必须提供 `flowId`，禁止 `elementIds` / `relationshipIds`；步骤与边完全从对应流程派生。

没有单独维护的视图节点/连线正文。模块视图与总体视图只是从同一表选取不同范围；流程步骤引用同一模块/接口。流程孤立步骤和未建模失败/恢复分支会警告，需判断是遗漏还是本轮确不适用，不为消警告虚构行为。

### 节点逐层下钻

下钻结构仍在同一 JSON 中，不另存一套导航图：

1. 元素 `drilldownViewId` 指向一个 `kind: module` 视图；目标视图的 `focusElementId` 必须反指该元素，二者一一对应，不能有多个模块视图争用同一 focus。
2. 模块视图 `elementIds` 仍列出全部可见节点。可选 `contextElementIds` 必须是它的子集，用于显式展示父级、外部系统或其他上下文边界；这些节点只允许查看，不从该视图继续下钻。
3. `elementIds` 去掉上下文后是内部节点，至少一个，而且每个都须通过 `parentId` 成为 focus 的严格后代，不能把 focus 本身或无关节点伪装成内部。
4. 内部节点可再声明下钻目标，形成总体 → 模块 → 子模块的连续层级。父子循环、导航循环、越界引用、断开的 focus/目标关联及重复 focus 均拒绝。

只有 module 视图支持 `focusElementId`；`contextElementIds` 还要求存在 focus。旧的无 focus 模块视图仍有效，可从视图选择入口查看，但不能假装成已绑定的节点下钻目标。最深层没有目标时只显示详情，不编造下一层。

### 连线语义与示意动效

关系和流程转移可选 `semantics: main | branch | async | return | error`，分别标明主路径、条件分支、异步、返回和错误。省略时保留普通连线，不自动把所有边认作主路径，也不从颜色/进度猜语义。流程的 `outcome` 仍独立说明 normal/failure/recovery；依据真实契约选择两个字段，不让视觉效果决定业务含义。

查看器的线型、方向和可选动效是对源中已声明关系的示意，不执行流程、连接运行进程、读取流水线实时状态或改变进度。启停动效只是本页查看行为；源不变，网页仍是固定修订的快照。

### 本轮变更

`changes` 可引用 `elementIds`、`contractIds`、`flowIds`，`acceptance` 为本轮具体验收条件字符串数组；缺少验收会警告。另有：

- `decision: draft | accepted | rejected`：方案采用状态，省略不表示已批准。
- `verification: unverified | implemented | verified`：实现/验证状态，省略不表示已验证。

采纳方案不代表运行通过或得到操作授权；已实现仍需验收。rejected 与 verified 不允许同时出现。证据字段的存在只是最低结构约束，标 verified 前仍须检查真实候选与验收证据。

## 渲染与失败边界

Python 3.9+ 标准库即可运行，无 npm、第三方包、服务、端口或在线图形库。先用 `--validate-only` 检查，再显式 `--output` 新的 `.html`/`.htm` 文件。输出父目录须已存在；已有文件、最终路径符号链接和同源路径均拒绝覆盖；没有 `--force` 或同步模式。

输出目录须由调用者控制，并在运行期间保持稳定。POSIX 使用目录描述符逐层固定祖先，不跟随符号链接，拒绝祖先符号链接和 `..`；某些 macOS 的 `/tmp` 是符号链接，不能假定总能使用，应选择真实无符号链接路径。原生 Windows 及缺少这些 POSIX 能力的平台保留排他新建路径（`O_EXCL`，Windows 加 `O_BINARY`），发出目录稳定性警告，不要求 WSL；这不是跨平台的恶意目录隔离保证。后备路径经过模拟回归，但本环境未原生 Windows 实测。

成功退出码 0；输入、语义引用或输出错误退出码 2，并报告位置。警告可以伴随成功，不能当作无问题。读取、验证或渲染失败不改写原源或既有输出。输出写入失败后可能留下本次新建的部分文件，工具不会自动删除它，以免误删并发替换的文件。检查错误与现场后，选择新输出名称重试；不要删除用户文件来绕过覆盖保护。

页面内嵌数据、CSS 和 JS，可直接用 `file://` 打开；显示源文件名、修订、原始源 SHA-256、生成时间和渲染器版本。源变了旧网页不会变化，网页不能写回 JSON/代码/记忆；需要时显式生成新快照并核对修订。源码 SHA-256 表示输入身份，不证明设计、实现、证据或权限正确。
