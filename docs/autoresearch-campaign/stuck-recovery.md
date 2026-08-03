# 受控 stuck 恢复 smoke 运行说明

本次 smoke 用于验证 worker 被受控标记为 stuck 后，ZaoFu 能由 harness 自动恢复任务，而不依赖人工移动状态。预期恢复链为 `worker.stuck → task.requeued → worker.stuck.recovered → re-dispatch`；恢复后的交付仍须依次通过 review、test、judge 和 discriminator，并由 kernel 推进到 done。

内层验收仅在项目根运行：

```bash
test -f docs/autoresearch-campaign/stuck-recovery.md
```

该命令成功只证明文档已交付，不证明外层 stuck 恢复场景通过。真实运行结果必须以对应 run 的 `events-summary.json` 和 `report.md` 为准：其中应能确认已请求并发生 stuck、至少一次 `worker.stuck.recovered`、没有 `worker.stuck.recovery_failed`，且恢复后任务通过正常门禁到达 done。若缺少这些事件或报告证据，不得宣称本 smoke 已通过。
