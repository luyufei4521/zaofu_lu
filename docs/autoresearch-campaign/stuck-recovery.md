# 受控 stuck 恢复运行记录

本场景验证：外层 operator 对当前任务的真实 dispatch 发起一次受控 `worker.stuck` 注入后，内核能够恢复或重新排队任务，并继续正常的 review、test、judge 与 discriminator 流程；worker 不手工修改 canonical 状态。

任务级验收命令：

```sh
test -f docs/autoresearch-campaign/stuck-recovery.md
```

本记录只说明场景目标和验收入口，不声明注入、恢复或 campaign 已经成功。实际恢复结论由外层 operator 根据运行结束后的事件摘要和报告判定。
