# 受控 stuck-recovery 运行说明

本轮用于验证：外层发起受控 `worker.stuck` 后，由 Kernel 自动恢复 worker 或重新排队任务，任务随后仍须经过正常的 review、test、judge 与 discriminator 流程。

本说明不代表恢复已经验证成功。恢复结果须由同一 task、instance、dispatch 的 canonical 事件链及外层评估报告签收，禁止人工移动任务状态。

文件验收命令：`test -f docs/autoresearch-campaign/stuck-recovery.md`
