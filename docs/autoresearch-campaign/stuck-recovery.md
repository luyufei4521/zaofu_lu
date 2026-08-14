# 受控 Worker Stuck 恢复运行记录

## 目标

本场景用于验证 worker 在受控 stuck 后仍由 Kernel 接管恢复，外层 operator 只负责发起受控注入，不直接修改任务、实例或派发状态。

## 预期路径

Kernel 校验注入与当前 `task.dispatched` 的 task、instance、dispatch 和 correlation 一致后，记录 `worker.stuck`。随后 Kernel 根据已有进度选择完成提醒，或将任务 requeue、恢复或重建 worker，并依据 canonical 状态重新派发；成功与失败分别以 `worker.stuck.recovered` 和 `worker.stuck.recovery_failed` 留痕。

## 验收口径

- 文档存在、非空、包含中文且 Markdown diff 无空白错误。
- 若实际执行受控注入，test/judge 必须核对同一 incident 的 `task.dispatched` → `autoresearch.inject.worker_stuck` → `worker.stuck` → `worker.stuck.recovered` 因果链，且不存在对应的 `worker.stuck.recovery_failed`。
- 任务仍须经过正常 review、test、judge 和 discriminator gate；本文仅记录目标与预期，不能单独证明恢复已经发生或已经通过，也不得以手工移动状态代替 Kernel 流程。
