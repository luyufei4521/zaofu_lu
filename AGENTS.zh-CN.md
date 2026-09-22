# AGENTS.md（中文版）

本仓库是 `ZaoFu`。

## 用途

ZaoFu 是一个多智能体 harness engineering（代理工程）脚手架。本仓库处于持续实现状态：确定性内核、运行时、CLI、测试以及本地 Web 面板都已存在。请将设计文档作为上下文，但要以代码和测试验证实际行为。

## 指令范围与优先级

- 这些仓库级规则适用于每个 Codex 和 Claude Code 会话。
- 任务/角色简报可以缩小范围并选择当前任务，但不得削弱状态所有权、安全性、验证或 Git 安全规则。
- 托管的 `Worker Protocol` 区块仅在当前派发简报以 `Active task: <task_id>` 开头时生效。如果没有这一标记，即使该区块存在，也不要仅因它存在而发出任务/工作流事件或心跳。
- 如遇架构冲突，请以 `docs/design/142-layered-runtime-authority-and-orchestration-modes.md` 及当前代码/测试为准。历史设计文档仅作背景参考，不能覆盖当前实现。

## 核心规则

- `zf.yaml` 是唯一的控制平面配置；请遵守 `project.state_dir`，不要硬编码 `.zf`。
- 配置的运行时状态目录（默认为 `.zf/`）是运行时状态，不是源代码。
- 保持确定性内核与由智能体驱动的行为相互分离。
- 对语义性、项目特定或需要判断的行为，优先由 agent/skill/prompt 负责：agent 做决定，skill 提供方法，prompt 提供目标和上下文。将不变量、模式、状态迁移、证据检查、安全性、重放/恢复以及外部副作用保留在确定性代码中。Agent 的决定必须产出工件/事件，或请求受控操作；不得直接修改由内核管理的规范状态。
- 对约束和门禁采用同样的边界：语义质量门禁、项目一致性规则、扫描方法、任务切分和产品验收，应尽可能放在 skill/prompt/agent 工件中。运行时门禁应保持机械化：模式、事件/状态有效性、证据存在性、路径/密钥/预算安全、重放/恢复、生命周期以及外部副作用。如果某项修复体现出可复用的方法，应先将其提升为通用 skill/profile，再硬编码到运行时。
- 只允许一个规范的任务契约（使用 `contract` 字段，而不是 `sprint_contract`）；不要引入重复的任务模式。
- `events.jsonl` 是只追加的发生/排序/因果/裁决/引用账本；请使用 `EventWriter` / `EventLog` 辅助工具。
- 规范的当前状态更新请使用 `TaskStore`、`FeatureStore`、`SessionStore` 和 `RoleSessionRegistry`。
- 必需的工件/sidecar 保存完整的语义正文或大型证据；应以原子方式持久化，并通过引用/摘要与其绑定。它们不是可随意丢弃的读取投影。
- 集成不得直接写入规范业务状态，也不得与编排器内部实现耦合。启用 Feishu 时，出站投影同步和入站意图/引用发布必须通过 `EventWriter` / 受控操作完成；sidecar 正文使用其获准的原子写入器。绝不得绕过这些路径。
- Web/API 投影保持面向读取，除非已经接入确定性、令牌门控的内核操作路径。
- `skills/` 是源目录；`.claude/skills/` 和 `.codex/skills/` 是同步后的分发副本。活跃工作目录/工作树可以包含未提交的候选代码，不是可丢弃的投影。除非更具体的设计另有规定，锁文件、进度、成本、诊断、Trace/Graph/Loop 以及 Web 摘要都属于运行时投影。
- 不要把确定性的 Python `Orchestrator` 运行时与配置为 `orchestrator` 的角色 agent 混为一谈。Product Flow 在内核中保留顺利路径的派发；Legacy safe-team 可以显式启用第二层决策者。Agent 通过工件/事件/受控 CLI 操作报告语义意图，不得成为第二个状态机。
- 保留产品命名（`ZaoFu`、`zf`、`zf-cli`）与方法论命名（`harness engineering`）之间的区别。
- 除非明确要求其他语言，面向仓库的正文、报告、backlog、任务拆分和命令摘要默认使用中文。

## 架构/运行时路径

