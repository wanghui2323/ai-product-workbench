# AI 产品开发方法与构建依据

调研核查日期：2026-09-11。以下工作台结构是结合官方方法与本项目用途作出的设计，不是任何来源规定的统一标准。页面用于组织判断、状态与证据；具体实现与实验运行使用项目已有工具。

## 产品定位

支持用户与 AI 协作，把模糊想法推进到可验证的产品。产品包含 AI 能力时，额外管理其行为合同、配置和效果；不要仅因为使用 AI Coding，就强迫一个普通产品引入模型或 Agent。

采用“需求澄清与方案决策 + 七个管理域”，围绕同一组对象关联：原始诉求 → 问题/假设 → 选择 → 需求 → 模块/能力 → 版本 → 任务/实验 → 证据/发布 → 反馈与新需求。稳定 ID 和来源维持追踪，不用任务完成比例代替用户价值证明。

## 分阶段使用，不一次填满所有表

| 阶段 | AI 和用户解决的问题 | 输出与继续条件 |
|---|---|---|
| 发现与澄清 | 为谁、在什么场景、改善什么；目前怎样做 | 问题简报、关键缺口、假设；能界定本次要研究什么 |
| 比较与验证方案 | 哪条路线符合目标与约束；不确定点如何检验 | 2–3 种可比较方案、推荐理由、用户选择或最小验证计划 |
| 定义产品与实现合同 | 用户如何完成任务；AI/人/系统分别负责什么 | 当前范围与非目标、交互/接口/数据状态、可观察验收条件；方向性缺口已解决 |
| 迭代实现与评测 | 哪些任务可独立推进；效果是否比基线改善 | 依赖与工作域、实现产物、配置和测试证据；真实结果满足退出条件 |
| 发布与学习 | 交付了什么；真实用户是否获益；哪里失败 | 配置与产品版本对应、目标环境记录、反馈/坏例、回归与下一轮需求 |

流程允许反复回到前面验证假设，不能变成固定时长的瀑布门。未决问题只限制依赖它的范围。小项目先管理一条完整用户链路和一个可验证版本。

## AI 产品特有信息如何进入七域

| 管理域 | 需要补充的 AI 产品内容 | 使用当前记录位置 |
|---|---|---|
| 需求方案 | 现有办法/非 AI 基线、为什么需要 AI、辅助或自动执行、输入输出、用户成功指标、错误代价 | discovery.brief、requirements.problem/scenario/acceptance、模块用户故事 |
| 技术方案 | Prompt/上下文/检索/工具的边界，模型输出如何变成业务结果，停止/重试/人工接管及数据权限 | 模块 technology 的 mechanism/objects/apis/risks、架构数据流、版本 technical_plan |
| 上线版本 | 同一次交付的代码、模型快照或可用标识、Prompt、工具 schema、知识索引与评测集版本；回退和灰度条件 | 版本技术方案、releases.artifact/preflight/rollback、证据 summary 与详细源文档 |
| 视觉交互 AI 规范 | 能做/不能做的说明，生成/执行/不确定/失败状态，证据查看、纠错、撤销和人工控制 | design.components/states、ai_rules/checks、页面合同与状态矩阵 |
| 技术选型 | 规则、搜索、单次模型调用、固定流程和 Agent 的选择依据；用代表性任务比較质量/时延/成本 | stack.alternatives/why/tradeoffs、决策来源及实验报告 |
| 开发计划及模式 | 最先验证价值或技术假设，再扩大实现；明确单 Agent/并行任务的契约、文件域与集成责任 | development.batches/principles、任务依赖、方案比较的 validation |
| 测试规范 | 能力评测与回归分开；固定数据切片、基线/候选配置、评分器与人类校准；结果、失败归因、成本与时延 | testing.levels/critical_paths、gates、evidence；坏例作为新需求/修复任务，链接原发布和回归用例 |

当前生成器管理上述摘要与关联，不单独执行评测或解析模型配置。详细配置、数据集和实验报告优先索引已有文件；确需大量跨版本实验比较时再扩展专用结构，不能声称已有实验平台或线上监控集成。

每个关键 AI 能力至少说清：输入、预期行为、可观察结果、非 AI 基线、允许失败与恢复、人能否干预、数据边界、质量/费用/时延目标。未知值写待验证，不随意给分。

比较实验时使用可追溯的同一任务集/切片与评分方法。分别标记真实样本、合成样本和人工判断；不同题库的分数不能直接当版本提升。发布记录应能回到被测配置；线上坏例加入回归后再验证修复。用户反馈不等于自动授权训练或发送用户数据。

## 工作台实现路线

1. **Skill + 项目源文件 + 静态视图**：适合个人/小团队借助 Coding Agent 管理项目。AI 在会话主动澄清、读写记录；页面负责理解、比较、填写选择草稿与复制交接。无额外模型密钥或后台依赖，版本可随 Git 管理。这是现有实现。
2. **独立网页 + 本地服务**：当用户需要直接在页面与 AI 对话、提交回答并写回时采用。新增会话、流式响应、数据校验、并发写入保护、变更历史及模型配置；前端选择和持久化状态应清楚区分。
3. **团队协作平台**：当出现真实多人角色、权限、审批、共享通知和平台集成需求再采用。需要后端权威记录、成员权限、冲突处理和审计；不要用 localStorage 或演示按钮伪装共享同步。

选路线时先问主要使用位置、协作人数和已有工具。用户未选择独立服务时不自动扩成 SaaS；他们明确需要网页完成闭环时，也不能仅交一组复制按钮就称需求完成。

## 官方依据及本框架的取舍

- [GOV.UK · Discovery](https://www.gov.uk/service-manual/agile-delivery/how-the-discovery-phase-works)：先研究用户问题、约束、范围及成功度量。这里借用阶段目标，不照搬政府审批流程或典型周期。
- [Design Council · Double Diamond](https://www.designcouncil.org.uk/resources/the-double-diamond/)：理解问题、重新定义、探索不同解法、小范围检验。这里据此增加澄清与方案比较入口，而非把已有七域变成七个固定阶段。
- [Microsoft · Disambiguate customer intent](https://learn.microsoft.com/en-us/microsoft-copilot-studio/guidance/cux-disambiguate-intent)：针对歧义提问或提供选项，问题数量需与帮助程度平衡。每轮通常 1–3 问是本框架的交互建议，不是来源规定的标准。
- [Google PAIR · User Needs + Defining Success](https://pair.withgoogle.com/chapter/user-needs/)：验证 AI 的独特价值，考虑规则基线，区分辅助与自动化。这里将其落实为用户结果、baseline 和 ai_role。
- [Anthropic · Building effective agents](https://www.anthropic.com/engineering/building-effective-agents)：按需要选择简单方案、固定工作流或 Agent。这里要求选型写依据与验证，不把多 Agent 当默认架构。
- [Anthropic · Demystifying evals for AI agents](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents)：区分任务、尝试、评分、轨迹和环境最终结果，并分别维护能力与回归评测。这里将其落到测试合同与证据。
- [LangSmith · Evaluation concepts](https://docs.langchain.com/langsmith/evaluation-concepts) 与 [Manage datasets](https://docs.langchain.com/langsmith/manage-datasets)：实验关联应用与数据集，线上问题可回到离线测试，数据集保留版本。这里采用可复现关系，不要求使用 LangSmith 或新增供应商。
