"""
RAGAS 评估脚本（RAGAS 0.4.x 兼容版）
======================================
用 RAGAS 框架评估 RAG pipeline 的检索和生成质量。

评估指标：
  - Faithfulness:       回答是否忠实于召回文档（不编造）
  - Answer Relevancy:   回答是否切题
  - Context Recall:     召回文档是否包含答案所需信息
  - Context Precision:  召回文档中有多少真正有用

运行：
  export DEEPSEEK_API_KEY='your-key'
  python3 eval_ragas.py
"""

import os
import json
import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)

from datasets import Dataset
from ragas import evaluate
# ragas.metrics 是旧路径，有 deprecation warning，但在 0.4.x 中仍是 evaluate() 唯一兼容的入口
from ragas.metrics import faithfulness, answer_relevancy, context_recall, context_precision
from ragas.llms import LangchainLLMWrapper
from ragas.embeddings import LangchainEmbeddingsWrapper
from langchain_openai import ChatOpenAI
from langchain_community.embeddings import HuggingFaceEmbeddings

from rag_pipeline import RAGPipeline

DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY") or os.environ.get("OPENAI_API_KEY")
if not DEEPSEEK_API_KEY:
    raise EnvironmentError("请设置 DEEPSEEK_API_KEY 环境变量")


def configure_metrics():
    """配置 DeepSeek 作为评判 LLM，本地模型作为 embedding"""
    lc_llm = ChatOpenAI(
        model="deepseek-chat",
        api_key=DEEPSEEK_API_KEY,
        base_url="https://api.deepseek.com",
        temperature=0,
    )
    ragas_llm = LangchainLLMWrapper(lc_llm)

    lc_embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    ragas_embeddings = LangchainEmbeddingsWrapper(lc_embeddings)

    for metric in [faithfulness, context_recall, context_precision]:
        metric.llm = ragas_llm

    answer_relevancy.llm = ragas_llm
    answer_relevancy.embeddings = ragas_embeddings

    return [faithfulness, answer_relevancy, context_recall, context_precision]


def run_pipeline_on_test_cases(pipeline: RAGPipeline, test_cases: list[dict]) -> list[dict]:
    results = []
    total = len(test_cases)
    for i, tc in enumerate(test_cases, 1):
        print(f"[{i}/{total}] {tc['question']}")
        result = pipeline.query(tc["question"])
        results.append({
            "question": result["question"],
            "answer": result["answer"],
            "contexts": result["contexts"],
            "ground_truth": tc["ground_truth"],
        })
        print(f"       → {result['answer'][:60]}...")
    return results


def print_results(result):
    df = result.to_pandas()

    metric_labels = {
        "faithfulness": "忠实度（不编造）",
        "answer_relevancy": "回答相关性",
        "context_recall": "上下文召回率",
        "context_precision": "上下文精确率",
    }

    print("\n" + "=" * 60)
    print("📊 RAGAS 评估结果（各指标平均分）")
    print("=" * 60)

    score_cols = [c for c in df.columns if c in metric_labels]
    for key in score_cols:
        label = metric_labels[key]
        score = df[key].dropna().mean()
        bar = "█" * int(score * 20) + "░" * (20 - int(score * 20))
        status = "✅" if score >= 0.7 else "⚠️ " if score >= 0.5 else "❌"
        print(f"{status} {label:<20} {bar} {score:.3f}")

    print("\n📋 逐条得分：")
    # RAGAS 0.4 内部列名：user_input / response / retrieved_contexts / reference
    q_col = "user_input" if "user_input" in df.columns else "question"
    a_col = "response" if "response" in df.columns else "answer"
    for _, row in df.iterrows():
        print(f"\n  Q: {row[q_col]}")
        print(f"     A: {str(row[a_col])[:50]}...")
        for col in score_cols:
            val = row[col]
            val_str = f"{val:.2f}" if val == val else "N/A"
            print(f"     {metric_labels[col]}: {val_str}")

    print("\n💡 指标解读：")
    print("  Faithfulness < 0.7    → 模型在编造文档中没有的内容")
    print("  Answer Relevancy < 0.7 → 回答跑题，没有正面回答问题")
    print("  Context Recall < 0.7   → 检索器漏掉了关键文档")
    print("  Context Precision < 0.7→ 检索器引入了太多噪声文档")

    df.to_csv("eval_results.csv", index=False, encoding="utf-8-sig")
    print("\n详细结果已保存到 eval_results.csv")


def main():
    print("=" * 60)
    print("RAG 评估 — RAGAS 0.4 + DeepSeek")
    print("=" * 60)

    pipeline = RAGPipeline("knowledge_base")

    with open("test_cases.json", encoding="utf-8") as f:
        test_cases = json.load(f)
    print(f"共 {len(test_cases)} 个测试 case\n")

    print("--- 运行 RAG Pipeline ---")
    raw_results = run_pipeline_on_test_cases(pipeline, test_cases)
    dataset = Dataset.from_list(raw_results)

    print("\n--- 配置评估模型 ---")
    metrics = configure_metrics()

    print("--- 开始 RAGAS 评估（会调用 DeepSeek API）---")
    result = evaluate(dataset=dataset, metrics=metrics)

    print_results(result)


if __name__ == "__main__":
    main()
