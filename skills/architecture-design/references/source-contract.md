# 规范源与视图契约

## 唯一来源与位置

结构以 [schemas/architecture.schema.json](../schemas/architecture.schema.json) 为准，语义引用由 [render_architecture.py](../scripts/render_architecture.py) 补充校验。`schemaVersion` 当前为字符串 `"1.0"`；`revision` 是这份设计源的显式修订，不是 Skill 的版本，也不是代码已通过验证的证明。

默认新的任务图纸放 `.agent-workspace/<work-id>/architecture.json`。已存在有效规范源时复用其实际位置，包括已由项目记忆固化的源，不拷贝到新任务目录成为第二份现状。一个设计范围只指定一份活跃源和一个 writer；不同独立范围可以有不同源，但共享契约仍指定唯一维护位置，不能互相复制后独立演化。本格式的 ID 引用不跨文件；涉及共享接口时优先在同一规范源建立不同范围的视图。

- `architecture.json`：详细架构、契约、现状和目标的标准化机器源；Agent 按本任务范围读取它。
- `architecture.html` 或带修订后缀的 HTML：仅是该源一次渲染的离线快照，可丢弃后重建，不是编辑入口。
- `memory/current.md`：项目唯一完整当前状态，直接写恢复必需事实、有效决定、基准、进度和下一步，并指向实际源路径与修订；不只留一个链接，也不复制完整契约表。
- 任务 `plan.md`：原有需求/切片/验收的主计划，引用有关对象 ID；不因增加架构图再创建平行计划。

长期保留时由记忆 writer 按已有归档、证据固化和并发检查协议处理源及引用；迁移后只保留一个有效入口，历史归档不能被当作现状。未经确认不移动、覆盖或删除已有材料。页面和脚本不自动参与任何归并、同步或迁移。

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

### 元素与关系

`elements` 另含必填 `kind`，按项目使用可读类型，如 system/module/store/external，不强制技术架构形式。可选：

- `parentId`：父元素；必须存在，不能循环。
- `responsibilities`、`rules`：字符串数组，职责与必要边界。
- `contractIds`：引用唯一契约表。

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
