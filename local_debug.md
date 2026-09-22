# ZaoFu 本地独立修复记录

本文记录本地工作区在与远端 `dev` 对齐前存在的 6 组独立修复，说明问题、涉及文件、修改思路、行为影响、集成状态和验证情况。

## 基线与状态

- 远端基线：`origin/dev@2fb83e6`
- 当前集成分支：`wip/codex-20260901-sync-dev-local-fixes`
- 当前集成提交：`9a44666`
- 原始修复保全分支：`wip/codex-20260901-preserve-local-fixes`
- 集成结论：第 1～5 组已进入当前集成分支；第 6 组仅保存在修复保全分支，未进入当前集成分支。

## 修复总览

| 编号 | 修复主题 | 当前状态 | 主要影响 |
| --- | --- | --- | --- |
| 1 | Hook 与 Web 启动事件扫描限界化 | 已集成 | 降低长历史事件日志带来的内存和 CPU 峰值 |
| 2 | 启动时优先消费持久化事件增量 | 已集成 | 避免待处理工作流事件被历史恢复扫描延迟 |
| 3 | 有界兼容旧版 PRD lane 身份 | 已集成 | 兼容旧任务数据，同时拒绝未知或跨 Flow 身份 |
| 4 | 终态 Task 绑定新工作流请求时安全轮换 | 已集成 | 允许同一 Task 开启新一代请求，避免沿用旧计划产物 |
| 5 | Reader retry 生成新的 attempt source manifest | 已集成 | 修复 retry worker 因缺失输入 sidecar 而失败的问题 |
| 6 | Web 项目预热可关闭 | 仅保全 | 可降低大历史项目启动内存，但控制方式不符合当前配置约束 |

## 1. Hook 与 Web 启动事件扫描限界化

### 问题

Provider Hook 是短生命周期进程，但原实现会通过 `EventLog.read_all()` 读取全部事件历史，用于查找 causation、活动 Task、孤儿事件和停止条件。随着归档事件增长，每次 PreToolUse、PostToolUse 或 Stop Hook 都可能重复解码完整历史。

Web 启动恢复也会一次性加载全部事件，再从中寻找未完成的 Kanban Agent turn。长生命周期项目可能因此出现明显的启动延迟、CPU 峰值和内存占用，极端情况下会触发 OOM 或页面进程退出。

### 涉及文件

- `src/zf/cli/hook_recv.py`
- `src/zf/cli/hook_event_tail.py`
- `src/zf/web/headless_recovery.py`
- `tests/test_hook_recv_codex.py`
- `tests/test_web_headless_recovery.py`

### 修改思路

1. 新增 Hook 专用的活动事件尾部读取函数，只读取当前 `events.jsonl` 的有界尾部。
2. 默认最多读取 8 MiB，并保证最小读取窗口为 64 KiB；从文件中部开始时丢弃第一条不完整 JSONL 记录。
3. causation、活动 Task 查询和孤儿事件去重共用这一有界读取路径，不再为单次 Hook 回放所有不可变归档段。
4. 只有 provider/Claude/Codex 的 Stop 类事件才计算 completed-tail quiescence，普通工具 Hook 不再执行无关扫描。
5. Web 恢复改用 `iter_event_records()` 逐条遍历事件段，只保留终态 turn id 和尚未终结的 started turn，不保留全部事件对象。
6. 为避免新增逻辑继续扩大已有超大文件，将有界事件查询拆到 `hook_event_tail.py`。

### 行为与影响

- 正向影响：Hook 和 Web 启动的内存使用从“随全部历史增长”改为“Hook 有界、Web 流式”。
- 正向影响：高频 Hook 不再反复解码归档段，降低 CPU 和 I/O 压力。
- 行为边界：如果活动 dispatch 已不在有界尾部，Hook 会保留事件但不填写 causation，而不是回退到无界历史读取。
- 安全性：缺失 causation 只影响链路关联，不会丢弃 Hook 事件，也不会让 Hook 直接修改 canonical state。