- `docs/design/00-index.md` 是完整的路由索引。本节中的短列表只是起始路径，并非完整的架构映射。
- `142-layered-runtime-authority-and-orchestration-modes.md` 是权威/编排入口，包含当前的路由族。
- `01-architecture.md`、`02-harness-yaml.md`、`03-orchestrator.md`、`05-task-model.md`、`08-events-observability.md`、`10-recovery-safety.md` 和 `13-interaction-protocol.md` 等基础文档仍可提供有用的历史背景，但必须以 `src/` 和测试核验行为。
- 当前的运行时交互流程是：`zf start` 加载 `zf.yaml` 和 `project.state_dir`，启动 tmux 和/或 stream-json 传输以及已启用的 sidecar；随后 `EventWatcher` 追踪 `events.jsonl`，并在出现需要唤醒的事件时唤醒 `Orchestrator.run_once()`。
- Kernel `Orchestrator` 负责确定性派发、扇出/返工/门禁以及机械化迁移。Worker 通过传输层接收简报，并通过 `zf emit` / 获准的操作报告事实。
- Supervisor 负责观察；Run Manager 决定恢复；Autoresearch 执行深入诊断或有界修复；`ControlledActionService` 应用获批准的确定性操作。
- Web Kanban 视图、Feishu、Inbox、Trace/Graph/Loop 以及摘要都是投影。Provider transcript、频道正文、大型诊断信息和上下文包都是 sidecar 载荷。它们可以请求受控操作，但不得绕过事件账本、规范存储或必需的 sidecar。

## 工作方式

- 在实现前说明重要假设。如果歧义会改变结果且不存在安全假设，请提问；否则明确写出假设后继续。
- 以满足目标的最小可验证改动为准：不要添加推测性功能，不要为一次性代码创建抽象。如果 200 行可以改写成 50 行，就重写。
- 保持差异精确：每一处改动都必须能追溯到任务；不要顺手“改进”无关的代码、注释或格式。
- 对于非平凡且模糊的请求，开始前先定义成功标准（`步骤 -> 验证`）。衡量标准是减少不必要的差异行数和后期澄清循环。

## 代码风格

- 使用 Python 3.11+、`src/` 布局、类型提示、`pytest`、`pathlib`、`dataclasses`，并优先使用标准库。
- 将副作用放在边界层。
- 优先使用现有模块：`src/zf/cli/`、`src/zf/core/`、`src/zf/runtime/`、`src/zf/integrations/`、`src/zf/web/`、`tests/`、`web/`。
- 新文件起始时不得超过 1000 行。当文件接近 800 行且包含两个或更多正交职责时，应按职责拆分。不要把内聚的处理器集合拆成 `_part1.py` / `_part2.py`。
- 除非现有模块明确是正确归属，否则应在过大的文件旁边新增行为，而不是继续追加到该文件中。

## 测试

- 测试行为，而不是实现细节；优先使用确定性测试。
- 覆盖状态迁移、事件追加/查询行为、配置校验，以及编排/验证/恢复缺陷的回归。
- 对配置/运行时/模式/Web/API 的改动，在变更行为附近添加针对性测试。
- 使用 `uv sync --extra dev --extra web` 安装完整测试依赖。
- 使用 `python scripts/dev-verify.py plan --base dev` 解释当前工作树的验证闭包，并使用 `python scripts/dev-verify.py run --base dev` 执行自动层级。该规划器采取保守策略：未映射的 `src/` 改动必须添加直接测试、传入显式 `--tests`，或扩展共享边界规则；绝不能静默地解释为“无需测试”。
- 按变更领域及其影响闭包测试，而不是只按变更文件数量测试。聚焦运行必须覆盖变更模块、其直接调用方，以及它跨越的任何共享 Event/Schema/Store 契约。Web UI 和后端是默认分开的测试领域；只有当变更跨越 API、投影、EventLog、Store 或模式边界时，才需要跨领域测试。
- 必需的测试层级：
  - 仅 UI 的改动：前端构建/类型检查，以及受影响的浏览器或组件测试；默认不要运行后端 pytest。
  - 后端模块改动：受影响模块测试、直接调用方测试，以及共享契约测试。
  - EventLog/Store/模式/配置/编排器/扇出/返工/恢复改动：影响闭包测试、`scripts/dev-premerge-gate.sh`，以及相关的确定性 mock E2E。
  - Provider、tmux、工作树或主机能力改动：先运行隔离的 mock provider 测试；真实 provider/主机测试属于显式层级。
- 完整 pytest 仅用于发布验证、重大跨边界重构、涉及三个或更多核心领域的改动，或负责人明确要求的场景。不要仅因为差异涉及 30 个以上可执行/配置/测试文件就触发完整 pytest。
- 完整验证可以在新进程中按模块/类/节点分片，并设置明确的时间和内存预算。长时间运行或耗尽资源的单体 pytest 进程属于测试基础设施故障，应报告该故障，而不是因此阻塞普通开发。
- 覆盖率是显式的发布层级（`uv run pytest --cov=zf --cov-report=term-missing ...`），不是普通开发中隐含的成本。即使确定性测试并行运行，主机和真实 provider 标记仍需显式指定。
- 聚焦验证不等于完整验证：请报告实际运行的准确层级。广泛的仅文档对照则运行文档/指令检查及针对性的生成器测试。
- 当前仓库的完整测试套件包含主机能力/版本传感器，并可能调用已安装的 provider CLI。请将这类失败单独归类，绝不要盲目重写已验证的哈希/版本基线，也不要把完整套件描述为真实 provider E2E 证明。真实 provider E2E 属于使用隔离状态并完成清理的显式测试层级。
- 对 Playwright/浏览器 E2E，请使用带有 `mcp/playwright:latest` 的 Docker。让 API 和 UI 监听 `0.0.0.0`，使用主机网络运行容器，不要安装主机浏览器，除非得到明确要求。如果 Docker 不可用，请报告确切阻塞原因和预期命令。

