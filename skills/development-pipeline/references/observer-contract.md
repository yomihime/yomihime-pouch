# 轮次流水线与本地观察器契约 v1

默认轮次严格按计划顺序执行。每轮含 1-n 个互相可并行任务及零个或多个有序检查点；本轮全部任务完成（或非必需项显式跳过）、检查点通过后才能进入下一轮。至少最后一轮具有必需测试或审查检查点。轮数来自实际任务，不限制失败修复次数。

失败进入 needs_decision：主调度者说明依据，选择顾问介入、返回当前/更早指定轮次或阻塞。工具记录与约束流程，不调用模型、运行产品命令、回滚源码、终止进程或替人决定是否通过。

## 文件与命令

运行材料位于各项目获准的 .agent-workspace/<work-id>/pipeline/，各运行 events.jsonl 是唯一机器事件源；项目固定入口 .agent-workspace/index.html、运行页面与 status 都是可重建投影，不是另一份人工项目记忆。init 固定项目 id/name/root 与随机 run_id，不共享全局注册表或浏览器存储；不同项目、运行不共用目录。记录中不放秘密和完整日志。

入口 scripts/pipeline.py，Python 标准库；预制组件 assets/observer/index.html、app.js、styles.css。默认复制到运行目录的 observer/，打开 index.html 即可；每次事件追加后在同一锁内原子更新 state.js。网页加载同目录经典脚本取得投影，不使用 file:// fetch，不启动服务/端口，不要求放宽浏览器设置。页面固定校验项目和 run_id，拒绝身份不匹配或版本倒退的数据。

项目索引仅发现 `.agent-workspace/<work-id>/pipeline/events.jsonl`，跳过保留目录、符号链接和嵌套项目；不会把记忆证据、初始化暂存或备份中的日志副本当运行。重放发现的日志时，损坏或不可读显示读取失败，不使用缓存状态。显式指定其他 run-dir 仍可直接操作，但不自动进入索引；不存在旧目录回退或自动迁移。completed 显示为已归档，其他运行按最后事件时间满 7 天显示为过期，否则显示为活动。分类是事件时间视图，不探测实际进程；归档和过期不表示移动或删除文件。索引提供现存观察页和已完成报告的链接，标明演示运行。init、事件更新及 view 重建所属统一工作区的索引数据，也可用 index 命令手动重建；索引页每 5 秒读取数据并按当前时间重新分类。

completed 后停止轮询与陈旧检查，自动生成单文件 report.html，内嵌样式、脚本和最终状态，无外部数据依赖。旧事件缺项目身份时保留未知，不推断；view 可刷新组件并重建投影，不改事件。若事件已追加而运行投影更新失败，明确报告已记录，修复后用 view 恢复；若索引输出失败，修复后用 index 恢复。均不重报事件。

可选兼容 HTTP 服务只绑定 127.0.0.1，GET /api/state，禁止 HTTP 写入、命令执行和任意文件读取；该服务前台运行，由启动者结束，不属于默认静态路径。

```text
pipeline.py init RUN_DIR --title TITLE [--demo] [--project-root PATH]
pipeline.py plan RUN_DIR --file PLAN_JSON
pipeline.py start RUN_DIR
pipeline.py task RUN_DIR TASK_ID running|passed|failed|skipped [--note TEXT] [--evidence PATH] [--candidate ID]
pipeline.py gate RUN_DIR GATE_ID running|passed|failed|skipped [--note TEXT] [--evidence PATH] [--candidate ID]
pipeline.py decide RUN_DIR consult|return|block [--round ROUND_ID] --note TEXT [--quiesced]
pipeline.py note RUN_DIR --target ID --text TEXT
pipeline.py status RUN_DIR [--json|--mermaid]
pipeline.py view RUN_DIR
pipeline.py index PROJECT_ROOT
pipeline.py serve RUN_DIR [--port PORT]
```

规划中可重复 plan，随每次定义事件逐步绘图；尚不完整的草案可以展示，start 才执行完整准入校验。执行中的结构不可静默改写。各 mutating 命令只输出简短标准事件摘要，主调度者在对话转发；结构变化时可附 Mermaid，不必每步重新描述整图。后台网页不能自行向聊天发送消息。

