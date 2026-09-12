# 选型、设计、测试与上线治理

根字段 `governance` 承载这四个独立管理域，和需求/版本/任务使用同一套 ID 引用。缺失或空值表示尚未整理，不推断该项目没有规范。

| 对象 | 字段 |
|---|---|
| governance | `design`、`stack`、`testing`、`releases` |
| design | `principles`、`tokens`、`components`、`ai_rules: [文字]`、`checks: [文字]`、`source` |
| principles[] | `title`、`rule` |
| tokens[] | `name`、`value`、`purpose` |
| components[] | `name`、`usage`、`states: [文字]` |
| stack[] | `id`、`area`、`choice`、`alternatives: [文字]`、`why`、`tradeoffs: [文字]`、`status`、`version_id`（可 null）、`source` |
| testing | `strategy`、`levels`、`critical_paths`、`rules: [文字]`、`source` |
| levels[] | `name`、`scope`、`command`、`pass_criteria`、`evidence` |
| critical_paths[] | `title`、`steps: [文字]`、`expected`、`recovery` |
| releases[] | `id`、`version_id`、`environment`、`state`、`artifact`、`recorded_at`、`changes: [文字]`、`preflight: [文字]`、`deploy_steps: [文字]`、`rollback`、`evidence_ids: [证据ID]`、`notes` |

未指定类型的字段均为字符串。所有列表可为空；未知值如实标记。`source` 是来源说明；可点击原文链接统一放 project.sources。设计规范的源文件、实际被浏览器加载的样式、验证结果是三个不同对象，不能互相代替。

## 技术选型

status 为 proposed / adopted / retired。解释为什么符合该项目约束、备选是什么、付出什么代价；写清与已有系统的兼容，不为填表重新选技术。采用新库或依赖不稳定的产品信息时核对当前官方资料。记录既有 ADR 时标明来源日期，不把历史描述当当前市场判断。

## 视觉交互 AI 规范

AI 的执行链：读取规范和目标页面 → 输出页面信息顺序、主行动、对象/接口和状态矩阵 → 复用 Token/组件 → 实现 → 浏览器核对真实加载、交互与响应式。无目标项目规范时可提出建议，明确待采用；不可把框架自身的深色工作台皮肤写成用户产品的设计规范。

tokens 保存有实际消费者的语义名与值；components 说明使用场景与状态；ai_rules 写 AI 执行约束；checks 写可观察检查。优先索引和引用已有 CSS / 设计文档，不另造平行真相源。

## 测试规范

写清测试层次、覆盖边界、真实运行入口、通过标准与证据位置。需要时区分单元、接口、UI、端到端、AI 输出评测、权限、恢复与目标环境验收。层数按项目需要，不能空挂所有类型。标准不是结果；执行后的结果归 evidence / gates。生成器不会执行 command 字段。

AI 产品需用代表任务定义输入、允许行为及可观察结果；区分能力提升与回归、真实与合成数据，保留数据集切片/版本、基线与候选配置、评分器版本和人工校准依据。质量、失败类型、费用和时延分开观察；线上坏例回到关联需求/修复任务和回归样例。配置与实验原文继续保存在已有项目文件，工作台索引它们，详见 [AI 产品方法](ai-product-method.md)。

## 上线版本管理

版本范围与任务属于 versions / tasks；每次候选交付或实际发布事件属于 releases。一次版本可以有多次发布尝试或回滚，保留记录 ID 与时间，不能仅用最新状态覆盖失败历史。

state：planned 计划；candidate 候选；deployed 已执行交付；verified 目标环境验收通过；rolled_back 已回滚；historical 历史记载未现场复核。`artifact` 记录实际 commit/tag/构建号或包版本；`environment` 说明去哪；`preflight`、`deploy_steps` 和 `rollback` 是流程与恢复条件；执行证据另列。计划步骤不构成执行授权。

包含 AI 能力时，交付身份还要能追到代码、模型可用版本标识、Prompt、工具 schema、知识源/索引和已评测数据集。无法固定供应商模型快照时记录别名、配置与核查时间，不声称完全可复现。监控/回退/用户纠错是否接通须有实际证据，不能由配置文件存在推导为已运行。

deployed / verified / rolled_back 必须有同版本 passed 证据；deployed / verified 还需 deploy 门通过，verified 需关联基础合同已验收交付的 released 版本。历史材料只有文字记录时保留 historical，不能为了让界面显示绿色而补假的发布证据。是否需要备份、人工确认或灰度继承项目实际要求。
