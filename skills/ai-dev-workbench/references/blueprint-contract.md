# 方案数据结构

随包模板通过可选的根字段 `blueprint` 展示完整方案。旧台账数据仍可生成；缺 blueprint 时显示待补方案，不制造技术事实。所有字段以下表为准，可为空列表；未知文本写明待确认。

| 对象 | 字段 |
|---|---|
| blueprint | `positioning`、`users`、`journey`、`modules`、`architecture`、`development`、`evolution` |
| users[] | `role`、`need`、`success` |
| journey[] | `id`、`title`、`actor`、`action`、`object`、`output`、`module_ids: [模块ID]`、`exception` |
| modules[] | `id`、`name`、`positioning`、`value`、`users: [文字]`、`stories: [文字]`、`requirement_ids: [需求ID]`、`pages`、`technology` |
| pages[] | `id`、`name`、`purpose`、`interactions: [文字]`、`states: [文字]`、`route`、`priority`、`status`、`reality`、`task_ids: [任务ID]`、`evidence_ids: [证据ID]` |
| technology | `strategy`、`key_tech: [文字]`、`objects`、`apis`、`risks`、`mechanism` |
| objects[] | `name`、`states: [文字]`、`truth`（权威记录位置与状态来源） |
| apis[] | `method`、`path`、`purpose` |
| risks[] | `risk`、`mitigation` |
| architecture | `summary`、`layers`、`edges`、`flows` |
| layers[] | `id`、`name`、`responsibility`、`module_ids: [模块ID]` |
| edges[] | `from: 层ID`、`to: 层ID`、`label` |
| flows[] | `id`、`title`、`steps`、`failure` |
| steps[] | `from`、`to`、`action`、`data`（均为说明文字） |
| development | `principles`、`batches`、`verification`、`sync_note` |
| principles[] | `title`、`practice`（本项目具体做法） |
| batches[] | `id`、`version_id`、`title`、`status`、`goal`、`why`、`task_ids: [任务ID]`、`entry_conditions: [文字]`、`exit_criteria: [文字]` |
| verification[] | `level`、`method`、`evidence`（验证层次、实际入口、证据形态，均为文字） |
| evolution[] | `id`、`version_id`、`title`、`problem`、`before`、`after`、`rationale`、`impact`、`source`（文字来源） |

ID 与台账对象全局唯一。页面 `priority` 同需求为 P0–P3；`status` 为 planned / built / verified，表示页面或能力入口的实现情况；`reality` 为 planned / mock / partial / connected / verified，表示服务接入与真实验证。两者 verified 都需要关联的 passed 证据；built、connected 只是实现记录，不自动证明验收。connected 不代表持久化或生产可用，必须在 states 或 evidence.summary 中说明范围。

批次 `status` 为 past / current / next / later，描述执行顺序，不推断验收。每批关联已定义版本与该版本任务；跨版本前置条件写在 entry_conditions。方案演进关联版本并说明从哪份来源得出 before / after，不能把候选目标写成已建事实。

页面的 route 与 API path 为展示文本，不自动请求或当作可点击链接。实际来源与证据链接仍放基础合同的 project.sources / evidence / decisions / archive，采用仓库相对路径。
