# 文章来源与主张边界

核查日期：2026-09-12。正文围绕本仓库当前运行示例，外部方法仅作少量转述。没有使用私有业务材料，没有为文档助手虚构用户回答或业务验收结果。

## 公开原始来源

以下 primary 页面已在本次写作任务中打开核对。七域、状态合同和每轮一到三个问题属于本框架设计，不代表外部机构的统一标准或背书。

| 来源 | 支持正文主张 | 不用于证明 |
|---|---|---|
| [Google PAIR · User Needs + Defining Success](https://pair.withgoogle.com/chapter/user-needs/) | 理解现有工作流，判断 AI 相对规则或既有方案是否提供额外价值 | 工作台效果、用户收益、示例已达到目标 |
| [Microsoft · Disambiguate customer intent](https://learn.microsoft.com/en-us/microsoft-copilot-studio/guidance/cux-disambiguate-intent) | 用提问与选项缩小意图歧义 | 固定必须问三题、自动代替用户选择 |
| [Anthropic · Demystifying evals for AI agents](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents) | 执行记录 transcript 与环境最终结果 outcome 需要区分 | 本项目业务已经通过 Agent 评测或验收 |
| [LangSmith · Evaluation concepts](https://docs.langchain.com/langsmith/evaluation-concepts) | 实验对应具体应用版本与数据集，版本比较应保留关联 | 本项目已经接入 LangSmith 或提供自动评测平台 |

每篇来源只支持相邻一段的机制判断，无外部逐字长引文。与本实现相关的事实依据如下。

## 仓库实现与示例依据

- [README](../../README.md)：产品定位、Python 3.10+ 环境、安装、示例预览、生成与校验命令、当前网页边界。
- [安装脚本](../../scripts/install.py)：安装到 CODEX_HOME 下的 skills；未设置时回退 ~/.codex/skills；具体更新与备份选项由 README 说明。
- [Skill 协议](../../skills/ai-dev-workbench/SKILL.md)：读项目事实、澄清、七域同步、受影响范围、同轮回写、状态与用户授权边界；简短 LearnBuddy 来源说明依此。
- [澄清与方案合同](../../skills/ai-dev-workbench/references/discovery-contract.md)：推荐不等于选择、回答来源与日期、自由回答、未决问题作用范围。
- [数据合同](../../skills/ai-dev-workbench/references/data-contract.md)：任务 done / accepted 与版本 local_verified / released、证据关联与校验边界。
- [方法依据](../../skills/ai-dev-workbench/references/ai-product-method.md)：AI / 非 AI 基线、行为合同、配置与评测对应关系。
- [公开示例源数据](../../examples/document-assistant/docs/workbench/workbench.json)与 [SPEC](../../examples/document-assistant/SPEC.md)：截图和正文业务对象、状态、选项与依赖的事实来源。

公开示例与 skill 内 assets/example.json 的业务记录一致；公开版本增加名称中的虚构标识、SPEC 来源链接和简报来源说明。正文以公开示例为准。

## 示例逐项核对

| 正文对象 | 当前源数据事实 | 写作限制 |
|---|---|---|
| 原始诉求 | 团队文档助手，能问资料，之后也许共享 | 不改写成已有对外客户分享要求 |
| Q-SHARE | 项目内共享 / 逐份邀请；open；未选择 | 不虚构用户回答，不将点击当确认 |
| PROP-SHARE | 按项目统一共享 / 按资料单独授权；proposed；推荐 OPT-PROJECT；未选择 | 推荐只在固定项目成员假设下成立；项目共同范围不混入逐资料 ACL |
| 共享假设 | 首批用户可能在固定项目内协作；unverified | 不能把适用前提写成调研事实 |
| REQ-01 | 导入状态可见、刷新一致、失败重试；scheduled | 计划中的行为，不是已实现服务 |
| TASK-01—04 | 状态合同先行，检索与页面依赖它，全流程验收等待两者 | 页面可打开不代表文档助手已有这些能力 |
| 状态存储 CHOICE-01 | proposed，具体运行栈未选 | 本地文件与数据库只比较代价，不替项目选型 |
| V0.1 / V0.2 | planned / candidate；online_version=null | 不称示例业务已交付；不与开源软件 v0.2.0 混淆 |
| evidence | 空数组 | 不制造报告、测试计数或成功率 |

七域后对“按项目统一共享”的描述为明确条件推演，说明选择后应影响哪里；源数据、截图与正文均不宣称该决策已发生。

## 当前正文实操核验

2026-09-12，在独立临时目录复制公开示例，实际执行一次记录变更：

- 将 REQ-01 的刷新验收改为“刷新后仍是同一处理任务，不重复创建，失败可重试”。
- 同步 TASK-01、TASK-03 的退出条件与资料导入页交互；既有测试关键路径已要求同一任务且不重复创建，保留。
- 运行 validate --check-links 和 build，均退出成功，生成首页与两个版本页；检查新页面包含修订后的条件。
- 共享问题和方案仍未选，版本仍为 planned / candidate，evidence 仍为空。
- 另用独立错误数据把 TASK-03 标为 accepted，校验按预期拒绝：TASK-01 依赖未完成，且缺少匹配 passed 证据。

这是工作台记录与生成链路验证，不是文档助手的刷新、解析、检索或权限业务测试。文章不宣称已执行 clone 到读者机器、替读者安装或生成业务应用。

## 发布与图文核验范围

- 本次任务先前已通过 GitHub API 与源码推送结果确认 [wanghui2323/ai-product-workbench](https://github.com/wanghui2323/ai-product-workbench) 为公开仓库，默认分支 main，MIT 许可证；现有发行版为 v0.2.0，附件见 [Releases](https://github.com/wanghui2323/ai-product-workbench/releases)。本轮文章更新不等同新增发行版。
- 先前发行验证记录为本机 Python 3.12.7 的 106 项框架与分发回归通过；它属于框架发行验证，不证明文档助手业务完成，也不替代远端 CI。
- 2026-09-12 对当前六图稿重新完成 Chrome 检查：1440px 与 390px 阅读页均无横向溢出，七节正文、六张正文图及 900×383 封面加载成功；逐张检查手机端图片阅读效果，浏览器无页面脚本错误。
- 实际读取剪贴板确认富文本包含七节正文与六张正文图，封面和工具栏未混入正文；模拟剪贴板拒绝后，页面正确提示并选中完整正文。配图库七张图均加载成功且无横向溢出。这只证明本地复制行为，不证明微信公众号编辑器接收成功。
- 四张截图由公开示例的真实浏览器页面取得，未修改 DOM 或业务数据；[截图清单](capture-screenshots.manifest.json)记录页面、源文件与图片哈希，逐项比对通过。两个机制图保留 SVG 与 PNG，SVG 文字未越界；封面生成记录见 [cover-prompt.md](cover-prompt.md)。
- 未进行微信公众号粘贴、保存、手机预览或发布。
