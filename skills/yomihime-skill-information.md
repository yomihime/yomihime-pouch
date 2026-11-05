# Yomihime Skill Information

把计划和交接的线索轻轻收好，留给下次开工的自己。这里是 yomihime 的小小工具箱，陪项目一点点完善。

本文介绍技能的公共约定、运行要求和评估结果。当前为 **1.0.0 候选基线**，版本号与本文不构成发布或安装证明；合并状态以 PR #9 的实际记录为准。作者：**yomihime（如月怜） <evenia@evenia.moe>**。技能目录和用途以 [技能目录](./README.md) 为入口，维护规则以 [SKILL_STANDARD.md](./SKILL_STANDARD.md) 为唯一权威；本文件提供导览，并记录指定候选的评估快照。

## 技能集合

| 技能 | 主要职责 | 不应混淆的边界 |
| --- | --- | --- |
| [architecture-design](./architecture-design/SKILL.md) | 梳理架构、边界、契约与有证据的图纸 | 不把目标设计或动画当成已实现事实 |
| [auto-style-string-resources](./auto-style-string-resources/SKILL.md) | 审计用户可见字串和文案指南，保留机器约束 | 结构检查不能证明文案语义或自然度 |
| [development-pipeline](./development-pipeline/SKILL.md) | 按依赖组织轮次、实现切片、检查点和证据 | 上报状态不等于独立验证，也不授权发布 |
| [interactive-planning-doc](./interactive-planning-doc/SKILL.md) | 前置调查与关键澄清，形成完整可交接主计划 | 完整草稿不代表全部就绪或获准实施 |
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
- 历史候选在 Linux x86_64、Python 3.12.14 和 3.13.5 上的 18 次 CLI 烟测全部通过；历史回归使用 Python 3.12。本轮原生 Windows 的部分通过、失败与跳过见下文，不据此承诺完整平台支持。Python 3.8/3.9 与 macOS 仍未实测。
- planning、multi-agent、memory、UI 四个技能是文档指导，使用时不需要 Python。init 的指导可独立使用；可选 helper 使用 Python 3.10+ 标准库。纯版本值比较不依赖 POSIX，也不读取目录或给出安装决定；完整目录检查另需 POSIX no-follow 文件描述符能力。原生 Windows 的目录检查明确退出码 2、需人工或宿主工具核验，不使用不安全回退；原生 Windows、macOS 与 Python 3.10 最低版本均未实测。浏览器交互需 JavaScript；Node DOM 测试为可选开发验证，不是用户使用文档技能的先决条件。
- 测试子进程使用最小环境与超时。浏览器测试默认显式启用 Chromium sandbox；只有明确声明的隔离 Linux 容器测试才有受控例外，启动失败不自动降级。

## 规划与交接语义移植及本机复核（2026-11-05）

本轮以 main `885a9cfb3556a9b936fa4c7f061f97e8a1bb1689` 为基准，将本地 `ccc91dccf3d609580d7d8b418a149c4b86784ed1` 中尚未等价合入的语义整理为候选 **`d6804e40f155a3b1d5b6e009af5f031ee95d2abd`**。下述结果只适用于该候选的技能内容；随后对本 information 文件的汇总编辑不改变技能目录。仍为未发布的 `1.0.0` 候选，四个受影响技能已刷新实际 `updated_at`，planning 中英文元数据一致。

### 内容与验证边界

规划流程现在强调：前置调查、必要的集中关键澄清、尽早形成完整主计划、检查交接条件。AI 自行核实工程事实与普通技术方案；已有完整计划的纯执行、小修复和单点问答仍可跳过规划。完整首稿不代表所有部分就绪或获准实施，不逐章审批，已有实施授权沿用；核心未决只阻止依赖范围，不能绕过既有轮次或失败屏障。

