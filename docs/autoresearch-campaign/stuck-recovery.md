# Controlled stuck-recovery 验证记录

## 场景目标

验证 outer operator 对真实任务发起受控 stuck 注入后，ZaoFu 能将任务重新排队或恢复，并继续经过 review、test、judge 和 discriminator，最终到达 done；全程不由 worker 手工移动 canonical 状态。

## 已观察证据与待验证项

- 已观察：critic v2 已批准本场景的验证交接，事件为 `evt-48cd5be88d54`，评审工件为 `.zf/artifacts/TASK-6F3E47/critic/v2/design-critique.json`。
- 待验证：本记录不声称已经产生 `worker.stuck`、`worker.stuck.recovered` 或恢复失败指标。仅在 outer operator 请求确定性 stuck 注入时，由 outer evaluator 在运行结束后核对 requested、stuck、recovered、recovery_failed、`stuck_injection_satisfied` 和 `tasks_done`。

## 当前结果

仓库交付物已准备，任务级存在性检查为 `test -f docs/autoresearch-campaign/stuck-recovery.md`。该检查通过只表示文件存在，不代表 stuck-recovery 场景、正常 gate 链或最终 done 已通过；这些结果仍等待各自责任角色验证。

## 残余限制

- dev 不执行真实 stuck 注入，也不替 outer evaluator 判定恢复成功。
- 文档本身不能证明任务没有被人工搬移；该结论必须由运行结束后的事件因果链与 outer summary 支撑。
- review、test、judge、discriminator 及条件式 outer evaluator 仍需按顺序独立给出证据。
