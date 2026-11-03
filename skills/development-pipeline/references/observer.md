# 静态观察页与上报

默认使用本地 HTML + CSS + JavaScript，不需要 HTTP 服务、端口、前端构建或常驻 Python。每次上报命令追加事件后更新本次运行的 state.js；页面加载同目录的经典脚本来取得状态，不用 file:// fetch，不要求放宽浏览器安全设置。浏览器对本地文件 fetch 有限制，经典脚本的嵌入规则见 [MDN 同源策略](https://developer.mozilla.org/en-US/docs/Web/Security/Defenses/Same-origin_policy)。

## 按项目和运行隔离

每个项目使用自己的 .agent-work/<work-id>/pipeline/，不同工作使用不同 work-id，不复用已经完成的目录。项目固定入口为 .agent-work/index.html；它是从该项目运行事件重建的只读索引，不是跨项目注册表。init 固定项目身份与随机 run_id，运行详情页校验两者；不使用 localStorage。相同名字的两个项目、相同 work-id 也不共用事件、锁或页面。此隔离是路径、数据与运行身份的隔离，不是操作系统权限沙箱。

```text
.agent-work/
  index.html                     项目固定入口（事件派生的运行索引）
  pipeline-index-data.js         由事件重建的索引数据
  <work-id>/pipeline/
    events.jsonl                 唯一机器事件源
    .pipeline.lock               跨进程读写锁
    observer/
      index.html                 本次运行的观察页面
      app.js                     预制显示逻辑
      styles.css                 预制样式
      state.js                   事件派生数据，原子替换
    report.html                  完成后自动生成，单文件最终报告
```

这些实际运行材料和索引本地私有，按 multi-agent-engineering/project-memory 保护，不暂存、提交或上传。预制组件由工具复制，不要求 LLM 编写前端。各运行 events.jsonl 是事实来源，索引、页面和报告可重建，不是另一份人工项目记忆。

## 一次初始化，直接打开文件

```powershell
$pipeline = "skills/development-pipeline/scripts/pipeline.py"
$runDir = ".agent-work/当前任务/pipeline"
python -X utf8 $pipeline init $runDir --title "当前任务" --project-root .
```

打开项目 .agent-work/index.html，选择运行进入其观察页；已完成的运行链接到单文件报告。也可直接打开命令输出的 observer/index.html。省略 --project-root 时，从运行目录的 .agent-work 祖先识别项目根；不在该布局时采用运行目录的父目录。显式指定时要求运行目录位于该项目内。项目身份固定在初始化事件中，旧日志未记身份时显示未记录，不猜成当前项目。

索引扫描项目 .agent-work 下的运行并重放非符号链接事件日志；不可读或损坏的日志显示读取失败，不以缓存状态冒充当前事实。completed 列为已归档，未完成且距最后事件至少 7 天列为过期，其余列为活动。归档和过期是索引分类，不移动或删除运行；过期只表示事件数据久未更新，不能证明执行者已停止，活动也不能证明进程存活。事件更新和 view 会重建索引数据，索引页每 5 秒读取该数据并按当前时间分类；需要手动重建时运行：

```powershell
python -X utf8 $pipeline index .
```

运行详情页每 1.5 秒读取自己的 state.js，仅事件版本变化时重绘；单次读取超时 8 秒，独立检查 10 秒未成功读取的数据异常，保留旧图与最后成功时间。没有新事件不等于执行者离线，页面不探测真实进程。浏览器若禁止本地脚本，可用下文可选 HTTP 模式，不更改浏览器安全设置。

## 规划时逐步画出

计划字段见 [契约](observer-contract.md)。主调度者根据需求和验收形成计划 JSON，可将短暂输入文件留在本批获准 scratch/；每次形成一组结构决定就上报，页面随事件扩展，不逐字制造进度动画。

```powershell
python -X utf8 $pipeline plan $runDir --file PLAN_JSON
python -X utf8 $pipeline status $runDir --mermaid
python -X utf8 $pipeline start $runDir
```

草案可不完整，start 才校验每轮有任务、最后轮有必需测试/审查、ID 唯一及有效返回位置。执行后结构冻结；任务有串行依赖就安排不同轮。重大重规划先停止/交接在途工作，保留旧运行并规划关联新运行，不编辑事件历史。