新增的 [计划模板](./interactive-planning-doc/assets/plan-template.md) 由 AI 填写与裁剪。流水线、任务交接和项目记忆引用同一主计划路径、修订和相关章节，后续变化先更新受影响计划再同步任务输入及证据。观察器逐步绘图与完整主计划独立；拓扑变化接续独立 run，保留旧状态。当前 `.agent-workspace/`、长期架构源、作者、权限和私有材料保护继续有效。

所有源码工作在原主 checkout 的新分支完成，没有复制仓库或额外 worktree；保留 `preserve/local-main-ccc91dc-20261105` 及原有未跟踪材料。一个新上下文审查者只读核对双语、模板、跨技能约定及已有授权、核心未决、小修复、在途修订四类情境，未发现 Blocker/Important。此为语义审查和情境推演，不是模型行为对照试验。

### 本机回归

环境为原生 Windows、Python **3.13.9**、Node **24.21.0**。先完整运行现有 Python suite **209 项**，再对新增三项文档契约运行最终 planning suite **10/10**。按最终各 suite 去重汇总为 **212 项：179 通过、3 失败、2 错误、28 跳过**；三套 Node DOM 检查通过。八个技能的 `quick_validate.py` 均通过；首次使用系统默认 GBK 时读取 UTF-8 失败，使用 Python 标准 `-X utf8` 后全部通过，未修改验证器。仓库级元数据、安装内引用和旧路径约束检查通过。

五个失败/错误出现在本轮未修改的实现和测试中：文案扫描三项路径断言收到 Windows 反斜杠；其环境白名单测试因 `SystemRoot` 大小写抛出 KeyError；流水线索引测试尝试创建含 `?`、`<`、`>` 的目录，触发 WinError 123。本轮不更改这些跨平台行为或放松断言，原始失败保留。跳过主要涉及 POSIX/no-follow、符号链接或可选浏览器能力。因此不能宣布全仓测试通过或完整 Windows 支持；DOM 检查也不证明浏览器布局、CSP 或端到端行为。

### Alibaba skill-up / skill-upper

使用官方 **skill-up 0.14.0 Windows amd64** 发布包并核对官方 SHA-256 校验和；按同版本 `skill-upper` 说明，为 planning、pipeline、multi-agent 和 memory 准备 **10 个案例**：完整首稿、核心取舍、已有授权、小修例外、草稿与同意、主计划与轮次、拓扑修订、任务包、记忆状态和定点更新。

初次配置验证指出 `agent_judge` 缺少 `judge.model`；仅修正评估配置，保留原日志。修正后 `validate` 加载 10 项通过，`list-cases` 与 `run --dry-run` 通过。配置为 OpenCode、百炼 **qwen-flash**，语义 judge 显式配置同一提供者/模型；没有使用本机默认模型替代百炼，也未运行无 skill 对照。

本机未发现已注入的百炼/OpenAI API 环境认证，按本轮边界没有读取凭据文件、私有会话或从云端转移 Network secret。**真实 agent/judge 执行、原版与候选行为比较、基于执行失败的 skill-upper 迭代均为 unrun**；本轮只完成案例、配置诊断修正、离线预检和独立语义审查。没有通过率、提升率或推理成绩，不能沿用历史结果作为本轮通过证明。

### NVIDIA 静态检查与 Tier 3 条件

使用 PyPI **SkillEvaluator 0.7.2**，external profile、默认 quality 配置、门槛 **70**、`--no-llm`，对八个技能分别运行完整 Tier 1 命令，生成 JSON/HTML。第一轮 Bandit/Gitleaks 缺失；在仓库外临时环境补齐 **Bandit 1.9.4**、**Gitleaks 8.30.0**（核对官方校验和）后，以同一冻结内容重跑八项，保留两轮报告，不跳过检查或修改规则。最终如下：

