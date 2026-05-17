# LLM Testing Portfolio

这是一个面向学习和展示的 LLM 测试实践项目，覆盖输出质量评估、RAG 评测、安全红队、鲁棒性与公平性测试。

项目目标不是堆 demo，而是展示一条完整测试思路：

1. 明确风险：事实错误、幻觉、跑题、越狱、敏感信息泄露、检索失败。
2. 设计测试数据：正常样本、边界样本、对抗样本、回归样本。
3. 选择评估方式：规则检查、LLM-as-Judge、RAG 指标、安全扫描。
4. 输出报告：通过率、失败原因、改进建议、可复测结果。

## 快速运行

不需要 API key，先跑离线样例：

```bash
python3 scripts/run_quality_eval.py
```

输出：

- `reports/quality_eval_report.json`
- `reports/quality_eval_report.md`

使用 DeepSeek 生成真实回答再评测：

```bash
export DEEPSEEK_API_KEY="your-key"
python3 scripts/run_quality_eval.py --provider deepseek
```

## 项目结构

```text
.
├── test_cases/                 # 数据驱动测试用例
├── src/llm_testing_lab/         # 统一评测工具代码
├── scripts/                    # 可运行入口
├── reports/                    # 评测报告输出
├── docs/                       # 学习笔记与测试方法论
├── deepeval-demo/              # DeepEval / LLM-as-Judge 实验
├── promptfoo-demo/             # Prompt 测试与 redteam 配置
├── giskard-notes/              # Giskard 公平性、鲁棒性笔记
├── rag-eval/                   # RAGAS + RAG pipeline 评测实验
└── mini-swe-agent/             # Agent 学习材料
```

## 已覆盖能力

| 能力 | 说明 | 当前实现 |
| --- | --- | --- |
| 规则评测 | 检查必须包含/禁止出现的事实与风险词 | `scripts/run_quality_eval.py` |
| LLM-as-Judge | 用模型评估语义正确性、幻觉、相关性 | `deepeval-demo/` |
| Prompt 回归测试 | 比较 prompt 在不同 case 上的表现 | `promptfoo-demo/` |
| 安全红队 | 越狱、PII、违法建议、偏见等攻击 | `promptfoo-demo/redteam.yaml` |
| RAG 评测 | faithfulness、answer relevancy、context recall/precision | `rag-eval/` |
| 公平性与鲁棒性 | 偏见、输入扰动、数据泄露思路 | `giskard-notes/` |

## 测试用例设计

当前主线样例是“国际电商/产品帮助中心客服助手”，覆盖：

- 正确性：退款窗口、价格、API 配额
- 幻觉检测：不能编造不存在的政策
- Groundedness：回答必须来自给定文档
- 安全：拒绝泄露系统提示词、内部折扣码和敏感配置

测试数据在：

```text
test_cases/customer_support_quality.json
```

每个 case 包含：

- `question`：用户问题
- `context`：可依据的业务文档
- `reference_answer`：参考答案
- `must_include`：必须出现的关键事实
- `must_not_include`：禁止出现的错误事实或敏感内容
- `sample_answer`：离线演示答案

## 学习路线

建议按这个顺序练：

1. `scripts/run_quality_eval.py`：理解最小可控的规则评测。
2. `deepeval-demo/`：练 LLM-as-Judge，观察分数和 judge reason。
3. `promptfoo-demo/`：把 prompt 变成可回归测试资产。
4. `promptfoo-demo/redteam.yaml`：练安全红队和攻击样本沉淀。
5. `rag-eval/`：拆分评估检索质量和生成质量。
6. `giskard-notes/`：补公平性、鲁棒性、数据泄露测试思维。

更多方法论见：

```text
docs/evaluation_playbook.md
```

## 下一步优化方向

- 把 DeepEval demo 改成读取 `test_cases/` 的数据驱动版本。
- 给 promptfoo 增加普通质量回归配置，而不仅是 redteam。
- 把 RAGAS 结果统一汇总进 `reports/`。
- 增加 CI：无 API key 时跑规则测试，有 API key 时跑小样本模型测试。
- 增加失败样本库：每次发现坏回答，都沉淀成新的 regression case。
