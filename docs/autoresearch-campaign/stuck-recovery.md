# 受控卡死恢复运行记录

## 场景目标

验证 `TASK-F1AB02` 在受控 `worker.stuck` 注入后仍能由内核恢复并继续既有
`review -> test -> judge -> discriminator` 流程；worker 不直接移动任务状态或自宣终态。

## 本次运行

- workflow run：`legacy`
- dev dispatch：`disp-bd8c7c4051e6`
- dev 派发事件：`evt-8449ac3c68d2`
- runtime snapshot：`.zf/snapshots/TASK-F1AB02/disp-bd8c7c4051e6/runtime-snapshot.json`

## 注入与恢复观察

本次已实际发生受控注入。事件账本显示：

1. `autoresearch.inject.worker_stuck`：`evt-68ee3d4e435e`；
2. `worker.stuck`：`evt-2c088ffd9479`，由上一事件直接触发；
3. `worker.stuck.recovered`：`evt-3e7fc398cc77`，恢复动作为
   `completion_nudge_requested`，并成功注入 completion nudge；
4. 恢复后 dev-1 已继续产生 heartbeat（例如 `evt-5ce14b79e6e0`）；
5. `orchestrator.idle`：`evt-4caa49abe919` 明确记录该 worker 已恢复，因 heartbeat
   正常而无需重复 respawn/requeue。

查询时 `worker.stuck.recovery_failed` 为 0，`task.requeued` 也为 0；因此本记录只证明
本次实际采用的原 dispatch 内唤醒恢复路径，不声称发生了 requeue 或重新派发。该路径
是否满足条件式恢复验收，须由后续 test/judge 根据任务合同独立判定。

## 验收与证据

- dev 精确验收命令：`test -f docs/autoresearch-campaign/stuck-recovery.md`
- 事件核对命令：`zf events --type <事件类型> --last 10 --json`
- 因果核对命令：`zf trace show TASK-F1AB02 --format json`

本文档落盘时，arch 与 critic 已有事件证据；review、test、judge、discriminator 尚待
内核沿既有流程调度，本文不预写其通过结论。