| 技能 | QUALITY | 完整 Tier 1 |
| --- | ---: | --- |
| architecture-design | 86.5 | incomplete |
| auto-style-string-resources | 93.5 | failed |
| development-pipeline | 88.2 | failed |
| interactive-planning-doc | 86.5 | failed |
| multi-agent-engineering | 89.0 | incomplete |
| project-memory | 85.0 | incomplete |
| ui-design | 86.5 | incomplete |
| yomihime-init | 83.8 | failed |

最终 **4 incomplete / 4 failed**；八项 QUALITY 超过 70，但不能称整体或安全门禁通过。八项 Bandit 与 Gitleaks 检查通过，SkillSpector **2.13.3** 仍报告 partial。文案的 E2/AR2 命中对应环境白名单测试及测试能力限制；planning 的 PII 命中保留的真实作者邮箱；init 的 TM1/SC2 对应明确禁止危险命令的规则。按实际状态保留，未删除规则、邮箱或测试以换 PASS。

流水线另命中本机已有的空 `scripts/__pycache__/`、`tests/__pycache__/` 目录（SC8）：其创建时间为 2026-10-30、最后修改 2026-10-31，早于本轮。遵守保留用户未跟踪材料的要求，没有清理它们；报告反映实际 checkout，不能把该命中归为本次新增源码或完整分发扫描已通过。QUALITY 为启发式信号，中文触发描述、外链示例及单一 `metadata.version` 可能与英文规则偏好不同，不为分数增设重复版本或虚假接口。 planning 本轮为 86.5；报告扣分项包括未识别示例、WHEN/Purpose、错误处理/验证、前置条件和限制等英文锚点，以及根级 version。相关中文边界与外置模板实际存在，不能据此推断行为退化，也不补重复英文段落换分。

**Tier 2 与技能间 embedding 比较未运行**，原因同上。官方 Tier 3 `doctor` 已实际执行，因缺少 Harbor 模块而退出 1；本机也未提供 Docker 命令。没有改写 HOME、放宽权限或替换官方运行路径。Tier 3 agent/verifier 两臂均未启动，**scored attempts=0**，分数、触发确认和 lift 均不可用；这是预检失败，不是完成了一次双臂评估。

### 用量、证据与后续

本轮上述评估器实际推理调用 **0**，聊天输入/输出、embedding token 均 **0**；配置中的 qwen-flash 没有成为实际执行模型。该计数不包含本次 Codex 编辑与独立审查，宿主未提供它们可单列的模型/用量；不能据此宣称整个任务费用为零。

原始报告、案例、配置失败与修正日志、目录内容指纹和审查回执保留在执行本机的仓库外目录 `C:/Users/eveni/AppData/Local/Temp/codex-planning-port-20261105-0130/`，不随 PR 发布。`frozen-skills.json` 记录按相对路径排序的非缓存文件 SHA-256 清单，扫描前后逐文件复核未变；NVIDIA JSON 另保留自身 source-tree/2 摘要与覆盖状态。没有发布用户材料或秘密。

后续在获准且能安全注入百炼认证的环境执行同一 suite 的原版/候选比较和完整相关回归，再执行 NVIDIA Tier 2；Tier 3 还需受支持的 Harbor、容器运行时和模型路径。当前只交付可审阅候选与真实验证记录，PR 保持 draft，不合并或发布。

## 解析边界修复与回归（2026-11-05）

基于 PR #9 的 `8afc84c4e71ed8cd2ec08d19207eed0a1754ba24` 复现：description 多行块首行缩进 2 空格、后续非空行仅 1 空格时，旧 helper 仍读出版本。现按首个非空内容行确定隐式块缩进，拒绝非法退缩及过深的前置空白行；块内 `#` 按文本处理，块外注释结束块，不能继续接受缩进内容。合法 literal/folded 的六种现有标记、1/2/4/8 空格缩进、空行与更深内容均有正例。没有新增依赖或扩展为通用 YAML 解析器。

