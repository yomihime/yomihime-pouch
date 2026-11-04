# Yomihime Skill Information

把计划理清，把交接时需要的线索收好，开工时就能从容一些。这里是 yomihime 的技能集合，一份陪项目慢慢完善的小小工具箱。

本文介绍技能的公共约定、运行要求和评估结果。当前为 **1.0.0 待审候选**，尚未合并、发布或安装。作者：**yomihime（如月怜） <evenia@evenia.moe>**。技能目录和用途以 [技能目录](./README.md) 为入口，维护规则以 [SKILL_STANDARD.md](./SKILL_STANDARD.md) 为唯一权威；本文件提供导览，并记录指定候选的评估快照。

## 技能集合

| 技能 | 主要职责 | 不应混淆的边界 |
| --- | --- | --- |
| [architecture-design](./architecture-design/SKILL.md) | 梳理架构、边界、契约与有证据的图纸 | 不把目标设计或动画当成已实现事实 |
| [auto-style-string-resources](./auto-style-string-resources/SKILL.md) | 审计用户可见字串和文案指南，保留机器约束 | 结构检查不能证明文案语义或自然度 |
| [development-pipeline](./development-pipeline/SKILL.md) | 按依赖组织轮次、实现切片、检查点和证据 | 上报状态不等于独立验证，也不授权发布 |
| [interactive-planning-doc](./interactive-planning-doc/SKILL.md) | 通过讨论形成可执行工程计划 | docs-only 阶段不擅自实施 |
| [multi-agent-engineering](./multi-agent-engineering/SKILL.md) | 分工、单一写入权、交接和独立审查 | 没有调度工具时不虚构独立 Agent |
| [project-memory](./project-memory/SKILL.md) | 保存当前状态与恢复必需上下文 | 只读检查不自动改写记忆或项目文件 |
| [ui-design](./ui-design/SKILL.md) | 复用界面规范，设计并验证可访问性 | 截图或 DOM 检查不等于端到端验证 |
| [yomihime-init](./yomihime-init/SKILL.md) | 检查所需技能、版本和安全工作区布局 | 保留本地定制，源不可核验时明确记录 |

每个技能都可以单独安装。跨技能协作是可选能力，所需依赖须在各自包中明确声明。详细触发正反例和权限边界见各技能自身的 `SKILL.md`。

## 公共 spec 导览

### 技能包结构

```text
skills/
  README.md
  SKILL_STANDARD.md
  yomihime-skill-information.md
  <skill-name>/
    SKILL.md                 # 必需：名称、触发条件、流程和边界
    LICENSE                  # 按本技能适用许可保留
    README.md                # 按需：安装、运行和验证入口
    agents/openai.yaml       # 按需：宿主界面元数据
    references/              # 按需：细则与案例
    scripts/                 # 按需：可执行辅助工具
    assets/                  # 按需：运行资源与模板
    tests/                   # 按需：结构、行为与安全回归
  tests/                     # 仓库维护检查，不是单技能运行依赖
```

- 目录名与 frontmatter `name` 一致。`metadata.author` 保留作者身份；唯一版本权威为字符串 `metadata.version`，采用 `MAJOR.MINOR.PATCH`，三个非负整数不允许前导零，每段最多 9 位，不附带 prerelease 或 build 字段。八个技能各自从 `"1.0.0"` 建立独立版本基线，之后按各自变化递增，不要求永远同步。
- `metadata.updated_at` 单独记录实际内容修订时刻，使用带引号的 UTC `YYYY-MM-DDTHH:MM:SSZ`，不是文件 mtime、下载时间、发布证明或版本排序依据。planning 的英文镜像与主文件保持相同作者、版本和更新时间。
- 后续兼容修复用 PATCH、向后兼容功能用 MINOR、不兼容契约变化用 MAJOR。尚未发布的同一候选修订可保留目标版本，但需要刷新真实更新时间并重验受影响证据。版本按整数三元组比较，不能按字符串或日期比较。
- 单独安装要保留该技能实际需要的脚本、资源、引用和许可；不复制不存在的依赖、不创建假的输出文件来满足扫描器。
- 历史 ISO 版本只作迁移来源。不能直接与 `1.0.0` 排序，也不能作为 NVIDIA `--previous-version`。只有已固定的可信旧源 commit 和完整目录摘要匹配迁移清单时，才能建议迁往新基线；更换版本格式本身不授权覆盖。
- `yomihime-init` 的 helper 将纯版本值比较与受保护目录检查分开；只有后者可提供内容指纹和候选建议。纯值比较无法确认内容、来源、本地改动或安装资格；同版不等于同内容。两者都不联网、不安装、不替换目录。实际源核验、权限、备份、并发复查、替换及回读仍由执行 Agent 依协议完成。本地定制、新增文件、未知基线、同版本内容漂移、回退和冲突都须保留并报告。详见该技能自包含的 [同步协议](./yomihime-init/references/skill-sync.md)。

