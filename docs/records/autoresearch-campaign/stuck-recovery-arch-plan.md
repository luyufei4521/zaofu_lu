---
kind: arch-handoff-plan
task_id: TASK-AF11DF
status: proposed
version: 2
---

# 受控卡住恢复验证：arch 交接方案

## 目标与边界

本任务的语义源 `source.md` 没有提供行为正文；本方案以同一工作树中的
`autoresearch-seed.txt` 和现有 autoresearch 手册为可追溯补充来源。目标是让一次
`controlled-stuck-recovery` 运行在外层注入一个已审计的 `worker.stuck` 后，仍然完成
正常的 review → test → judge → discriminator 闭环，并由 dev 产出
`docs/autoresearch-campaign/stuck-recovery.md`。本 arch 任务只提交实现交接计划，不能创建该最终运行记录、修改 `zf.yaml` 或直接改变 `.zf` canonical state。

角色边界如下：

- arch：发布本计划及四个候选工件，说明文件所有权、证据和风险。
- critic：只评审本计划；不运行完整验证，也不替 dev 写运行记录。
- orchestrator：在设计门通过后合成/物化下游任务，保持 `contract` 为唯一任务合同。
- dev：只写最终运行记录，并在真实 dispatch 后允许外层注入一次 stuck。
- review/test/judge/discriminator：分别做语义审查、验证、判定和机械证据门；不能用手工状态移动代替事件链。

## 预期运行链

```text
arch.proposal.done
  -> design.critique.done
  -> dev.build.done (文件存在且记录完整)
  -> static_gate.passed
  -> review.approved
  -> test.passed
  -> judge.passed
  -> discriminator.passed / task done
```

外层 supervisor 只在目标 dev dispatch 已真实出现后注入
`autoresearch.inject.worker_stuck`。内层 kernel 应记录并驱动：

```text
autoresearch.inject.worker_stuck
  -> worker.stuck
  -> task.requeued
  -> worker.stuck.recovered
  -> task.dispatched (重新派发)
```

签收必须同时看到 `stuck_injection_requested_count >= 1`、`worker_stuck_count >= 1`、
`worker_stuck_recovered_count >= 1`、`worker_stuck_recovery_failed_count == 0`，且
`stuck_injection_satisfied == true`。这些指标来自 run report/events summary，不由 worker
自报成功。

## v2 重工结论

本版响应 `design.critique.done:evt-f5aecf4a7a76` 的五项修订：

- 当前被测 worktree 固定为
  `/tmp/zaofu-autoresearch-resident/worktrees/rmar-24e159d2370e`，当前 state dir 固定为其
  `.zf`；所有内层命令从该 worktree 根执行，不再使用尖括号占位符。
- 当前运行本身已由外层 real-provider runner 以 `--confirm` 启动，内层角色不能递归启动
  第二个 autoresearch run。内层 T-04 是 deterministic event checker；real-provider 的
  post-run report 验证由外层 operator 在 runner 退出后执行。
- stuck 签收不再只看计数：必须证明原 dispatch → external injection → kernel stuck，随后
  `task.requeued` 与 `worker.stuck.recovered` 均由该 stuck 导致，最后同 task/instance 获得
  不同的新 dispatch id；非空 correlation 必须保持一致。
- dev 的最终记录除了存在，还必须包含场景、完整恢复链、四项 stuck 指标、
  review/test/judge/discriminator verdict 和可回查 event/state/output refs；T-01 对内容逐项检查。
- “无手工状态移动”被收窄为可机械检查的判据：对本 run 的 `task.status_changed`，
  `actor` 必须为 `zf-cli` 且 `origin` 不能是 `worker`；同时
  `task.invalid_transition == 0`。检查结果由 T-04 和外层 `events-summary.json` 共同提供。

当前 outer run 的确定路径为
`/home/uisee/zaofu_projects/loshu_zaofu_dev2/.zf-loshu_zaofu_dev2/autoresearch/resident/rmar-24e159d2370e/runs/loop-001-controlled-stuck-recovery-20260818T091520`。
该目录中的 `report.md`/`events-summary.json` 只有在内层 runner 退出后才能生成，因此不能作为
内层 worker 自报完成的前置条件；外层 supervisor 用它们做最终 real-provider 签收。

## 实现交接

1. orchestrator 读取本目录的 `task-map.json`，将 dev 的唯一写入范围限定为
   `docs/autoresearch-campaign/stuck-recovery.md`；其他角色为只读证据消费者。
2. dev 在收到真实 task 后，按种子要求写一份简洁中文运行记录，至少包含场景/注入方式、
   事件恢复链、四项 stuck 指标、最终 review/test/judge 结果和残余风险。记录中的命令、
   event id、report 路径必须可回查；不得伪造 event 或直接写 `events.jsonl`。
3. review 只检查记录是否与当前 task contract、git diff 和已产生的 event refs 对齐；test 执行
   测试矩阵中的确定性测试和当前-run 因果检查；judge 汇总 acceptance matrix；discriminator
   只依据事件、文件和测试证据完成机械 gate。外层 operator 在 runner 退出后再读取 report。
4. 若注入窗口在 runner 退出前没有目标 dispatch，标记
   `stuck_injection_satisfied=false` 并走失败/重工路由；不得通过手动把 task 改成 done
   来绕过 gate。若恢复失败，保留 `worker.stuck.recovery_failed` 作为 fatal evidence。

## 运行与清理建议

当前 real-provider run 已由外层 resident supervisor 启动，进程参数含
`--scenario controlled-stuck-recovery`、`--expected-done 1`、`--timeout 7200` 和 `--confirm`；
内层角色不得再启动第二次 provider run。外层验证完成并归档 report 后，由 resident/operator
负责停止 harness、tmux 和清理 worktree。不要触碰本分支已有的 `zf.yaml`、
`autoresearch-seed.txt` 或 `web/node_modules` 脏改动。

## 指令卫生审计

- 已考虑：`AGENTS.md`、`CLAUDE.md`、本任务 briefing、kernel task/source/progress、
  `skills/zf-harness-instruction-hygiene/SKILL.md`、`docs/manual/autoresearch-orchestrator.md`、
  `docs/manual/10-autoresearch-usage.md` 和 `autoresearch-seed.txt`。
- 缺口：`source.md` 的语义正文为空；briefing 提供的四个设计工件是本次补齐的候选计划，
  不是 runtime truth。arch 允许的其他 load-on-demand 技能在本工作树未物化，不能假设其方法已生效。
- 采用规则：以 runtime/AGENTS 约束优先；所有状态变化走事件和 canonical store；本计划只作为
  `artifact.manifest.published` 的 proposed 输入，不新建配置控制面。

## 工件索引

- `skill-adapter-plan.json`：角色到方法/证据边界的适配，不改变技能启用配置。
- `acceptance-matrix.json`：从最终文件到事件指标和无手工状态移动的验收映射。
- `test-matrix.json`：按模块、恢复链和真实场景分层的验证清单。
- `task-map.json`：供 orchestrator 物化的下游任务候选图；不直接写入 Kanban。