非法块在 `inspect`、本地或候选侧的 `compare` 均返回 `unknown`、退出码 2，保留输入文件；不再给出正常版本建议。纯值比较、POSIX no-follow 限制及原生 Windows 目录核验不支持的边界不变。init 的 `metadata.updated_at` 随脚本与测试修改更新，未发布候选的版本仍为 `1.0.0`。

本次 Linux / Python 3.12.14 回归共 **209 项：208 通过、1 项可选 Chromium 跳过**，其中 init **40 项全部通过**；Node 24.22.1 的 3 套 DOM 回归及 7 个 JS/CJS 文件语法检查通过。浏览器测试显式启用后因最小子进程环境无法解析 Playwright 而跳过，没有放宽 sandbox。

本次未重跑 skill-up、NVIDIA QUALITY / Tier 1 / Tier 2 / Tier 3 或 Semgrep。下文分数、覆盖率和模型结果仍为对应历史冻结输入的快照；init 输入已变化，不能把历史 83.8 或扫描状态标为本次重新取得的结果。完整安全门禁未由本次功能回归补齐。原生 Windows/macOS、最低 Python 版本、真实浏览器/CSP/布局和安装/恢复事务仍未覆盖。

## 精简与评估快照（2026-11-04）

技能输入冻结在 `b82cd4771044ca66544ff3b781e2c5973005afe8`，基线为 PR #9 的 `fa38c2a22ef1c4281c2ff4ac70ff4a15611e7095`。此后截至 `8afc84c` 只更新本导览，八个技能目录未变；2026-11-05 的 init 修复另见上节。本轮修正架构 README 的悬空命令指引，脚本命令集中到示例页；精简文案指南导览及 observer 重复协议，完整保留操作、恢复、授权与私有材料保护。保留名规则移入观察器契约，未删除；该轮 UI、init 及 planning 中英文镜像未作内容改动。

### 阿里 skill-up → skill-upper 迭代

使用官方发布的 **skill-up 0.14.0**（安装器校验 checksum），按官方 **skill-upper** 源码 `4234ca279c573369e71f480849bc6b021ee14107` 的诊断、修订、同例回归流程执行。执行器为官方支持的 local custom engine，调用百炼 **qwen-flash**，temperature=0、max_tokens=1400、单请求超时 90 秒、单案例 110 秒、不自动重试。源文本显式装入上下文；没有测试宿主自动触发、文件写入、安装或真实多 Agent 调度，不是 Qwen Code 或 NVIDIA Tier 3。

12 项动作集合案例覆盖：既有架构源保护、预览输出冲突、只审计与获准改字串、失败后的在途回报、投影与索引恢复、UI/init 指南冲突、同版漂移、docs-only、记忆交接、quiesced 与小改动边界。每题同时包含允许和禁止的动作，精确比较完整集合；全拒绝或全接受均失败。另加 consulting/blocked 两项结构化状态断言，检查接收终态后的状态、新工作禁令及 quiesced 是否终止进程。

| 轮次 | 动作集合 | 状态事实 | 说明 |
| --- | --- | --- | --- |
| 基线，修正评测设置后 | 12/12 | 1/2 | consulting 被错写为 needs_decision |
| 精简初版 | 12/12 | 0/2 | 分别错写 running、needs_decision |
| 增补状态转换表，最终全量 | 12/12 | 2/2 | 14 项全部通过，未降判定标准 |

诊断发现“动作选择正确”不能证明解释和状态字段正确，因此没有把第一轮 12/12 当作完整通过。契约新增三行状态表，强调节点结果与运行状态是不同字段；同一断言在最终全量回归中通过。随后按 NVIDIA 重复组诊断再次缩短架构 README 的目录细则，保留关键边界并链接原契约；重跑全部 4 个使用架构文本的案例，4/4 通过，其余 10 项输入不变沿用最终全量结果。这里只能说明这批合成案例的单次结果，不能推断泛化成功率、触发率或可靠提升幅度。

