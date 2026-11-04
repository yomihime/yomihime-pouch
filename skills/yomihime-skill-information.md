# Yomihime Skill Information

本文件介绍 yomihime 的技能集合、公共约定和评估方法。本轮是 **1.0.0 待审候选**；提交或 draft PR 不代表已合并、已发布或已安装。作者：**yomihime（如月怜） <evenia@evenia.moe>**。技能目录和用途以 [技能目录](./README.md) 为入口，维护规则以 [SKILL_STANDARD.md](./SKILL_STANDARD.md) 为唯一权威；本文件是导览和带日期的评估快照，不建立第二套运行协议。

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
| [yomihime-init](./yomihime-init/SKILL.md) | 检查所需技能、版本和安全工作区布局 | 不覆盖本地定制，不用失联网冒充检查成功 |

每个技能都可以单独安装。跨技能协作是可选能力，不能把本文件或相邻技能变成未声明的运行依赖。详细触发正反例和权限边界见各技能自身的 `SKILL.md`。

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
- 本轮在 Linux x86_64、Python 3.12.14 和 3.13.5 做了 18 次 CLI 烟测，全部通过。Python 3.8/3.9、macOS、原生 Windows 尚未实测；具体平台限制见各技能文档。
- planning、multi-agent、memory、UI 四个技能是文档指导，不凭空声明 Python 运行依赖。init 的指导可独立使用；可选 helper 使用 Python 3.10+ 标准库。纯版本值比较不依赖 POSIX，也不读取目录或给出安装决定；完整目录检查另需 POSIX no-follow 文件描述符能力。原生 Windows 的目录检查明确退出码 2、需人工或宿主工具核验，不使用不安全回退；原生 Windows、macOS 与 Python 3.10 最低版本均未实测。浏览器交互需 JavaScript；Node DOM 测试为可选开发验证，不是用户使用文档技能的先决条件。
- 测试子进程使用最小环境与超时。浏览器测试默认显式启用 Chromium sandbox；只有明确声明的隔离 Linux 容器测试才有受控例外，启动失败不自动降级。

## 评分信息（2026-11-04 候选快照）

评分回答不同问题：阿里 skill-up 用于行为案例迭代；NVIDIA QUALITY 是文本/结构启发式，不是模型成功率；完整 Tier 1 另含元数据、版本与安全检查。QUALITY 过线不等于全套通过。

### 历史行为评估

Alibaba skill-up 0.14.0 的历史有效结果为 24/24：首次全量 23/24，修正 init 的 judge 关键词误判后定向重跑 3/3，其他结果沿用原快照。模型、思考深度和 token 计量未确认。本轮未重跑这套行为测试，不能把历史结果当作当前候选成绩。

### 本轮 NVIDIA 与验证

NVIDIA SkillEvaluator 0.7.2，external profile，QUALITY 门槛 70，未调用 LLM。各技能分别检查，结果如下：

| 技能 | 当前 QUALITY | 完整 Tier 1 |
| --- | ---: | --- |
| architecture-design | 88.2 | incomplete |
| auto-style-string-resources | 93.5 | failed |
| development-pipeline | 88.2 | incomplete |
| interactive-planning-doc | 93.2 | failed |
| multi-agent-engineering | 89.0 | incomplete |
| project-memory | 85.0 | incomplete |
| ui-design | 86.5 | incomplete |
| yomihime-init | 83.8 | failed |

八项版本、Schema 与 QUALITY 门禁均通过；完整 Tier 1 为 **5 项 incomplete、3 项 failed**，没有完整通过项。SkillSpector 全部 partial；strings/init 的 Security Scan failed，planning 的 PII Scan 命中保留的准确作者邮箱。安全检查缺口没有用独立补证改写为通过。

七项 QUALITY 与上一轮相同；init 从 90.8 变为 83.8。新真实脚本触发两条启发式扣分：评估器不识别已有中文/双语脚本表标题，并要求实际不存在的 run_script 包装。不伪造接口或为分数隐去限制；其他分数也不代表模型行为提升。

- 最终 Python 回归 **202 项，201 通过、1 项可选 Chromium 跳过**；3 套 DOM、6 项 JS 语法、7 条安全规则正反例通过。
- 18 次双 Python CLI、8 次文档真实示例、48 次目录 helper 检查、24 次纯值 CLI 检查通过；非法值按预期拒绝。实际解释器为 Linux 上 Python 3.12/3.13，模拟平台检查不等于原生 Windows 实测。
- 16 项真实 HTML 集成通过。68 条 JS 规则检查 6 个原文件，未报告 finding/顶层 error，但本轮有 10 种 fixpoint-warning 规则，不能称完整数据流安全通过。
- init 最后变更后定向重跑 NVIDIA，并重跑全量功能测试；其余技能及 HTML/JS 输入逐项确认未变后复用相应结果。原始证据单独保留，公开文档只给必要摘要。
- 原生 Windows/macOS、最低 Python 3.8/3.9/3.10、真实模型路由、真实浏览器/CSP/布局和用户安装事务未验证。Windows 纯版本值比较不读目录、不授权更新；完整目录检查明确不支持原生 Windows，需可靠宿主工具人工核验，不能用纯值结果替代。

本轮保留作者、字串扫描/JSONL、子进程隔离与超时、JS/DOM 验证及技能触发边界改进，再加入版本/更新时间与安全迁移协议。当前仅为供审阅的 1.0.0 候选，没有 merge、release/tag、部署或用户技能目录安装。

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
6. **以最终候选重验并交付。** 修代码后跑相关测试，修文档后查链接、元数据与触发边界，再用同一冻结内容重新生成受影响报告。完整交付补丁、修改文件、原始证据和限制。发布、推送、安装与 PR 均按另行授权执行。

评估入口：[Alibaba skill-up](https://github.com/alibaba/skill-up) · [NVIDIA SkillEvaluator 固定版本](https://github.com/NVIDIA/SkillEvaluator/tree/f878f99a9cd4a85dd04043feb43e5bd6a777f64b)。本文件中的分数是这一日期与候选的快照，后续修改不能继续沿用为最新通过证明。
