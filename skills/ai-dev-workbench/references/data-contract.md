# 工作台数据合同

仅在使用随包生成器时适用。已有工作台可保留其格式与字段名，遵守同样的信息关系即可。

## 文件与信息责任

`docs/workbench/workbench.json` 保存状态与导航；`index.html` 和 `versions/<id>.html` 是生成视图。项目原有 PRD、技术文档、SPEC / ADR 保存详细设计和决策原文。不要同时编辑视图里的状态。

完整框架在基础台账之外还有 `discovery`（需求澄清与方案决策）、`blueprint`（产品、架构和开发蓝图）与 `governance`（选型、设计、测试和上线治理），分别见 [澄清合同](discovery-contract.md)、[方案数据结构](blueprint-contract.md) 和 [治理合同](governance-contract.md)。初始化生成全部空骨架；旧台账可不带扩展字段继续构建，但不应因此宣称内容已完整。

所有对象 ID 使用字母、数字、点、下划线或横线，并在全文件唯一。日期用 ISO 8601；优先带时区的核查时间。`href` 为仓库相对文件路径（允许 `#fragment`），或完整 http / https URL；本地绝对路径、路径逃逸及脚本 URL 均不接受。远程 URL 不会由校验器抓取。

每个列表字段必须存在，可以为空。下表列出必填字段；例子见 [示例数据](../assets/example.json)。示例完全虚构，不能复制其任务状态当项目事实。

| 对象 | 必填字段 |
|---|---|
| 根 | `schema_version: 1`、`project`、`requirements`、`versions`、`tasks`、`gates`、`evidence`、`decisions`、`archive` |
| project | `name`、`purpose`、`updated_at`、`current_version`、`online_version`、`sources: [{label, href}]`、`next_action` |
| requirement | `id`、`title`、`problem`、`scenario`、`priority`、`status`、`version_id`、`acceptance: [文字]`、`source` |
| version | `id`、`title`、`goal`、`status`、`scope: [文字]`、`non_goals: [文字]`、`requirements: [需求ID]`、`product_plan`、`technical_plan`、`execution_plan`、`risks: [文字]`、`next_action` |
| task | `id`、`title`、`version_id`、`requirement_ids: [需求ID]`、`owner`、`module`、`status`、`depends_on: [任务ID]`、`deliverable`、`exit_criteria: [文字]`、`evidence_ids: [证据ID]`、`blocker`、`next_action` |
| gate | `id`、`version_id`、`title`、`kind`、`required: true/false`、`status`、`evidence_ids: [证据ID]`、`reason`、`next_action` |
| evidence | `id`、`version_id`、`task_id`、`label`、`kind`、`status`、`environment`、`recorded_at`、`command`、`href`、`summary` |
| decision | `id`、`title`、`version_id`、`decision`、`rationale`、`href` |
| archive | `label`、`href`、`note` |

`project.current_version`、`online_version`、需求的 `version_id`、证据的 `task_id`、决策的 `version_id` 允许 null。`source` 是文字来源说明，不必为 URL。没有运行命令的人工观察允许 `command: ""`，但必须写观察者 / 对象 / 结果到 summary。无阻塞的 `blocker`、无豁免的 `reason` 可为空字符串。

## 状态表

| 对象 | 值与含义 |
|---|---|
| 需求 | `idea` 待澄清、`ready` 可排期、`scheduled` 已排期、`accepted` 已验收、`dropped` 暂不采纳 |
| 版本 | `candidate` 候选、`planned` 已计划、`in_progress` 开发中、`local_verified` 本地验证通过、`released` 已交付且目标环境验证、`archived` 历史档案 |
| 任务 | `todo` 待做、`doing` 进行中、`blocked` 阻塞、`done` 实现完成待验收、`accepted` 退出条件已验证 |
| 验收门 | `pending` 未验证、`passed` 通过、`failed` 未通过、`waived` 有理由豁免 |
| 证据 | `observed` 观察记录、`passed` 针对该范围验证通过、`failed` 验证失败 |

验收门 kind：`local` 本地验证、`review` 人工复核、`backup` 备份、`deploy` 目标交付 / 发布、`online` 目标环境验证、`other` 其他。`online` 对 CLI / 库可以是干净安装和真实使用验证，不要求必须有网站。不是每个项目都需要 backup 或 review。

## 关联与完成约束

- 需求排期后必须绑定版本，并出现在该版本 requirements；两端一致。任务引用该版本内需求。纯工程任务可以没有 requirement_ids，但应说明对版本交付的作用。
- 任务必须有产物与退出条件。blocked 必须写原因和下一步；依赖必须存在且不能成环。accepted 需要与本任务 / 本版本匹配的 passed 证据，依赖任务至少完成实现。
- passed 验收门需要该版本的 passed 证据。waived 必须有具体理由与依据，不能用来回避项目明定的硬门；工具无法判断业务授权是否充分，由使用者核对。
- local_verified 至少有一个 required local 门通过，所有 required local 门通过；允许独立的发布任务未完成。
- released 必须有全部任务 accepted，全部 required 门 passed 或合理 waived，并有 deploy 与 online 两种通过的门；online_version 只能指向这样的版本。只有历史版本文字、缺少可追溯证据时，用 archived 并写明历史事实和未核验部分，不伪造通过记录。
- 需求 accepted 要有实际关联任务且这些任务全部 accepted。本工具不自动把完成任务提升为需求 / 版本完成。

证据需要匹配具体对象和检查范围：例如一个接口测试通过，不能支持“手机整条流程验收”。记录测试环境、时间、输入 / 操作、结论、报告位置；在 summary 中写代码 commit 或被测产物版本，未记录时如实说明。比较旧证据的版本、代码与当前改动，判断是否需要重跑；工具不验证报告内容，也不检测代码变化导致的证据过期。

## 接手提示与更新约定

生成的复制提示应包含项目来源、需求与版本边界、任务依赖、模块、产物、退出条件和证据要求。复制不等于启动执行，浏览器也不会写回 JSON。

每轮更新路径：核实真实变化 → 修改负责该字段的源记录 → 更新核查时间与下一步 → validate → build → 刷新浏览器。ID 保留不重排；范围变化更新版本摘要，重大取舍写回已有 ADR。复核各入口有无版本 / 统计矛盾，不只相信校验器。
