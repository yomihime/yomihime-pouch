# 静态观察页与上报

默认使用本地 HTML + CSS + JavaScript，不需要 HTTP 服务、端口、前端构建或常驻 Python。每次上报命令追加事件后更新本次运行的 state.js；页面加载同目录的经典脚本来取得状态，不用 file:// fetch，不要求放宽浏览器安全设置。浏览器对本地文件 fetch 有限制，经典脚本的嵌入规则见 [MDN 同源策略](https://developer.mozilla.org/en-US/docs/Web/Security/Defenses/Same-origin_policy)。

## 按项目和运行隔离

每项工作使用新的 `.agent-workspace/<work-id>/pipeline/`，不复用已完成目录，不占用受管保留名或其 Windows 别名。项目固定入口为 `.agent-workspace/index.html`。不同项目和运行不共享目录；这是路径、数据和运行身份隔离，不是操作系统沙箱。保留名、身份与索引规则见[观察器契约](observer-contract.md#文件与命令)。

下图只列流水线 CLI 在相应操作中实际创建或更新的文件；不要求手工预建，也不表示 yomihime-init 会生成整棵树。

```text
.agent-workspace/
  index.html                     工具生成：项目固定入口（事件派生的运行索引）
  pipeline-index-data.js         工具生成：由事件重建的索引数据
  .pipeline-index.lock           工具生成：项目索引跨进程锁文件，释放后仍留存
  <work-id>/pipeline/
    events.jsonl                 工具生成：持久的唯一机器事件源
    .pipeline.lock               工具生成：运行读写锁文件，释放后仍留存
    observer/                    工具生成：可重建的静态页面与资源
      index.html                 本次运行的观察页面
      app.js                     预制显示逻辑
      styles.css                 预制样式
      state.js                   事件派生数据，原子替换
    report.html                  工具生成：完成后保留的单文件最终报告
```

这些实际运行材料和索引本地私有，按 multi-agent-engineering/project-memory 保护，不暂存、提交或上传。预制组件由工具复制，不要求 LLM 编写前端。各运行 events.jsonl 是事实来源，索引、页面和报告可重建，不是另一份人工项目记忆。

保留事件日志、最终报告及项目索引入口；可重建不等于获准删除。`.pipeline-index.lock` 与 `.pipeline.lock` 是工具维护的锁文件，不是每次命令结束即删除的临时文件；文件存在不代表仍被占用，在用时禁止删除，也不作为普通残留清理。原子更新期间工具还会创建随机名 `.tmp` 文件并在正常退出路径中清理，不为它们约定固定文件名；异常中断后发现的残留先核对占用与用途，再按授权处理。

## 一次初始化，直接打开文件

下列 init 子命令只创建一次流水线运行，不代替 yomihime-init 的项目盘点与安全整理。项目根自动识别和项目索引只采用统一工作区，不查找旧目录、建立别名或自动迁移；旧项目下次开工时先处理 yomihime-init 报告的材料与路径冲突。

```powershell
$pipeline = "skills/development-pipeline/scripts/pipeline.py"
$runDir = ".agent-workspace/当前任务/pipeline"
python -X utf8 $pipeline init $runDir --title "当前任务" --project-root .
```

打开项目 .agent-workspace/index.html，选择运行进入其观察页；已完成的运行链接到单文件报告。也可直接打开命令输出的 observer/index.html。省略 --project-root 时，从运行目录的 .agent-workspace 祖先识别项目根；不在该布局时采用运行目录的父目录。显式指定时要求运行目录位于该项目内。显式指定其他位置的运行仍可直接操作和查看，但不因此进入项目索引。项目身份固定在初始化事件中，旧日志未记身份时显示未记录，不猜成当前项目。

索引从统一工作区的运行事件重建，显示活动、过期、已归档或读取失败；分类不证明进程是否存活，也不移动或删除文件。发现范围、刷新周期与分类阈值以[契约](observer-contract.md#文件与命令)为准。需要手动重建时运行：

```powershell
python -X utf8 $pipeline index .
```

运行详情页自动读取 `state.js`，读取异常时保留旧图与最后成功时间；精确时限见[状态投影](observer-contract.md#状态投影静态脚本及可选-get-apistate)。没有新事件不等于执行者离线。浏览器若禁止本地脚本，可用下文可选 HTTP 模式，不更改浏览器安全设置。

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

失败后暂停新工作与推进，先接收此前已 running 节点的真实终态，再选择 consult、return 或 block；成功回报不解除已有失败决策状态。返回前记录取消或交接依据，实际协调停止后才用 `--quiesced`；该参数不终止进程或回滚数据，也不能替代已完成结果上报。允许的状态转换、attempt 重置和证据要求以[计划契约](observer-contract.md#计划-json)为准。

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