评测设置的失败单独保留：两个探针分别遇到输出目录缺失、输出文件未声明；首次 12 案例另有 3 项因误列不存在的 init README 出错，3 项因 JSON 代码围栏被严格解析拒绝。修复清单及围栏解析后，两版重新全量运行；未将这些错误记为技能成绩。动作 judge 做了 48 项正反/围栏检查，状态 judge 做了 10 项正反检查。最终 14 项没有执行错误或超时；原始响应及评测元数据保留在仓库外，不发布。

### 本轮本地检查

Python **205 项：204 通过、1 项可选 Chromium 跳过**；3 套 DOM 回归、4 个 JS 文件语法检查通过。契约最后修改后再跑流水线 61 项（60 通过、1 跳过）。本地 Markdown 路径与锚点检查通过；不以本地链接检查冒充外部网站可用性或浏览器视觉验收。原生 Windows/macOS、最低 Python 版本与真实安装事务未覆盖。

### 本轮 NVIDIA 冻结检查

使用 NVIDIA SkillEvaluator **0.7.2 / f878f99a9cd4a85dd04043feb43e5bd6a777f64b**，Tier 1 为 external profile、默认质量配置、门槛 70、`--no-llm`。Tier 2 使用 **qwen-flash + text-embedding-v4**，默认阈值 0.8；技能间名称/description 比较阈值 0.75。三个受影响技能重跑 Tier 2，另外五个不沿用旧分数冒充新结果。

| 技能 | QUALITY | 完整 Tier 1 | 本轮 Tier 2 / HIGH |
| --- | ---: | --- | --- |
| architecture-design | 86.5 | incomplete | failed / 2 |
| auto-style-string-resources | 93.5 | failed | passed / 0 |
| development-pipeline | 88.2 | incomplete | failed / 1 |
| interactive-planning-doc | 93.2 | failed | 未重跑 |
| multi-agent-engineering | 89.0 | incomplete | 未重跑 |
| project-memory | 85.0 | incomplete | 未重跑 |
| ui-design | 86.5 | incomplete | 未重跑 |
| yomihime-init | 83.8 | failed | 未重跑 |

架构 QUALITY 从历史 88.2 降为 86.5：入口命令代码块移到已链接的示例页后，启发式判为缺少 examples。保留实际可用的导航，不补虚构 run_script 或第二版本字段换分。Tier 2 文案原指南重复组已消失；架构仍命中用途导览、唯一源及生命周期概述，流水线改为命中切片设计与契约的轮次原则。人工核对后保留这些职责不同的必要说明，不将模型 HIGH 等同真实缺陷。最终八技能名称/description 相似度检查通过；未做 full-body 技能间比较。

完整 Tier 1 为 **5 incomplete / 3 failed**，八项 QUALITY 均超过 70，但不能称安全门禁通过。使用 SkillSpector **2.13.3**、Gitleaks **8.30.0** 与 Bandit；SkillSpector 均报告 partial。文案测试中的 `os.environ.items()` 和 “do not judge” 命中，init 的禁止 `git reset --hard` / `curl | sh` 规则命中，planning 保留作者邮箱的 PII 命中均按失败保留。文案两处命中分别是最小环境白名单测试、测试不判断文案自然度的能力限制；init 两处是显式禁止危险操作，语境不支持直接认定恶意行为，但扫描失败和不完整状态仍保留。Semgrep 本轮未安装，其可选检查未覆盖；历史独立 JS 分析不能替代当前扫描完整性。

运行问题与处理单列：初次扫描器默认安装目录只读；通过官方支持的 runtime/cache 目录安装后，uv 子进程的隔离环境仍缺少缓存配置，改用官方支持的扫描器可执行路径配置。未改扫描规则或隔离设置。架构测试生成的未跟踪 `__pycache__` 一度触发分发内容命中；只清理本轮缓存后重跑，最终表使用干净源码结果，源码与测试均保留。

