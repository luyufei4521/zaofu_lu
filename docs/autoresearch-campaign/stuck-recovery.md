# controlled-stuck-recovery 运行记录

本场景验证受控 `worker.stuck` 后，任务能否在不人工移动 canonical 状态的前提下继续交付，并由 Kernel 独占管理 requeue、recover 与 re-dispatch。

本轮账本已记录注入事件 `evt-b7e9ccf6d240`、`worker.stuck` 事件 `evt-cb460f3801b1`，以及 Kernel 以 `completion_nudge_requested` 执行的 `worker.stuck.recovered` 事件 `evt-e413fd13be19`；未观察到 `worker.stuck.recovery_failed`。截至本记录生成时，尚无 `task.requeued` 及恢复后的新 `task.dispatched` 证据，因此不得宣称完整恢复链已通过；requeue/recover/re-dispatch 因果覆盖仍待 test/judge 根据外层事件账本验证。

外层 operator 只负责发起受控注入；worker 不直接修改任务状态。重排队、恢复、重新派发、后续 review/test/judge/discriminator 流程及最终状态更新均由 Kernel 的事件与门禁路径执行。

最终文件验收命令：

```sh
test -f docs/autoresearch-campaign/stuck-recovery.md
```
