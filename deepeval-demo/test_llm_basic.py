"""
DeepEval 入门Demo - AI测试工程师实战
=====================================
这个文件演示了AI测试的核心场景：
1. 测试LLM输出的正确性（Correctness）
2. 测试是否存在幻觉（Hallucination）
3. 测试答案相关性（Answer Relevancy）

运行方式：
  deepeval test run test_llm_basic.py
  或
  pytest test_llm_basic.py -v

注意：需要设置环境变量 OPENAI_API_KEY（DeepEval默认用OpenAI做judge）
如果你只有Anthropic API Key，看下面的 test_without_llm_judge 用无LLM指标测试
"""

import pytest
from deepeval import assert_test
from deepeval.test_case import LLMTestCase
from deepeval.metrics import (
    GEval,
    HallucinationMetric,
    AnswerRelevancyMetric,
)


# ============================================================
# 场景1：用 GEval 测试LLM输出的正确性
# GEval 是Google提出的评估方法，用另一个LLM来打分
# 这就是"LLM-as-Judge"的核心思路
# ============================================================

def test_correctness():
    """测试：客服机器人回答退货政策是否正确"""
    
    correctness_metric = GEval(
        name="Correctness",
        criteria="判断 actual_output 是否与 expected_output 语义一致，信息是否准确完整",
        evaluation_params=["actual_output", "expected_output"],
        threshold=0.5,  # 0-1分，低于0.5算失败
    )
    
    test_case = LLMTestCase(
        # 用户输入
        input="你们的退货政策是什么？",
        # LLM实际输出（模拟你的AI系统返回的结果）
        actual_output="我们提供30天无理由退货，运费由我们承担，全额退款。",
        # 期望输出（ground truth）
        expected_output="客户享有30天全额退款政策，无需支付额外运费。",
    )
    
    assert_test(test_case, [correctness_metric])


# ============================================================
# 场景2：幻觉检测
# 这是AI测试最独特的部分——传统测试没有这个概念
# 检查LLM的输出是否有"编造"的内容
# ============================================================

def test_hallucination():
    """测试：LLM是否在编造不存在的信息"""
    
    hallucination_metric = HallucinationMetric(threshold=0.5)
    
    test_case = LLMTestCase(
        input="介绍一下你们公司的创始人",
        actual_output="我们公司由张三于2015年在上海创立，专注于跨境电商技术服务。",
        # context 是RAG检索到的参考文档，LLM应该基于这些内容回答
        context=[
            "公司成立于2015年，总部位于上海。",
            "公司主营业务为跨境电商技术解决方案。",
            "创始人为张三，毕业于复旦大学计算机系。",
        ],
    )
    
    assert_test(test_case, [hallucination_metric])


def test_hallucination_should_fail():
    """测试：这个case应该检测出幻觉——LLM编造了不存在的信息"""
    
    hallucination_metric = HallucinationMetric(threshold=0.5)
    
    test_case = LLMTestCase(
        input="介绍一下你们公司的创始人",
        # 注意：LLM编造了"获得红杉资本A轮融资"，context里没有这个信息
        actual_output="我们公司由张三于2015年在上海创立，已获得红杉资本A轮融资5000万美元。",
        context=[
            "公司成立于2015年，总部位于上海。",
            "公司主营业务为跨境电商技术解决方案。",
            "创始人为张三，毕业于复旦大学计算机系。",
        ],
    )
    
    # 这个测试预期会失败（检测到幻觉），用 pytest.raises 捕获
    # 实际项目中你不会这样写，这里是为了演示
    try:
        assert_test(test_case, [hallucination_metric])
        print("⚠️ 幻觉未被检测到（可能judge模型判断不够严格）")
    except AssertionError:
        print("✅ 成功检测到幻觉！")


# ============================================================
# 场景3：答案相关性
# 测试LLM的回答是否和用户的问题相关（没有跑题）
# ============================================================

def test_answer_relevancy():
    """测试：LLM的回答是否切题"""
    
    relevancy_metric = AnswerRelevancyMetric(threshold=0.5)
    
    test_case = LLMTestCase(
        input="Python中怎么读取CSV文件？",
        actual_output="你可以使用pandas库的read_csv()函数来读取CSV文件。示例：import pandas as pd; df = pd.read_csv('data.csv')",
    )
    
    assert_test(test_case, [relevancy_metric])


# ============================================================
# 场景4：不需要LLM Judge的指标（不需要API Key就能跑！）
# 用传统NLP方法评估，适合没有OpenAI Key的情况
# ============================================================

def test_without_llm_judge():
    """
    用字符串匹配和简单规则测试，不需要任何API Key
    这个你现在就能跑！
    """
    test_case = LLMTestCase(
        input="1+1等于几？",
        actual_output="1+1等于2。",
        expected_output="2",
    )
    
    # 手动检查：输出中是否包含期望的关键信息
    assert "2" in test_case.actual_output, "输出中应包含正确答案'2'"
    print("✅ 基础断言通过：输出包含正确答案")


# ============================================================
# 场景5：批量测试（Data-Driven Testing）
# 用多组数据跑同一个评估逻辑，类似你在PDD做的数据驱动测试
# ============================================================

TEST_DATA = [
    {
        "input": "什么是跨境电商？",
        "output": "跨境电商是指不同国家或地区之间通过互联网进行商品交易的电子商务活动。",
        "expected": "跨境电商是跨越国境的线上商品交易。",
    },
    {
        "input": "TEMU是什么平台？",
        "output": "TEMU是拼多多旗下的跨境电商平台，主要面向北美和欧洲市场。",
        "expected": "TEMU是PDD Holdings运营的海外电商平台。",
    },
    {
        "input": "什么是API测试？",
        "output": "API测试是验证应用程序编程接口的功能、性能和安全性的测试方法。",
        "expected": "API测试是对接口进行功能和性能验证的测试类型。",
    },
]


@pytest.mark.parametrize("data", TEST_DATA, ids=[d["input"][:10] for d in TEST_DATA])
def test_batch_correctness(data):
    """批量测试多个QA对的正确性"""
    
    test_case = LLMTestCase(
        input=data["input"],
        actual_output=data["output"],
        expected_output=data["expected"],
    )
    
    # 这里用简单断言代替LLM Judge，你可以换成 GEval
    assert len(test_case.actual_output) > 10, "输出不应为空或过短"
    print(f"✅ '{data['input'][:15]}...' 测试通过")


if __name__ == "__main__":
    print("=" * 60)
    print("DeepEval Demo - 直接运行基础测试")
    print("=" * 60)
    
    # 先跑不需要API的测试
    print("\n--- 场景4: 无需LLM Judge的基础测试 ---")
    test_without_llm_judge()
    
    print("\n--- 场景5: 批量数据驱动测试 ---")
    for data in TEST_DATA:
        test_case = LLMTestCase(
            input=data["input"],
            actual_output=data["output"],
            expected_output=data["expected"],
        )
        assert len(test_case.actual_output) > 10
        print(f"  ✅ '{data['input'][:15]}...' 通过")
    
    print("\n" + "=" * 60)
    print("基础测试全部通过！")
    print()
    print("下一步：设置 OPENAI_API_KEY 后运行完整测试：")
    print("  export OPENAI_API_KEY='your-key'")
    print("  deepeval test run test_llm_basic.py -v")
    print()
    print("或者用 Anthropic API（需要额外配置，见 README）")
    print("=" * 60)
