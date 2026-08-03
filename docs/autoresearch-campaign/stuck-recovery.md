# Controlled stuck-recovery 运行说明

## 验证目的

本次验证用于确认 ZaoFu 能观察到受控的 worker stuck，并经正常的恢复、重新派发及
review/test/judge/discriminator 流程收敛任务；全程不得手工移动任务状态。

## 任务级验收

在仓库根目录执行：

```bash
test -f docs/autoresearch-campaign/stuck-recovery.md
test -s docs/autoresearch-campaign/stuck-recovery.md
```

两条命令返回 0 只证明交付文档存在且非空。

## 证据边界

文档内容不能替代真实 stuck 注入与恢复证据。场景是否通过，必须以外层生成的
`report.md`、`events-summary.json` 和 trace 为准：事件链应包含至少一次
`worker.stuck` 及一次 `worker.stuck.recovered`（或等价的成功恢复/重新入队证据），
且派生指标满足 `worker_stuck_count >= 1`、`worker_stuck_recovered_count >= 1`、
`worker_stuck_recovery_failed_count == 0`、`tasks_done >= 1`、`fatal_count == 0`。
若外层没有实际注入 stuck，或缺少上述报告、汇总与 trace，不能宣称 stuck-recovery
场景通过。
