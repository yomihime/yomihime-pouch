# 示例：保留 UI 的桌面音频包装

**日期：2026-10-03。以下是说明能力分配的情境，不是已完成项目、已确认 bug 或永久模型配置，也不可直接复制成工程规则。** 只有目标账户实际提供这些型号、配置允许且预算认可时才采用；否则映射到能力相当的可用候选。

情境：已有 voice-changer 2.1.4-alpha 解包客户端，第一阶段用 Electron 或 Tauri 包装并保留原 UI，调查 client mode 的输入设备问题；Python UI 留到后续明确授权阶段。不要借包装任务顺便重写界面。

## 某工程生成的 economy 分配示意

| 责任 | 示例选择 | 升级原因 |
| --- | --- | --- |
| 主协调者 | GPT-6.1 Sol / medium | 维护边界、依赖和验收 |
| analyst 资源盘点 | GPT-6 Luna / medium | 只读清点文件、入口、调用链 |
| analyst 因果诊断 | GPT-6.1 Sol / high | 设备选择、异步竞态、跨进程状态 |
| designer | GPT-6.1 Sol / medium 或 high | 取决于包装边界与生命周期歧义 |
| implementer 机械修改 | GPT-6 Luna / medium | 明确规格、低耦合、可立即验证 |
| implementer Electron | GPT-6.1 Sol / medium | 现有前端与桌面权限集成 |
| implementer Tauri / Node sidecar / 音频生命周期 | GPT-6.1 Sol / high | 跨进程启动、退出、异常和资源释放 |
| verifier 清单执行 | GPT-6 Luna / medium | 测试设计先由具备相应能力者完成 |
| 独立 reviewer | GPT-6.1 Sol / medium 或 high | 审查同一稳定修订，匹配风险 |

GPT-6 Astra 只是复杂瓶颈的候选；此 economy 示例在昂贵升级前先批准。型号强弱与 effort 分开考虑；不用模型名推算账户费用。此示例生成了最多两个子任务并行、standard speed 的限制，仍以实际配置和上层约束为准。

## 先证伪假设，再修复

`deviceId` 约束丢失、semaphore 未释放、mute 与采集状态耦合只是**待证假设**。先定位源码、复现并记录实际轨道/状态，再决定修复清单；不为了“看起来合理”一次全部修改。

最小验证矩阵（按适用系统实际执行）：

- OS 默认输入 A，客户端选择 B：记录请求的 deviceId、实际 track settings/设备 ID 及实际采集结果，确认不是只改了下拉框文案
- 权限失败后重试：无永久锁死、重复采集或错误状态残留
- 设备拔插、切换与进程重启：选项、恢复行为、轨道关闭与资源释放符合已确认契约
- mute/unmute：按产品定义验证采集、发送和 UI 状态，不预设它必须停止麦克风
- 实际打包 Electron/Tauri 运行时：验证窗口权限、启动/退出、sidecar 生命周期；浏览器开发预览仅提供部分证据

没有真实 A/B 设备或目标 OS 时，可做源码与 mock 验证，但相关用例记 `unrun` 并交接具体操作，不能报告输入设备问题已彻底解决。修复切片和包装切片只有在接口及写入范围独立时并行；Python UI 不因本轮完成自动开工。
