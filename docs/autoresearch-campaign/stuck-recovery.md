# controlled-stuck-recovery 运行记录

本场景验证：外部触发或配置一次 `worker.stuck` 后，由 Kernel 自动重新排队或恢复任务，并继续正常的 review、test、judge、discriminator 流程；全程不得人工搬运任务状态。

## 真实证据边界

本文件只证明 dev 已交付运行记录，不证明 stuck 注入、自动恢复或后续门禁已经通过。实际验证须由 test、judge、discriminator 从追加式事件账本和外层运行报告中核对同一 task、instance、dispatch 的注入、stuck、recovered 因果链；在这些证据产生前，不记录事件 id，也不作恢复成功结论。

## 原始验收命令

```sh
test -f docs/autoresearch-campaign/stuck-recovery.md
```