### 使用者项目中的材料

项目内协作资料按需放入 `.agent-workspace/`，不是把技能包源码搬到这里：

```text
.agent-workspace/
  design/                    # 设计/文案指南与资源记录
  memory/                    # 当前状态与归档
  architecture/              # 仅在没有既有有效图源且确有需要时创建
  <work-id>/
    plan.md
    jobs/
    pipeline/
    scratch/
    artifacts.md
  runtime.md                 # 可选能力记录
  index.html                 # 流水线入口
```

保留名、固定根文件名、Windows 别名处理、工作区整理和单一权威图源规则以 [维护规范](./SKILL_STANDARD.md#项目工作区) 为准。不要预建所有目录或迁移已存在的有效图源；源码留在主 checkout，工作资料不自动提交、发布或删除。

### 真实运行要求

- 架构渲染与流水线 helper：Python 3.9+，仅标准库。字串完整扫描：Python 3.8+，仅标准库。这是代码/API 下限核对，不是最低版本实机测试证明。
- 修复前候选在 Linux x86_64、Python 3.12.14 和 3.13.5 上的 18 次 CLI 烟测全部通过；本次回归使用 Python 3.12。Python 3.8/3.9、macOS、原生 Windows 尚未实测；具体平台限制见各技能文档。
- planning、multi-agent、memory、UI 四个技能是文档指导，使用时不需要 Python。init 的指导可独立使用；可选 helper 使用 Python 3.10+ 标准库。纯版本值比较不依赖 POSIX，也不读取目录或给出安装决定；完整目录检查另需 POSIX no-follow 文件描述符能力。原生 Windows 的目录检查明确退出码 2、需人工或宿主工具核验，不使用不安全回退；原生 Windows、macOS 与 Python 3.10 最低版本均未实测。浏览器交互需 JavaScript；Node DOM 测试为可选开发验证，不是用户使用文档技能的先决条件。
- 测试子进程使用最小环境与超时。浏览器测试默认显式启用 Chromium sandbox；只有明确声明的隔离 Linux 容器测试才有受控例外，启动失败不自动降级。

## 评估结果（2026-11-04）

本次输入固定为修复提交 `3560987b63fa8697722169e99e9a516c67360806` 的八个技能目录。后续提交只整理本文件，不改变评估输入。修复包括字串截断边界、规划维护检查与提交分组规则、重复说明精简，以及架构派生报告、最终候选交付和记忆归档的说明。

### 本地回归

Python 测试共 **205 项：204 通过、1 项可选 Chromium 跳过**；3 套 Node DOM 检查通过。新增截断测试覆盖长度 1、2、3、4、80、100、101、非正数拒绝，以及 JSONL 保留完整文本。省略号计入长度上限，非正数在扫描前报错。

这些结果覆盖本次 Linux 环境下的脚本、文档约定和 DOM 逻辑。原生 Windows/macOS、最低 Python 版本、真实浏览器布局与 CSP、用户安装事务尚未验证。

### NVIDIA QUALITY 与第二阶段

使用 NVIDIA SkillEvaluator **0.7.2**，固定源码 `f878f99a9cd4a85dd04043feb43e5bd6a777f64b`。QUALITY 为不调用模型的文本与结构启发式检查；Tier 2 使用百炼 `text-embedding-v4` 和 `qwen-flash`。下表的 HIGH 是评估器报告的重复组数，不是人工确认的缺陷数。

| 技能 | QUALITY | Tier 2 结果 | HIGH 重复组 |
| --- | ---: | --- | ---: |
| architecture-design | 88.2 | failed | 3 |
| auto-style-string-resources | 93.5 | failed | 1 |
| development-pipeline | 88.2 | failed | 1 |
| interactive-planning-doc | 93.2 | failed | 8 |
| multi-agent-engineering | 89.0 | passed | 0 |
| project-memory | 85.0 | passed | 0 |
| ui-design | 86.5 | failed | 1 |
| yomihime-init | 83.8 | failed | 1 |

八项 QUALITY 均超过 70；本次只重跑 QUALITY，未重跑完整 Tier 1。Tier 2 的技能间相似度检查通过。技能内重复检查为 2 项 passed、6 项 failed，均已返回结果，没有因接口中断而缺项。

人工核对后保留了双语镜像、关键安全边界和独立安装所需说明。planning 的多数重复来自中英文对应章节；架构命中脚本入口、唯一图源与工作区说明；文案和 UI 命中指南入口；init 命中纯版本比较与受保护目录检查的边界；流水线命中 observer 契约和操作示例。部分概述已精简，必要重复仍保留。分类由模型参与，重复组数变化不能直接解释为内容质量变化。

官方默认技能间比较只提取名称和 description；`--full-body` 才加入 `SKILL.md` 正文，并不等于扫描整个技能包。技能内重复提取覆盖 Markdown、MDC、Python 和 shell 等受支持文件，去除 frontmatter，并按工具规则排除缓存及评测输出等目录；README 和双语镜像也会参与。百炼 embedding 每次最多 10 条，仓库外适配器把官方最多 64 条的请求保序分批，保留全部内容；离线验证覆盖分批边界、返回顺序和异常索引。

### Harbor 独立双臂行为试验

使用 Harbor **0.24.0** 的 `trial start`、Qwen Code **0.26.7**、百炼 `qwen-flash` 的 OpenAI 兼容 Chat Completions 接口。每项为一个独立合成案例，有 skill 与无 skill 两臂使用同一任务、模型和隔离条件，串行执行，单臂 agent 超时 180 秒，不自动重试。这是 Harbor 独立试验，**不是 NVIDIA 白名单 agent 的完整 Tier 3**。

每项两臂的有效性、独立检查与原始 overall 如下。独立检查记为「通过/总数；失败、未运行」，overall 按有 / 无 skill 顺序列出。无效试验的独立检查仅供诊断，不计有效成绩。

| 技能 | 有 skill | 无 skill | overall（有 / 无） | 触发确认 |
| --- | --- | --- | --- | --- |
| architecture-design | 有效；9/9；0 失败、0 未运行 | 有效；9/9；0 失败、0 未运行 | 0.96 / 1.0 | 评估器确认 |
| auto-style-string-resources | 有效；8/8；0 失败、0 未运行 | 有效；8/8；0 失败、0 未运行 | 0.64 / 1.0 | 未确认 |
| development-pipeline | 无效：AgentTimeoutError；2/5；0 失败、3 未运行 | 有效；4/5；1 失败、0 未运行 | 无效 / 1.0 | 未确认 |
| interactive-planning-doc | 有效；10/10；0 失败、0 未运行 | 有效；10/10；0 失败、0 未运行 | 0.6333 / 1.0 | 未确认 |
| multi-agent-engineering | 有效；5/6；1 失败、0 未运行 | 有效；4/6；2 失败、0 未运行 | 0.6 / 1.0 | 未确认 |
| project-memory | 有效；6/8；2 失败、0 未运行 | 有效；4/8；4 失败、0 未运行 | 0.64 / 0.8833 | 未确认 |
| ui-design | 有效；6/7；1 失败、0 未运行 | 有效；6/7；1 失败、0 未运行 | 0.595 / 1.0 | 未确认 |
| yomihime-init | 有效；6/8；1 失败、1 未运行 | 有效；6/8；1 失败、1 未运行 | 0.64 / 1.0 | 未确认 |

16 个臂中，15 个有效，1 个因 agent 超时无效。所有有效臂的安全与准确性维度均为 1；目标完成维度仅记忆基线为 0.3，行为维度仅 UI 有 skill 臂为 0.75，其余均为 1。独立检查发现：

- 架构、文案和规划两臂的独立检查全部通过。
- 流水线有 skill 臂超时，无有效成绩；基线通过四类行为测试，但交付记录中的最终候选哈希不匹配。
- 多 Agent 有 skill 臂未通过审查任务依赖检查；基线还未通过写入范围互不重叠检查。这些是任务包结构检查，未验证实际委派执行。
- 记忆两臂均未通过原快照与证据副本的逐字节检查；基线还缺少证据引用，当前快照未更新。
- UI 两臂均缺少案例明确要求的 `:focus-visible` 规则，其余六项检查通过。
- init 两臂均未通过离线就绪状态及未核验标记的组合断言；两项可用技能识别因 `TypeError` 未运行，其余六项通过。字段异常没有阻断后续独立检查。

两臂共同比较安全、准确性、目标完成与行为维度，并另列文件与行为断言。`overall` 在有 skill 臂额外包含技能执行和效率维度，不能相减后称为提升率。`skill_execution=0` 只表示评估器未确认触发，不能据此断定技能有缺陷。只有 agent 与 verifier 均完成的试验计为有效。

检查器把通过、失败、未运行和异常分开记录。缺少单个字段时继续运行其余独立断言；缺少整份报告时依赖该报告的检查标为未运行。离线正反例验证了缺失输出、字段短路和 UI 焦点规则。记忆案例使用完整的项目相对归档与证据路径，消除旧案例的路径歧义。init 案例仍有一处格式歧义：任务只规定 `available` 为数组，检查器却按字符串数组处理；返回其他元素类型时的 `TypeError` 记为未运行，不据此认定技能错误。检查仍以选定行为和结构为主，不能证明完整语义、视觉效果或实际子 Agent 委派。

### 本次调用用量

- Tier 2：embedding **76,081 token**；聊天输入 **40,084**、输出 **3,875**。
- Harbor agent（全部尝试，包括失败）：输入 **2,579,790**、输出 **25,505**；其中缓存输入 **2,367,422**，已包含在输入中，不重复相加。
- 已知聊天合计：输入 **2,619,874**、输出 **29,380**。每个 trial 只计一次顶层用量，不再叠加其模型明细。

Harbor verifier 的调用未提供独立 token 计量，上述聊天合计是已知下限。接口未返回可核实的费用金额，实际费用以百炼账单为准。修复前各轮的已知用量单列为聊天输入 5,267,985、输出 36,520、缓存输入 5,006,176，以及 embedding 76,513 token，未重复计入本次合计。

### 历史结果与适用范围

修复前 `abaa03f` 的完整 Tier 1 为 5 项 incomplete、3 项 failed：SkillSpector 均为 partial；文案和 init 的 Security Scan failed，planning 的 PII Scan 命中保留的作者邮箱。当前 QUALITY 结果没有覆盖或取消这些历史缺口。

Alibaba skill-up 0.14.0 的历史有效结果为 24/24：首次 23/24，修正 init 的 judge 关键词误判后定向重跑 3/3，其余沿用原快照。模型与 token 计量未确认，本次未重跑。修复前 Harbor 试验中也出现过接口不兼容、超时和检查器歧义；失败试验的 verifier 分数不计为有效，旧案例分数不与修订后的案例直接比较。

## 评估流程：先 skill-up 迭代，再 NVIDIA 检查

1. **确定候选和真实任务。** 固定仓库 SHA、工作副本差异、工具版本、权限边界与期望产物。为每个技能准备正常、负向、失败/降级和边界案例；不只检查答案有没有某个关键词。
2. **先用阿里 skill-up 做行为迭代。** 按官方当前配置接入可用执行器，记录实际模型、参数、case、judge、输入/输出、文件改动和退出码。先验证 judge 正反例，避免“正确行为因措辞没命中”或“只有承诺却判通过”。发现问题后修技能或 judge，并保留修改理由。
3. **完成针对性回归。** 修改 judge 时重跑其所有受影响案例；修改跨技能协议时扩大回归范围。发布前重跑完整相关 suite，旧结果、定向重跑和新全量结果分开记录。无法确认模型/token 时明确写未知，不补造计量。
4. **冻结内容，再跑 NVIDIA SkillEvaluator。** 每个技能分别执行：

   ```sh
   skillevaluator tier1 skills/<skill-name> --no-llm -r json -r html -o <仓库外报告目录>
   ```

   `skills/` 总目录不是单个技能。固定 profile、质量配置和门槛，保存退出码、JSON/HTML、工具版本与候选哈希。需要 LLM/Tier 2/Tier 3 时应单独约定执行条件，不能从 Tier 1 推断已跑过。
5. **解释分数并补覆盖。** 把真实缺陷、工具策略冲突、可复核误报和未覆盖项分开。对 JS 解析限制增加专用分析、source→sink 审查和可用的 DOM/浏览器回归；不能删测试、移走文件或降规则换 PASS。
6. **以最终候选重验并交付。** 修代码后跑相关测试，修文档后查链接、元数据与触发边界，再用同一冻结内容重新生成受影响报告。交付补丁、测试汇总和限制；原始证据按授权范围保存与分享。发布、推送、安装与 PR 均按另行授权执行。

评估入口：[Alibaba skill-up](https://github.com/alibaba/skill-up) · [NVIDIA SkillEvaluator 固定版本](https://github.com/NVIDIA/SkillEvaluator/tree/f878f99a9cd4a85dd04043feb43e5bd6a777f64b)。本文件中的分数是这一日期与候选的快照，后续修改不能继续沿用为最新通过证明。