embedding 本地适配仅将请求保序切成至多 10 条，沿用官方向量索引校验；0、1、10、11、25 条及响应乱序测试通过，没有截断输入。初轮未执行官方 Tier 3，随后补试的实际结果见下节。Harbor 独立双臂未重跑；历史超时、触发未确认与检查器缺陷仍保留，不能由本轮文本案例推出这些缺口已修复。

### 本轮用量与限制

- skill-up：57 个已计量响应，输入 **519,620**、输出 **5,645 token**，包括报告设置失败探针、诊断轮与回归；另有 1 次早期探针在报告写入前失败，其 token 未留存，不能补算。最终 14 项全量运行输入 129,710、输出 1,516；后续 4 项定向回归已包含在上述合计内。
- NVIDIA Tier 2 与相似度检查：embedding **43,684 token**，聊天输入 **16,911**、输出 **1,679 token**，包含架构目录段再次精简后的重跑。Tier 1 不调用模型。
- 已知聊天合计输入 **536,531**、输出 **7,324 token**；因早期探针缺计量，这是下限。未单列缓存 token，未重复相加；接口未提供可核验金额，费用以百炼账单为准。

上述文本评测和 Tier 2 没有 API 超时或最终案例执行错误；官方 Tier 3 补试在启动阶段失败，未形成有效成绩。原始响应、报告和元数据不随 PR 发布；本文件只记录可公开的输入版本、方法、结果与限制。

### Tier 1 细分原因补查

最终 Tier 1 的三个 failed 分别由以下阻断项造成；八项同时含 SkillSpector partial，QUALITY 达标不会覆盖这些状态。

| 技能 | 阻断规则与位置 | 语境核对 |
| --- | --- | --- |
| auto-style-string-resources | E2：`tests/subprocess_support.py:14`；AR2：`tests/test_string_helpers.py:4` | 环境遍历实际为白名单过滤；“do not judge”说明测试不判断文案自然度。属于语境误报，原失败状态保留 |
| interactive-planning-doc | PII `emails`：`SKILL.en.md:7` | 作者邮箱是真实地址，用户明确要求保留；检测正确，但与作者元数据要求冲突 |
| yomihime-init | TM1：`SKILL.md:78`；SC2：`references/skill-sync.md:94` | 两处均明确禁止危险命令；不能解释为要求执行，原失败状态保留 |

以相同 SkillSpector 2.13.3、`--no-llm` 对干净技能目录补查，八项均 `execution_successful=true`。细分账本如下；百分比为扫描器报告的文件覆盖，不是安全成功率。

| 技能 | 文件覆盖率 | reference_missing | static_parse_limit |
| --- | ---: | ---: | ---: |
| architecture-design | 89.5% | 3 | 2 |
| auto-style-string-resources | 100% | 9 | 0 |
| development-pipeline | 91.3% | 5 | 2 |
| interactive-planning-doc | 100% | 4 | 0 |
| multi-agent-engineering | 100% | 2 | 0 |
| project-memory | 100% | 2 | 0 |
| ui-design | 100% | 4 | 0 |
| yomihime-init | 100% | 6 | 0 |

`reference_missing` 出现在运行时 `.agent-workspace/`、`AGENTS.md` 等路径，以及 API 名或数字版本所在行；它不等于 Markdown 链接断裂，也不要求为扫描器伪造这些项目文件。静态解析跨度限制涉及架构的 `assets/viewer.js`、`tests/test_viewer_dom.cjs`，以及流水线的 `assets/observer/app.js`、`tests/test_index_dom.cjs`。这是实际静态覆盖限制，DOM 通过不能将其改写成完整安全扫描通过。未启用的语义 LLM 分析器也不在本轮覆盖内。

### 官方 Tier 3 小规模补试