### 提交与验证

- 主要提交：`e49347b fix: bound hook and web startup event scans`
- 结构收口：`7ba7c33 refactor: extract bounded hook event queries`
- 补充覆盖：`9a44666 test: cover legacy role and headless recovery boundaries`
- 已验证有界尾部保留最新完整事件、Web 只恢复未终结 turn、原有 Web 启动恢复行为保持有效。

## 2. 启动时优先消费持久化事件增量

### 问题

ZaoFu 重启后需要消费 watcher 停止期间写入 `events.jsonl` 的事件。原启动 catch-up 直接执行 idle tick，idle 路径会先触发历史恢复和 projection 扫描。在大事件账本中，新写入的 `workflow.invoke` 或已接受请求可能长时间得不到处理。

### 涉及文件

- `src/zf/cli/start.py`
- `tests/test_cli_start.py`

### 修改思路

1. 启动 catch-up 先读取 Orchestrator 的 durable offset。
2. 通过 `EventLog.read_from_offset()` 获取 offset 之后的增量事件及新 offset。
3. 存在增量时，直接调用 `orchestrator.run_once(events=pending, consumed_offset=new_offset)`。
4. 没有增量时仍执行原 idle tick，保留周期性维护语义。
5. 对不具备 `_load_offset` 或 `read_from_offset` 的轻量 fake/旧 adapter 保留原路径。
6. 异常仍通过现有启动失败事件记录，不绕开事件账本。

### 行为与影响

- 启动后的真实待处理事件优先于历史范围维护任务。
- watcher 停机期间的事件可以在启动阶段立即被消费，无需等待后续 tick。
- 空增量启动仍会执行原有恢复、投影和周期维护逻辑。
- 不改变 offset 的 canonical 所有权，也不引入第二套启动状态机。

### 提交与验证

- 提交：`e78d1de fix: prioritize durable startup event deltas`
- 已覆盖“存在 durable delta 时直接消费”和“无 delta 时保持 idle tick”两条路径。

## 3. 有界兼容旧版 PRD lane 身份

### 问题

旧版生成的 PRD Task/合同可能使用 `prd-dev-lane-0` 一类身份，当前配置中的角色名称和 instance id 则是 `dev-lane-0`。严格按字符串匹配会将历史 Task 判定为未知 owner，阻断合同校验或 writer owner 解析。

直接放宽为任意前缀或模糊匹配又会错误接纳不存在的 lane，甚至跨 Flow 绑定 writer。

### 涉及文件

- `src/zf/core/task/contract_validation.py`
- `src/zf/runtime/flow_roles.py`
- `tests/test_flow_roles.py`

### 修改思路

1. 始终先尝试精确身份匹配。
2. 仅对以 `prd-` 开头的历史身份增加一个候选值：去掉一次 `prd-` 前缀。
3. 去前缀后的候选必须真实存在于当前 `zf.yaml` 角色或 instance 集合中。
4. owner role、owner instance、rework target 和角色反向解析使用相同的有界兼容规则。
5. 保留 `flow_owner_cross_flow`、`flow_owner_instance_unknown` 和 role/instance mismatch 的原有拒绝语义。

### 行为与影响

- `prd-dev-lane-0` 可映射到已配置的 `dev-lane-0`。
- `prd-dev-lane-9` 在 lane 9 未配置时仍被拒绝。
- 不接受任意包含关系、相似名称或多次去前缀。
- 影响范围局限于历史 PRD identity 兼容，不改变当前配置的 canonical role identity。

### 提交与验证

- 主要提交：`80cb268 fix: accept bounded legacy PRD lane identities`
- 补充负向测试：`9a44666 test: cover legacy role and headless recovery boundaries`
- 已验证合法旧别名能够映射、未知 writer 继续失败、跨 Flow 检查保持有效。

