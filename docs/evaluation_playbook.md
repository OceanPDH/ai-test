# LLM 测试能力地图

这个项目可以按四层能力来练习和展示。

## 1. 确定性规则测试

目标：用稳定、便宜、可进 CI 的方式捕捉明显错误。

- 必须包含：关键事实、政策边界、金额、时间、错误码
- 禁止包含：内部信息、错误承诺、敏感词、编造事实
- 适合工具：`pytest`、本项目的 `scripts/run_quality_eval.py`

## 2. LLM-as-Judge

目标：评估语义正确性、完整性、语气、拒答质量。

- 适合工具：DeepEval、自定义 judge prompt
- 关键风险：judge 不稳定、模型偏见、阈值漂移
- 最佳实践：保存 judge 原因，并保留人工抽查样本

## 3. RAG 评测

目标：拆开看检索和生成。

- Faithfulness：回答是否忠实于上下文
- Answer relevancy：回答是否切题
- Context recall：关键证据有没有被召回
- Context precision：召回内容是否噪声太多
- 适合工具：RAGAS、Phoenix、LangSmith

## 4. 安全与红队

目标：发现 prompt injection、越狱、PII 泄露、非法建议等问题。

- 适合工具：promptfoo redteam、Giskard
- 关键实践：把失败样本沉淀成回归用例
- 展示方式：列出攻击类型、失败原因、修复策略、复测结果

## 作品集展示建议

每个实验都回答四个问题：

1. 我在测什么风险？
2. 测试数据怎么构造？
3. 通过/失败标准是什么？
4. 失败后如何定位和改进？