在前述未执行说明之后，实际使用固定 **SkillEvaluator 0.7.2 / f878f99、Harbor 0.24.0** 补试 `development-pipeline`。官方 agent 选择 **OpenCode**，模型参数 **openai/qwen-flash**，provider 为百炼 OpenAI-compatible；未使用 Qwen Code 或独立 Harbor 试验冒充官方路径。OpenCode 尚未进入容器安装执行阶段，未取得其实际版本。

一个合成案例 `inflight-state-retention` 同时包含 consulting 下接收 passed、blocked 下接收 failed 两条记录，要求写出决策 JSON。两臂使用同一案例，attempts=1、concurrency=1、max-cases=1、timeout-multiplier=0.6，保留 baseline，采用官方 `default_plus_custom`。附加判定检查两条记录完整性、状态保留、接收终态、新工作禁令与 quiesced 无终止副作用；离线正例、缺失产物、错误状态检查通过。数据集与 grader 契约验证通过，未执行任何评分标准降级。

实际运行经过以下阶段：

- Docker **29.9.2**、Compose **2.40.3**、Harbor 与官方 doctor 通过；OpenCode 模型配置被解析接受。独立容器中宿主 checkout 不可见，经既有代理及只读 CA 挂载访问百炼得到未认证 401，证明网络/TLS 路径可达，不证明推理凭据或完整 agent 路由成功。
- 第一次官方 evaluate 因默认状态目录只读而停止；改用官方支持的 `XDG_STATE_HOME` 后再次执行。官方实时目录验证提示“不能证明运行凭据”，按其 degraded 路径继续。
- 第二次已规划有技能和无技能两臂，但 Harbor CLI 的首次通知逻辑硬编码写入 `~/.cache/harbor/notifications.json`，home 为只读，返回 Errno 30。两臂均在 trial 启动前失败，没有 agent 或 verifier 成绩。

最终官方报告为 **INCOMPLETE**，机器字段 `execution_status=failed`，**expected_attempts=2、scored_attempts=0**；两臂分数均不可用，触发状态 unknown，lift 未测量。这是本轮确实执行后的环境阻碍，不是沿用历史失败。未改写 HOME、放宽权限或补丁绕过缓存限制；继续需要环境提供可写的默认 Harbor 缓存位置，或上游提供受支持的缓存路径配置。

此次补试新增 agent/verifier 推理调用 **0**，没有新增已计量聊天或 embedding token；模型目录/连通性检查不作为推理成绩，也不据此声称账单金额为零。原始任务、报告与元数据保留在仓库外，只发布本汇总。评测专用临时文件已从技能目录移出，运行技能内容仍为 `b82cd4771044ca66544ff3b781e2c5973005afe8`。PR 描述更新此前失败，本次未重试或换路。

## 历史评估（2026-11-04，3560987）

本节历史输入固定为修复提交 `3560987b63fa8697722169e99e9a516c67360806` 的八个技能目录。后续提交只整理本文件，不改变评估输入。修复包括字串截断边界、规划维护检查与提交分组规则、重复说明精简，以及架构派生报告、最终候选交付和记忆归档的说明。

### 本地回归

Python 测试共 **205 项：204 通过、1 项可选 Chromium 跳过**；3 套 Node DOM 检查通过。新增截断测试覆盖长度 1、2、3、4、80、100、101、非正数拒绝，以及 JSONL 保留完整文本。省略号计入长度上限，非正数在扫描前报错。

这些结果覆盖该轮 Linux 环境下的脚本、文档约定和 DOM 逻辑。原生 Windows/macOS、最低 Python 版本、真实浏览器布局与 CSP、用户安装事务尚未验证。

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

八项 QUALITY 均超过 70；该轮只重跑 QUALITY，未重跑完整 Tier 1。Tier 2 的技能间相似度检查通过。技能内重复检查为 2 项 passed、6 项 failed，均已返回结果，没有因接口中断而缺项。

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

### 该轮调用用量

