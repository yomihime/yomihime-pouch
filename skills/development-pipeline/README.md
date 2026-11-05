# development-pipeline

将需求拆成里程碑、可验收切片和角色任务，用顺序轮次、轮内并行与检查点推进到用户约定的交付终点。

每轮有 1-n 个可并行任务及必要的有序检查点；本轮任务和检查点满足条件才开放下一轮。失败由主调度者选择顾问介入、返回指定轮次或记录阻塞，保留失败历史。验证和审查绑定真实候选，不能把局部通过当成集成交付通过。

每个项目的 `.agent-workspace/index.html` 是固定入口，汇集活动运行和已完成或过期的历史运行，并链接到各运行的观察页或最终报告。运行详情按项目与运行隔离：规划时逐步显示流程，执行时读取相邻数据脚本，完成后停止刷新并生成单文件最终报告。索引和详情均由事件派生，显示上报事实而非进程存活证明。Python 标准库 CLI 记录事件并更新投影，默认无需服务、端口、前端构建或第三方依赖；它不代替 Agent 调度与实际测试。

可与 multi-agent-engineering 的 task-handoff-v1、project-memory 的 knowledge-extract-v1 配合，也可由单 Agent 顺序执行。架构变化可按需使用 `architecture-design`，把必要视图、契约和验证证据关联到已有切片与检查点；小任务不强制完整架构阶段，缺少配套技能时按现有证据有界分析。配套技能、子 Agent、目标环境和独立审查是否实际可用须如实说明。跨任务图纸复用既有唯一源；无源时按需使用 `.agent-workspace/architecture/`，从稳定项目入口引用并交接修订与 owner，不随运行清理或复制到另一份 project-memory 图源。

```text
使用 $development-pipeline，将这个功能拆成可验收切片。
明确里程碑、依赖层次、当前执行轮次和质量检查；按已有权限推进到本地已验证候选。
```

- `SKILL.md`：范围、阶段与质量边界。
- `references/slicing.md`：需求拆片、依赖、轮次和可开工输入。
- `references/quality.md`：验收矩阵、候选证据、独立审查和失效复验。
- `references/delivery.md`：交付终点、失败回流与记忆/资源收束。
- `references/observer.md`：项目固定入口、观察器启动、上报与每步对话汇报。
- `references/observer-contract.md`：命令、事件投影与轮次状态约束。
- `scripts/pipeline.py`：事件记录、状态校验、静态页面/报告及可选只读服务。
- `assets/observer/`：复用的观察网页；`assets/demo-plan.json`：合成示例计划。
- `tests/test_pipeline.py`：状态、并发记录及 HTTP 边界测试。
- `agents/openai.yaml`：技能展示元数据。

按需使用既有计划与工作区，不生成项目源码布局、CI 或发布配置，不自动提交、推送、安装、发布或清理。技能规则提供可追溯质量控制，不证明未执行测试通过，也不保证零缺陷。实际项目材料保持本地私有。

## 运行条件与触发边界

观察器 CLI 需要 Python 3.9+ 标准库和 assets；文件锁使用 POSIX fcntl 或 Windows msvcrt。 具体触发正反例、平台限制与实测范围见 [SKILL.md](SKILL.md#触发示例与运行要求)。
