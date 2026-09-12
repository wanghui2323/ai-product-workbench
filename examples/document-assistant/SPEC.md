# 文档助手 · 完全虚构的公开示例

这是 AI 产品开发工作台的演示数据，不是可运行的文档问答产品，也不包含任何客户资料、用户记录或私有项目快照。所有角色、需求、场景、日期与开发状态均为虚构。

## 目标与边界

让项目成员导入资料、提出问题，并查看回答对应的原文位置。先与关键词搜索和人工阅读比较价值，再决定是否使用生成模型。V0.1 的计划范围是资料状态与带引用的回答；V0.2 的共享粒度仍需用户选择。

本示例没有 API 服务、模型密钥、真实文档处理、真实权限隔离或已发布产品。工作台中的页面、服务和发布条目只用于展示管理合同，不能作为能力已经实现的证据。

## 需要解决的业务问题

- 提交文件后，用户需要知道资料正在处理、可检索或失败，而非只看到上传成功。
- 回答必须提供可核对的原文位置；没有依据时应明确说明。
- 共享需要先选择项目范围还是逐份授权。这项未决选择只影响共享需求，不阻塞独立的 V0.1 方案工作。

## 对象与验证设计

`Document` 保存处理状态；`Chunk` 保存原文位置；`Answer` 引用可回溯片段；`Membership` 或 `Visibility` 的具体访问模型尚未决定。解析失败不能被标为可检索，撤销授权后的结果不能继续泄露内容。

计划中的验证包括处理中刷新、无依据问答、失败恢复和跨范围检索。未运行这些产品测试，因此示例没有 passed 证据，也不声称产品验收通过。

## 如何查看

在仓库根目录运行：

```bash
python3 skills/ai-dev-workbench/scripts/workbench.py validate --project-root examples/document-assistant --data examples/document-assistant/docs/workbench/workbench.json --check-links
python3 skills/ai-dev-workbench/scripts/workbench.py build --project-root examples/document-assistant --data examples/document-assistant/docs/workbench/workbench.json
```

打开生成的 `docs/workbench/index.html`。选择“全部版本”可以查看 V0.2 的共享问题和方案比较；页面填写的回答或选择仅可复制给 AI，不会修改源数据。