- Tier 2：embedding **76,081 token**；聊天输入 **40,084**、输出 **3,875**。
- Harbor agent（全部尝试，包括失败）：输入 **2,579,790**、输出 **25,505**；其中缓存输入 **2,367,422**，已包含在输入中，不重复相加。
- 已知聊天合计：输入 **2,619,874**、输出 **29,380**。每个 trial 只计一次顶层用量，不再叠加其模型明细。

Harbor verifier 的调用未提供独立 token 计量，上述聊天合计是已知下限。接口未返回可核实的费用金额，实际费用以百炼账单为准。修复前各轮的已知用量单列为聊天输入 5,267,985、输出 36,520、缓存输入 5,006,176，以及 embedding 76,513 token，未重复计入该轮合计。

### 历史结果与适用范围

修复前 `abaa03f` 的完整 Tier 1 为 5 项 incomplete、3 项 failed：SkillSpector 均为 partial；文案和 init 的 Security Scan failed，planning 的 PII Scan 命中保留的作者邮箱。该轮 QUALITY 结果没有覆盖或取消这些历史缺口。

Alibaba skill-up 0.14.0 的历史有效结果为 24/24：首次 23/24，修正 init 的 judge 关键词误判后定向重跑 3/3，其余沿用原快照。模型与 token 计量未确认，该轮未重跑。修复前 Harbor 试验中也出现过接口不兼容、超时和检查器歧义；失败试验的 verifier 分数不计为有效，旧案例分数不与修订后的案例直接比较。

## 评估流程：先 skill-up / skill-upper 迭代，再 NVIDIA 检查

1. **确定候选和真实任务。** 固定仓库 SHA、工作副本差异、工具版本、权限边界与期望产物。为每个技能准备正常、负向、失败/降级和边界案例；不只检查答案有没有某个关键词。
2. **先用阿里 skill-up，再按 skill-upper 诊断迭代。** 按官方当前配置接入可用执行器，记录实际模型、参数、case、judge、输入/输出、文件改动和退出码。先验证 judge 正反例，避免“正确行为因措辞没命中”或“只有承诺却判通过”。发现问题后修技能或 judge，并保留修改理由。
3. **完成针对性回归。** 修改 judge 时重跑其所有受影响案例；修改跨技能协议时扩大回归范围。发布前重跑完整相关 suite，旧结果、定向重跑和新全量结果分开记录。无法确认模型/token 时明确写未知，不补造计量。
4. **冻结内容，再跑 NVIDIA SkillEvaluator。** 每个技能分别执行：

   ```sh
   skillevaluator tier1 skills/<skill-name> --no-llm -r json -r html -o <仓库外报告目录>
   ```

   `skills/` 总目录不是单个技能。固定 profile、质量配置和门槛，保存退出码、JSON/HTML、工具版本与候选哈希。需要 LLM/Tier 2/Tier 3 时应单独约定执行条件，不能从 Tier 1 推断已跑过。
5. **解释分数并补覆盖。** 把真实缺陷、工具策略冲突、可复核误报和未覆盖项分开。对 JS 解析限制增加专用分析、source→sink 审查和可用的 DOM/浏览器回归；不能删测试、移走文件或降规则换 PASS。
6. **以最终候选重验并交付。** 修代码后跑相关测试，修文档后查链接、元数据与触发边界，再用同一冻结内容重新生成受影响报告。交付补丁、测试汇总和限制；原始证据按授权范围保存与分享。发布、推送、安装与 PR 均按另行授权执行。

评估入口：[Alibaba skill-up](https://github.com/alibaba/skill-up) · [NVIDIA SkillEvaluator 固定版本](https://github.com/NVIDIA/SkillEvaluator/tree/f878f99a9cd4a85dd04043feb43e5bd6a777f64b)。本文件中的分数是这一日期与候选的快照，后续修改不能继续沿用为最新通过证明。
