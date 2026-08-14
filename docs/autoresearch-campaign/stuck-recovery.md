# Controlled stuck-recovery 运行说明

本场景验证：外层 operator 对真实任务发起一次受控 stuck 注入后，Kernel 能够恢复或重新排队任务，并继续通过正常的 review、test、judge 与 discriminator 门禁；worker 不手工注入 `worker.stuck`，也不手工移动任务状态。

任务级验收命令：

```sh
test -f docs/autoresearch-campaign/stuck-recovery.md
```

该命令只证明文档存在，不代表恢复已经通过。最终由外层 operator/kernel 与 test/judge 核对可关联的 `autoresearch.inject.worker_stuck -> worker.stuck -> worker.stuck.recovered` 事故链，并确认 `stuck_incident_audit.status=passed`、`stuck_injection_satisfied=true`、`worker_stuck_recovery_failed_count=0`、`tasks_done>=1`、`fatal_count=0`。