## 4. 终态 Task 绑定新工作流请求时安全轮换

### 问题

Task 进入 `done`、`cancelled` 等终态后会由 `TaskStore` 归档。随后同一业务 Task 收到一个经过证明的新 Workflow Request 时，旧逻辑仍禁止终态 Task 参与 request rotation，导致新请求无法绑定。

即使重新开放 Task，如果继续复用旧一代计划生成的 source index、product contract、task map 或 plan package evidence，新请求也可能错误消费过期产物。Task 多次终结后，读取第一条归档记录还可能拿到旧 authority revision，造成 CAS 判断错误。

### 涉及文件

- `src/zf/core/task/store.py`
- `src/zf/runtime/workflow_request_acceptance.py`
- `src/zf/runtime/workflow_start.py`
- `src/zf/runtime/workflow_start_inputs.py`
- `src/zf/runtime/workflow_task_request_rotation.py`
- `tests/test_task_store.py`
- `tests/test_workflow_request_acceptance.py`
- `tests/test_workflow_task_request_rotation.py`

### 修改思路

1. 只有通过既有 request rotation 证明、origin binding digest 校验和新 request admission 检查的终态 Task 才能重开。
2. 扩展 `TaskStore.compare_and_update_contract()`：在显式 `reopen_terminal=True` 时，从终态归档恢复最新记录并执行原子 CAS。
3. 重开时先把非终态记录写回 active store，再删除 terminal index，保持崩溃安全顺序。
4. Task 状态重置为 `backlog`，清空 `blocked_reason`、`assigned_to`、`active_dispatch_id` 和 `completed_at`。
5. 归档查询改为从最新记录向前查找，确保多代归档返回当前 canonical snapshot。
6. 将新一代请求标记为 `fresh_request`，清除上一代 `source_index_ref`、`product_contract_ref` 以及 task-map/plan-package 等 evidence 引用。
7. 保留 Task 自身仍有效的 source/spec、acceptance、scope、约束等合同输入，并重新计算输入合同和 binding digest。

### 行为与影响

- 已取消或已完成 Task 可以在受控条件下接收新一代 Workflow Request。
- 普通调用不能任意复活终态 Task；重开仍受 authority revision 和 origin binding CAS 保护。
- 新请求不会继承上一轮计划阶段生成的过期 artifact refs。
- 同一 Task 多次归档后，读取和 CAS 使用最新一代记录。
- `completed_at` 被清空，避免非终态 Task 同时携带终态时间戳。

### 提交与验证

- 主要提交：`b9ab19a fix: rotate terminal tasks onto fresh workflow requests`
- 补充修复：`212d587 fix: clear completion time when rotating terminal tasks`
- 已验证终态 Task 的归档、受控重开、新 request binding、fresh input 过滤、最新归档读取和错误 revision 拒绝。

## 5. Reader retry 生成新的 attempt source manifest

### 问题

Reader 首次 dispatch 会生成与 attempt 绑定的不可变 source manifest。Reader 因 provider turn 关闭、worker 重启或 dispatch loss 进入 retry 后，run id/attempt id 已更新，但旧 retry 路径没有为新 attempt 生成对应 sidecar。

Retry briefing 要求 worker 按新 attempt 读取输入，因此 `zf artifact read` 会因为 source manifest 不存在而 fail closed，造成恢复路径再次失败。

### 涉及文件

- `src/zf/runtime/orchestrator_fanout.py`
- `src/zf/runtime/fanout_retry_support.py`
- `tests/test_reader_fanout_runtime.py`

### 修改思路

