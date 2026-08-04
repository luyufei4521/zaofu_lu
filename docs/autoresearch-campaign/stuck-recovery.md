# 受控卡死恢复验证

本轮运行用于验证 `worker.stuck` 受控注入后的自动恢复。若外层 operator 注入卡死，应由 Kernel 自动重排或恢复同一任务，并继续执行 review、test、judge、discriminator 门禁；不得手工搬运任务状态。

运行后核对 `worker.stuck` 之后出现 `worker.stuck.recovered`，且没有 `worker.stuck.recovery_failed`。交付物可在仓库根目录运行 `test -f docs/autoresearch-campaign/stuck-recovery.md` 检查。
