# 卡死恢复运行记录

## 验证目标

本次运行验证 ZaoFu 在受控 `worker.stuck` 后能够由 Kernel 自动重排或恢复，并继续通过 static、review、test、judge、discriminator 门禁直至机械收口。文件存在仅证明文档交付，不单独证明恢复或最终门禁成功。

## 唯一交付物

本任务唯一交付物为 `docs/autoresearch-campaign/stuck-recovery.md`，不修改恢复内核、控制面配置或 canonical runtime state。

## 恢复证据口径

恢复结论只以 append-only 事件账本和 Autoresearch 运行汇总为准。若观测到 `origin=external` 的受控注入，审计必须确认身份与因果一致且唯一的 `task.dispatched` → `autoresearch.inject.worker_stuck` → `worker.stuck` → `worker.stuck.recovered` 链，不得出现 `worker.stuck.recovery_failed`；后续门禁及 done 状态均由 Kernel 闭合，禁止手工移动状态。本文不虚构 event id，也不提前声明尚无账本证据的恢复或终局成功。

## 验收命令

```sh
test -f docs/autoresearch-campaign/stuck-recovery.md
test -s docs/autoresearch-campaign/stuck-recovery.md
```

两条命令返回 0 仅表示目标文件存在且非空。
