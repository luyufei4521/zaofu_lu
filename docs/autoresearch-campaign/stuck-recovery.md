# 卡住恢复验证运行说明

## 受控场景

外层 operator 可在 worker 已收到真实任务后，针对当前有效的 task、dispatch、attempt 和 worker 绑定发起一次受控 stuck 请求。Kernel 校验请求及其因果关系后，才可记录 `worker.stuck`。是否实际触发必须以本轮事件账本为准；没有真实注入事件时，只记录条件未触发，不声称已经演练恢复。

## 恢复边界

Kernel 负责 canonical state 和恢复副作用。有效的受控 stuck 可进入 `worker.stuck -> task.requeued -> worker.stuck.recovered -> re-dispatch` 路径，也可依据已记录进度或待提交产物请求原 worker 继续完成；需要时由受控恢复流程重启 worker。具体采用哪条路径及是否成功，只能由真实事件证据确认。

任何角色或人工操作都不得直接编辑 `events.jsonl`、Kanban 或 TaskStore 等 canonical state，也不得手工把任务移动到下一状态。恢复失败应由 Kernel 记录并交给既有升级路径处理。

## 标准验证链

正常链路为：

`arch.proposal.done -> design.critique.done -> dev.build.done -> static_gate.passed -> review.approved -> test.passed -> judge.passed -> discriminator`

- Review 逐项核对本文件是唯一产品变更，并确认中文内容覆盖场景、恢复边界、禁止人工状态移动、验证链和验收命令。
- Test 独立执行文件存在性验收，不能据此声称恢复行为已验证。
- Judge 核对标准 DAG；仅当本任务存在真实受控 stuck 注入时，才继续核对注入、恢复或重新派发的因果链。
- Discriminator 根据已有证据作最终机械判定；worker 不自行声明任务、发布或运行最终通过。

验收命令：

```bash
test -f docs/autoresearch-campaign/stuck-recovery.md
```

命令返回 0 只证明文件存在。event id、恢复结果和最终 verdict 均以本轮实际运行证据为准，本说明不预先宣称这些结果。