assets/demo-plan.json 是合成计划示例。演示 init 加 --demo；示例 writes 仅是模拟互斥范围，不会创建对应源码目录，合成证据不能充当产品验收。演示运行会在索引中标识为演示，不能当成真实项目进度或验收结果。

## 执行只调用短命令

```powershell
python -X utf8 $pipeline task $runDir engine running --note "已收到任务与代码地图"
python -X utf8 $pipeline task $runDir engine passed --candidate CANDIDATE_ID --evidence RESULT_FILE --note "状态断言通过"
python -X utf8 $pipeline gate $runDir integration-test running
python -X utf8 $pipeline gate $runDir integration-test failed --note "真实失败摘要"
python -X utf8 $pipeline decide $runDir consult --note "需要顾问分析契约冲突"
python -X utf8 $pipeline decide $runDir return --round r2 --note "按已确认方案修复"
python -X utf8 $pipeline note $runDir --target engine --text "特殊情况与下一步"
```

示例 ID 来自示例计划，需在所属轮次开放后调用。脚本不执行产品任务或测试。passed 必须给实际候选和现存证据文件，failed 必须给原因；长输出留证据，必需项不得 skipped。

主调度者接收角色回报后统一上报；委派节点直接上报时明确 run-dir、节点 ID、允许状态和候选，不让多个 writer 竞争同一节点。锁串行化事件追加与投影更新，不替代工作区/进程资源协调。

失败后停止启动新工作、跳过待执行节点或推进检查点；此前已 running 的节点仍可提交 passed/failed，候选、证据和原因要求不变。needs_decision、consulting、blocked 都接收这些在途终态，保持原有失败决策状态，不因另一个成功而恢复放行，也不因新增失败退出顾问/阻塞状态。

主调度者先接收已完成的在途结果，再选择 consult、return 或 block；已经处于顾问/阻塞状态时继续接收结果。return 新增 attempt，重置目标轮及下游，旧终态及证据留在历史；未完成而实际取消/交接的节点先用 note 说明事实和必要证据位置，协调停止后再用 --quiesced。该参数不终止进程、不替代已完成结果上报，也不回滚代码或数据。

## 完成即结束，保留结果

最后必需检查点通过后，页面收到 completed 就停止轮询和陈旧检查，显示“运行已结束 · 静态留存”。上报命令自动写出 report.html：样式、逻辑和最终状态全部内嵌，单独打开仍可查看节点与历史，不产生轮询、服务或端口。报告包含私有路径与证据指针，继续本地保存。

blocked/needs_decision 仍是待处理状态，不冒充完成；可继续决策和返回。异常中断时没有后台服务需要清理，运行状态仍保留真实未完成事实。停止观察页面不等于终止 Agent、测试进程或外部服务，那些资源仍按任务归属收束。完成后附加备注会更新磁盘报告，已停止的页面需重新打开才能看到。

旧运行或 Skill 组件升级后，用 view 更新预制组件并从事件重建页面；不追加事件，不重复任务：

```powershell
python -X utf8 $pipeline view $runDir
```

若上报提示事件已记录但运行投影失败，先处理磁盘/权限等问题，再调用 view；若提示索引输出失败，可运行 index 重建。两种情况均不能重报同一事件。损坏事件流仍报错，不修剪历史。

可选 HTTP 兼容入口是 serve RUN_DIR --port 0，前台显示地址，Ctrl+C 停止；它不属于默认静态流程，不自动运行或长期保留。若明确选择该入口，主调度者负责记录和结束自己启动的服务。

## 每步向人类汇报与记忆收束

结构变更、执行开始/结果、检查点、顾问、回流、阻塞及完成后，主对话及时转述简短事件摘要。首次及结构变化可贴 status --mermaid 图；同轮并行启动可合并汇报，不能隐藏失败或跳过。后台脚本不能自行给对话发消息。

current.md 只归并项目/运行身份、有效轮次/attempt、候选、关键结果、阻塞与下一步，引用 run-dir，不复制 JSONL。长期必要证据按 project-memory 固化；Cleaner 在引用、占用、恢复和授权满足后处理准确路径，不因页面完成删除事件、报告或在用锁。