## Sprint / Backlog

- `backlogs/` = 被 Git 忽略的本地候选项（`proposed` / `defer`）。未经批准的项目留在这里，不应提交。
- `tasks/` = 活跃 sprint 和归档（`active` / `done`）。获得批准后，使用 `mv backlogs/<file>.md tasks/`，因为新 backlog 通常会被忽略且未跟踪；提交时再精确暂存 `tasks/<file>.md` 路径。只有当 `git ls-files --error-unmatch <source>` 成功时，才使用 `git mv`。已完成的项目仍保留在 `tasks/` 中。
- 新文件使用 UTC 时间格式 `YYYY-MM-DD-HHMM-<slug>.md`。
- 第一段必须包含 `> 状态:`，值只能是 `proposed`、`active`、`done`、`defer`、`superseded`、`obsoleted` 之一。
- `done` 必须包含简短提交哈希和标题；`defer` 必须包含具体触发条件；`superseded` 必须指向替代的 sprint。
- 验收标准使用 `步骤 -> 验证: 检查项` 格式；验证薄弱会导致返工。
- 每完成不少于 10 个 backlog 项目或一个主线批次后，都要对照近期 `git log` 审计过时的 proposed 项目；将确实完成的项目更新为 `done`，仍未解决的更新为 `defer`。

## 提交 / 完成

- 使用一个常规前缀：`feat:`、`fix:`、`docs:`、`style:`、`refactor:`、`test:`、`chore:`。
- `feat:` / `fix:` 面向用户；仅构建/工具链工作使用 `chore:`。
- 对同一功能同时包含测试和实现的 TDD 提交使用 `feat:`。
- Sprint 计划使用 `docs:`。
- 当用户明确批准执行 backlog/task 批次时，运行聚焦验证，并在最终答复前提交实现和任务状态。
- 不要自动提交仅分析性工作或未经批准的 backlog 候选项；`push` 仍需要用户明确请求。
- 在将新的编排组件标记为完成之前，必须证明它已接入实际的运行时/CLI/Web 入口或已注册的服务，并用测试覆盖该调用方；只有库代码而没有调用方不算完成。
- 在修复过时 backlog 缺陷前，先在当前 HEAD 上复现。如果已经无法复现，应标记为“已验证解决”，而不是修改代码。

## 多驱动 Git 纪律（2026-06-11 — 索引竞争事故 `ddd1dd9`）

多个 agent 会话可能同时操作本仓库。以下四条是硬性规则：

- **仅使用显式路径规格**：绝不要使用 `git add -A`、`git add .`、`git commit -a` 或不带路径的 `git commit`，以免把当前暂存区中的其他内容一并提交。只暂存你修改的确切文件，提交前运行 `git diff --cached --name-only`，如果其中包含不属于你的文件就中止。共享索引存在竞争风险——另一个会话暂存的工作可能正在其中。
- **唯一的 dev 合并负责人**：当有多个会话活跃时，每个会话都在自己的工作分支（`wip/<driver>-<utc-date>-<slug>`）上提交；只能由指定的一个会话合并到 `dev`。单独工作时可以直接提交到 `dev`，但提交前必须重新检查 `git log -1`；如果 HEAD 意外移动，就视为存在并发驱动并切换到工作分支。
- **合并前哨兵门禁**：将任何分支合并到 `dev` 前，运行 `bash scripts/dev-premerge-gate.sh`（事件契约/注册表闭包/结构纪律/主干投影，约 2 秒）。如果为红色，不要合并。它不能替代完整回归，只阻止最容易在合并时破坏的类别（2026-07-04 的教训：一次合并重新引入了 13 个失败项）。
- **外部移动 `dev` 引用后，确认检出内容是最新的**：来自其他工作树的 CAS 合并或 `git update-ref` 可能移动 `refs/heads/dev`，却不会更新已经检出 `dev` 的长期工作树。在该工作树中运行 Web/工具链前，确认工作树干净且处于最新状态；不要在过时的树上操作。

## 文档 / 命令