## 计划 JSON

```json
{"rounds":[{"id":"r1","title":"第一轮","tasks":[{"id":"t1","title":"契约","role":"architect","required":true,"writes":[],"resources":[]}],"gates":[{"id":"g1","title":"契约审查","kind":"review","required":true,"return_to":"r1"}]}]}
```

ID 全局唯一且稳定，轮次顺序按数组。任务有串行依赖时分到不同轮次，不利用 wave 标签绕过屏障；同轮共享写入/资源不能同时运行。writes 声明同一工作区的相对逻辑范围，允许 . 表示整个工作区；拒绝绝对/驱动器/UNC、..、Windows 尾点/空格及非法组件，统一斜杠并忽略大小写比较重叠。它不是文件系统沙箱；符号链接、junction、hardlink、8.3 短名或跨工作区的实际别名由调度者使用相同 resources 标识互斥，不能依赖词法范围检测真实文件身份。检查点按数组顺序，只有任务已完成且前置检查点满足才可开始。return_to 必须为当前或更早轮次。

passed 需非空候选与存在的证据文件，保存路径及校验但不提供文件浏览器，不把摘要当完整日志。failed 必须有非空原因；必需项不能 skipped；非必需跳过需理由，可从 pending 显式跳过。passed/failed 先 running 再结果，不可直接把未来轮次或待执行检查点标通过。失败与旧通过保留事件身份，不追溯改为成功。

needs_decision、consulting、blocked 只允许此前已 running 的当前轮节点继续上报 passed/failed，记录当前 attempt 的完整候选/证据/原因；不允许新的 running、pending 跳过或检查点/轮次推进。接收在途结果保持已有决策状态与原失败；新成功不会恢复调度，新失败不会把 consulting/blocked 改回 needs_decision。结果到达顺序不能决定哪些真实结果被保留。主调度者应在返回前接收已完成结果，对实际取消/交接的未完成任务记录备注与依据。

return 保留历史，增加 attempt，将指定轮次及下游任务/检查点重置为待执行，早于目标的记录仍保留原身份；主调度者负责判断更早证据是否受影响。仍有 running 任务时，需实际协调停止并 --quiesced 确认交接后再重排；此参数不终止进程，不替代已完成结果的上报。重复/不合法状态更新拒绝，不破坏历史。

## 状态投影（静态脚本及可选 GET /api/state）

```text
version: 1
run_id, title, demo, status: draft|running|needs_decision|consulting|blocked|completed
project: {id,name,root}|null  (legacy logs keep null)
revision: event sequence, attempt: integer, current_round: ID|null
rounds: [{id,title,index,status:pending|ready|running|passed|failed,
 tasks:[{id,title,role,required,writes,resources,status:pending|running|passed|failed|skipped,
 note,evidence:[{path,sha256}],candidate,updated_at,attempt}],
 gates:[{id,title,kind,required,return_to,status,note,evidence,candidate,updated_at,attempt}]}]
events: [{seq,time,kind,entity_id,round_id,attempt,note,...}]  chronological
updated_at: last event timestamp
```

页面固定中文界面：项目/运行身份、规划/执行状态、当前轮次/尝试、轮次并行分支、检查点、失败返回边、顾问状态、节点备注与证据指针、可展开历史信息的时间线。历史失败可查，读取异常保留旧图与时间；读取超时 8 秒、异常阈值 10 秒，独立每秒检查，成功恢复。它们是 UI 读取参数，不是任务预算；数据文件未变化不等于 Agent 离线。completed 页面不再报陈旧。显示的是上报事件，不冒充进程探测或独立质量证明。

程序跨进程序列化事件与投影写入，写前校验并完整重放，损坏日志报错不静默修剪；CLI 与静态/HTTP 投影一致。投影 JSON 转为脚本或内嵌时转义 '<' 与行分隔符，用户文本用 textContent/SVG 文本显示。state.js 是受管的生成脚本，只加载本次运行的固定相邻路径，不接受任意脚本地址；它及页面仍是可信本地执行文件，不作为不受信任输入导入。HTTP 只提供固定资源与状态 JSON。
