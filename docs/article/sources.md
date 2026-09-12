# 文章来源与主张边界

核查日期：2026-09-12。只读公开 primary 页面与本仓库源文件；没有使用私有业务材料。外部方法是参考，本框架的七域、状态合同和每轮一到三个问题是作者实现与设计取舍，不代表这些机构的统一标准或背书。

## 已重新打开的公开原始来源

| 来源 | 本轮核查内容 | 支持正文主张 | 不用于证明 |
|---|---|---|---|
| [Google PAIR · User Needs + Defining Success](https://pair.withgoogle.com/chapter/user-needs/) | Map existing workflows / Decide if AI adds unique value | 先理解现有做法，并比较 AI 是否比规则或现有方案提供额外价值 | 本工作台有效性、真实用户收益、权限架构正确性 |
| [Microsoft · Disambiguate customer intent](https://learn.microsoft.com/en-us/microsoft-copilot-studio/guidance/cux-disambiguate-intent) | 文档正文可读，定义意图消歧并提出问题与选项两类方法 | 用关键提问或选项缩小歧义 | 不是“固定必须问3题”的依据 |
| [Anthropic · Demystifying evals for AI agents](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents) | Definitions: task/trial/transcript/outcome；代码、模型、人工评判范围 | 执行记录与环境最终状态不同，模型声称成功不等于实际结果成功 | 不以别的 Agent 基准分证明本项目；不搬用厂商测试数字 |
| [LangSmith · Evaluation concepts](https://docs.langchain.com/langsmith/evaluation-concepts) | Experiment：specific application version on a dataset；包含输出、评分和轨迹 | 版本比较需要将被测应用配置与数据集对应起来 | 本项目已经接入 LangSmith、自动跑评测或上线监控 |

正文为少量转述，无外部逐字长引文。每篇来源仅支持相邻一段，主要文档助手设计为作者的教学推演。

## 本地实现来源

- `../../README.md`：产品定位、安装入口、使用边界、标准库运行环境和状态说明。
- `../../scripts/install.py`：实际安装逻辑。安装脚本和 README 必须保持一致；正文说明 Codex skills 安装位置、CODEX_HOME 未设置时的回退路径，以及显式读取 SKILL.md 的替代入口。
- `../../skills/ai-dev-workbench/SKILL.md`：澄清、七域同步、只作用于相关范围、当前网页交互责任。
- `../../skills/ai-dev-workbench/references/discovery-contract.md`：用户回答来源/日期、推荐不等于选择、自由回答和范围阻塞。
- `../../skills/ai-dev-workbench/references/data-contract.md`：done、accepted、local_verified、released、证据关联与校验边界。
- `../../skills/ai-dev-workbench/references/ai-product-method.md`：AI 非 AI 基线、行为合同、配置和评测关联；本轮亦独立打开上述公开文档核对。

## 教学例子的定义

虚构产品：文档助手。原始诉求：团队能问资料，最好答案还能分享给客户。候选路线：个人资料助手 / 项目内分享 / 外部客户分享。虚构用户最终明确选择：首版项目内、按资料权限访问、答案能看引用；客户外链以后再议。

后文的检索前权限过滤、分享访问时重新核查、引用与版本记录、失败测试都是此假设选择下的方案推演；不是对示例代码已经提供相应功能的声明。本文没有虚构访谈、用户量、正确率、效益或真实业务验收。

## 本轮交付核验

- 2026-09-12，GitHub API 与源码推送结果确认 [wanghui2323/ai-product-workbench](https://github.com/wanghui2323/ai-product-workbench) 为公开仓库，默认分支 main，MIT 许可证。本文对应 v0.2.0；发行附件以 [Releases](https://github.com/wanghui2323/ai-product-workbench/releases) 页面为准。
- 本机 macOS / Python 3.12.7：106 项回归通过，安装结果与发行 skill 一致，格式校验通过。远端 CI 独立记录在仓库 Actions；本地结果不替代远端执行。
- 三张正文图与封面均已导出，SVG 可编辑；浏览器核对桌面与 390px，无缺图或整页横向溢出。
- 正文富文本复制已实测：剪贴板含正文及 3 个图片标签，不含工具栏；权限拒绝时能选中正文回退。
- 已交付本地文章与公开源码，未进行微信公众号的粘贴、保存、预览或发布。