- 架构、运行时、配置模式、Web/API、安全性或外部控制平面行为发生变化时，必须更新 `docs/design/` 或 `docs/impl/` 下的相关文档（`docs/new-design/` 是历史材料；不要在那里新增文档）。
- 新文档必须先选择正确的目录类别（`design`、`impl`、`ideas`、`runbooks`、`manual`、`refer` 或 `records`）；设计文档使用下一个数字编号的 `<number>-<slug>.md` 前缀，并必须登记到 `docs/design/00-index.md`。
- 提交新的 design / impl 文档前，通过确认它已被索引、源码、其他文档、backlog 或 task 引用，检查是否存在孤立文档。
- Claude Code 的详细规则位于 `.claude/rules/`；保持它们与本文件中的跨 provider 硬性规则一致。
- `skills/` 是仓库 skill 的规范单一来源；`.claude/skills/` 和 `.codex/skills/` 是从它同步的分发副本（参见 `skills/zf-tool-skill-parity/`），不是可以独立演进的分支。
- 常用命令：`uv sync --extra dev --extra web`、`python scripts/dev-verify.py plan --base dev`、`python scripts/dev-verify.py run --base dev`、`uv run pytest <focused-paths> -q --no-cov`、`uv run pytest -q --no-cov`、`uv run zf validate --cold-start`、`uv run zf start`、`uv run zf stop`、`uv run zf kanban --board`、`uv run zf trace show <id>`、`uv run zf web --port 8001`。

## 临时模拟卫生

- 将模拟/演示/一次性 E2E 状态放在 `/tmp/zf-<purpose>-<utc-timestamp>/`。
- 将 Web 端口 `8001` 保留给真实开发会话；临时模拟使用 `8002+`。
- 模拟运行结束后发出 `simulation.done`，然后终止其 tmux 会话和 Web 进程。
- 运行结束或诊断结束后，清理临时 tmux 会话、Web 进程和状态目录；过时的 `/tmp` 状态可能掩盖静默运行时缺陷。

<!-- ZF:START -->
## Worker Protocol（由 ZaoFu 管理——请勿编辑标记之间的内容）

此区块由 `zf update agents-md --write` 重新生成。请自由编辑 ZF 标记之外的内容。标记内的编辑会被覆盖。

### 作用域守卫

此协议仅在当前 ZaoFu 派发简报以 `Active task: <task_id>` 开头时生效。在没有该标记的普通交互式开发、审查或操作员会话中，即使存在此区块，也不要仅因它存在而发出任务/工作流事件或心跳。

### 活跃任务固定标识

每份 worker 简报的第一行都是 `Active task: <task_id>`。你发出的每个事件都必须引用此 id；即使用户消息中包含其他 id，也不要另造一个 id。恢复/操作员侧脚本会搜索这一行，以确认 worker 确实正在处理预期任务。缺少 id 或 id 不匹配时，将按故障关闭处理。

来源：`src/zf/runtime/injection.py::generate_task_briefing`；
契约测试：`tests/test_runtime_injection.py`。

### 事件发出通道

Worker 通过 `zf emit <event-type> --task <task_id>` 报告状态变更意图。不要直接写入 `kanban.json` / `feature_list.json` / `progress.md` / `memory/`；请使用获准的 `zf` CLI 命令或内核操作，以保持运行时状态协调一致。

### 禁止自行声明完成

没有支持性的门禁证据时，Worker 不得代表自己的角色发出终态完成事件（`*.passed`、`*.approved`、`task.done`）。内核判别器（`ContractD` / `FunctionalD` / 其他判别器）会核验这些证据，并可能拒绝自行声明；被拒绝的声明会通过 `rework_routing`（见 `zf.yaml`）转入有界返工。

### 子 Agent 递归守卫

如果你的简报包含 `## Recursion Guard (强制)` 区块，说明你正在作为子任务 worker 运行。在此范围内：

- 不要派发其他同角色子任务。
- 只执行父级简报中的指令。
- 除非父级简报明确要求，否则不要修改 `tasks/` / `feature_list.json` / `kanban.json`。

来源：`src/zf/runtime/injection.py::_render_recursion_guard`；
契约测试：`tests/test_runtime_injection.py`。

### 行内覆盖审计

用户消息中出现诸如 `"skip critic"` / `"skip test"` / `"跳过 critic"` / `"跳过 test"` 的字面关键词时，会触发审计事件，并可能跳过某个阶段。Worker 不得代替用户合成这些关键词；在遵循覆盖指令时，必须发出对应的审计事件。

来源：`src/zf/runtime/inline_overrides.py::scan_inline_overrides`；
契约测试：`tests/test_inline_override_scanner.py` 及编排测试。

### 心跳

只有在存在活跃任务标记且任务处于 `in_progress` 状态时，才遵循该任务简报中呈现的精确 `worker.heartbeat` 命令和频率。绝不要臆造或复用 task id，也不要在普通仓库维护会话中发出心跳。
<!-- ZF:END -->
