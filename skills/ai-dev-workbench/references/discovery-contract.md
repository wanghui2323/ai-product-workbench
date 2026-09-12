# 需求澄清与方案决策

用于原始请求含糊、存在冲突、缺少成功标准或用户需要比较路线时。已知事实先从仓库与会话读取；不要把所有字段都变成问卷。

## AI 的澄清行为

1. 先复述理解，分开列出已明确事实、影响方向的缺口、可先采用的低风险假设。不要把用户随口举例当唯一业务范围。
2. 优先识别目标用户、触发场景、要改善的结果、当前做法、范围、约束、AI 的角色与成功标准。只问会改变产品范围、关键体验、数据边界、费用或验收的问题。
3. 每轮通常提出 1–3 个关键问题，说明“不确定什么、答案影响什么”。可用时调用宿主的结构化提问工具；否则用简短自然语言提问。支持自由回答、组合方案及“暂时不知道”。不能要求用户先写好 PRD。
4. 有合理路线时给 2–3 个有实质差异的方案。按适用场景、核心范围、收益、代价、复杂度、风险、最小验证比较；推荐一个并写出成立条件。避免仅用“简单/标准/高级”包装相同方案，也不捏造精确工期、成本或评分。
5. 用户无法选择时，提出最小验证：样例、流程草图、小原型或数据探查，并说明它能解决哪个分歧。用户已授权的研究、原型及不受该答案影响的工作继续进行；决定关键方向的答案未到时，相关需求不得变成已确认或开始依赖它的实现。
6. 用户回答后，记录原意与来源，更新问题、选择、需求验收条件、版本范围和受影响方案。没有改变目标或重大范围时直接据答案推进，不反复要求“最终确认”。默认选项、页面推荐、超时、AI 推断和复制动作都不是用户决策。

澄清停止条件：当前迭代的用户、场景、范围及非目标、约束和可观察验收条件足够支撑下一步，且没有尚未回答的方向性问题。无需先澄清所有未来版本。方案变更后重新打开受影响问题，不回退无关已完成工作。

## 数据结构

根字段 `discovery` 可选以兼容已有工作台；新初始化包含空骨架。下表对象字段均必填，列表可为空；未标类型为字符串，ID 在全文件唯一。它是跨七域的入口，不替代原需求、技术和版本记录。

| 对象 | 字段 |
|---|---|
| discovery | `brief`、`questions`、`proposals`、`assumptions` |
| brief | `raw_request`、`users`、`problem`、`scenario`、`outcome`、`success_metrics: [文字]`、`constraints: [文字]`、`non_goals: [文字]`、`ai_role`、`baseline`、`source` |
| questions[] | `id`、`question`、`why`、`blocking: boolean`、`requirement_ids: [需求ID]`、`version_id: ID/null`、`status`、`options: [{id, label, description}]`、`selected_option_id: ID/null`、`answer`、`answer_source`、`answered_at`、`next_action` |
| proposals[] | `id`、`title`、`question_ids: [问题ID]`、`requirement_ids: [需求ID]`、`version_id: ID/null`、`blocking: boolean`、`options`、`recommended_option_id: ID/null`、`recommendation_reason`、`status`、`selected_option_id: ID/null`、`decision`、`decision_source`、`decided_at` |
| proposals[].options[] | `id`、`title`、`summary`、`fit`、`scope: [文字]`、`benefits: [文字]`、`tradeoffs: [文字]`、`effort`、`risks: [文字]`、`validation` |
| assumptions[] | `id`、`statement`、`risk`、`validation`、`status`、`source` |

问题状态：`open / answered / deferred`。answered 必须有非空 answer、answer_source 与 ISO 日期 answered_at；选项属于该问题，selected_option_id 可 null 以接受自由回答。未回答时这四个回答字段留空/null。deferred 写可执行 next_action，方向性问题仍然未解除。

方案状态：`proposed / selected / deferred / superseded`。每组至少两种方案；有推荐必须有 recommendation_reason；selected 必须有 decision、decision_source、ISO 日期 decided_at，可选择本组选项，也可 selected_option_id 为 null 并在 decision 记录自定义或组合方案。非 selected 不得填写 selected_option_id；superseded 可保留原决策文字和来源，但写明被什么替代。

假设状态：`unverified / validated / rejected`；validated/rejected 需要非空来源，不把假设提升为用户回答。

## 未决事项的作用范围

blocking 表示该答案是相关范围进入实现的必要输入。问题与方案都可阻塞；待定方案也不得被 AI 悄悄选中。

- 有 requirement_ids：只作用于这些需求及引用它们的任务；version_id 如有值，需求必须属于该版本或尚未排期。
- 没有 requirement_ids、但有 version_id：作用于该版本。
- 两者均空：作用于当前项目，谨慎使用；从旧项目迁移时不要凭缺少历史访谈就新增全局阻塞。
- 未解决的 blocking 问题（open/deferred）或方案（proposed/deferred）不允许受影响需求 ready/scheduled/accepted，或受影响任务 doing/done/accepted。blocked 任务可记录暂停的既有工作。
- 版本级/全局阻塞不允许版本 in_progress/local_verified/released；需求级阻塞不禁止同版其他独立需求继续开发，但该版不能 local_verified/released。archived 历史版本不因新问题被重新打开。

这是结构一致性校验，不判断用户答案是否真实、完整或被正确理解；需要 AI 对照原始回答核查。

## 页面交互与实际提问

“需求澄清与方案决策”展示产品简报、待回答问题、对比选项、推荐理由和已记录决策。总览突出当前未决事项；复制开发任务必须携带作用于它的未决事项，并要求先澄清。

默认静态页不运行模型，也不直接写源文件。用户在页面填写回答或选择方案后，可以复制自己的选择给 AI；明确提示“尚未回写项目记录”。允许自由补充，复制失败提供手动文本。浏览器选择不能直接把需求标 ready，不能把未回答的问题显示为已解决。AI 在会话中主动提问，在收到用户回答后负责回写并重建页面。