1. Reader retry 在发送 transport task 之前，为新的 retry run id 生成 source manifest。
2. manifest 绑定 `task_id`、`workflow_run_id`、`target_ref`、新 attempt/dispatch id 和上一 dispatch event id。
3. metadata 记录 `retry_of_run_id` 和 `retry_attempt`，保留重试因果链。
4. 将 descriptor ref、digest、required reads 和 input consumption policy 写入新的 `fanout.child.dispatched` payload。
5. sidecar 生成失败时不继续发送一个缺少输入契约的 worker，而是写入 `fanout.child.failed`，并标记 `failure_kind=artifact_read`。
6. 将 sidecar 准备和 retry 失败事件构造拆到 `fanout_retry_support.py`，使 `orchestrator_fanout.py` 不超过仓库冻结的超大文件行数上限。

### 行为与影响

- retry reader 与首次 dispatch 一样拥有完整、不可变、可校验的输入 manifest。
- worker 可以按新 attempt id 执行 `zf artifact read`，不会错误复用旧 attempt sidecar。
- manifest 写入失败时 fail closed，并留下可追踪的事件证据。
- 每次 reader retry 增加一次小型 sidecar 写入，但换取了确定性输入和恢复正确性。

### 提交与验证

- 主要提交：`ad371d2 fix: materialize reader retry source manifests`
- 结构收口：`9036609 refactor: isolate fanout retry support`
- 已验证 provider turn closed 后会生成 retry dispatch，并且 descriptor 指向实际存在的新 manifest 文件。

## 6. Web 项目预热可关闭

### 问题

Web `create_app()` 会启动后台线程预热最近项目。对于拥有大规模历史事件归档的项目，预热可能在首个页面请求前消耗较高内存，并与 Web 启动恢复同时竞争资源。

### 涉及文件

- `src/zf/web/server.py`

### 原始修改思路

1. 增加环境变量 `ZF_WEB_PREWARM`。
2. 默认值为开启，保持原行为。
3. 值为 `0`、`false`、`off` 或 `no` 时不启动 `zf-web-prewarm` 后台线程。
4. 禁用预热后，项目 snapshot 仍可按请求按需生成。

### 影响与未集成原因

- 正向影响：内存受限或大历史项目可以跳过非必要预热，降低启动峰值。
- 负向影响：首次访问未预热项目时延迟可能增加。
- 配置风险：仓库规定 `zf.yaml` 是唯一控制面配置；新增 `ZF_WEB_PREWARM` 会形成未纳入 schema、validate 和配置快照的第二控制入口。
- 当前决定：不进入集成分支。若后续确有需求，应设计为 `zf.yaml` 中的正式 Web/runtime 配置项，并补充 schema、文档和测试。

### 保存位置与验证状态

- 保全提交：`ebf7a81 fix: allow disabling web project prewarm`
- 所在分支：`wip/codex-20260901-preserve-local-fixes`
- 当前集成分支不包含该修改，因此最终集成验证不覆盖此开关。

## 集成验证摘要

当前集成分支对第 1～5 组修复执行了以下验证：

- `scripts/dev-premerge-gate.sh`：50 项通过，1 项跳过。
- 串行并发安全测试：10 项通过。
- 工作流 mock smoke：10 项通过。
- Web TypeScript 类型检查：通过。
- Web 单元测试：通过。
- Hook、Web recovery、Flow role、Task rotation、reader retry、结构约束和 stop-guard 聚焦测试：通过。
- 广泛确定性测试中的本地结构回归已经消除；剩余失败经对照归为远端基线或环境传感器问题，不是上述第 1～5 组修复新增。

## 后续维护注意事项

1. 不要重新把 Hook causation 或 Web 启动恢复改回 `EventLog.read_all()`；需要完整历史语义时优先使用流式 segment iterator。
2. PRD 身份兼容必须保持有界，只允许一次 `prd-` 历史前缀映射且目标必须存在。
3. 终态 Task 重开只能走受控 request rotation 和 CAS 路径，不能直接编辑 `kanban.json` 或 terminal archive。
4. Reader retry 修改 run id 时，必须同步生成并绑定该 attempt 的 source manifest。
5. Web 预热开关如需重新引入，应进入 `zf.yaml` schema，而不是继续使用独立环境变量。
