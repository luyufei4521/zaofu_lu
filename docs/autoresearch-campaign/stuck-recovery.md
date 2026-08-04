# 受控 Stuck 恢复验证

本次验证由外层 operator 对一个已派发 worker 注入或配置一次 `worker.stuck`，观察内核通过 `task.requeued` 或 `worker.stuck.recovered` 自动恢复并重新投递；全程不手工修改任务状态。

恢复后任务仍须依次通过正常的 review、test、judge 与 discriminator 门禁并到达 `done`。若恢复失败、出现 fatal event 或缺少终态证据，则本次验证失败。本文仅描述预期流程，不构成真实运行证据；实际结果应以 append-only events、`events-summary.json` 与 `report.md` 为准。
