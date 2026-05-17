"""
DeepEval + DeepSeek 实战 - LLM-as-Judge
========================================
用 DeepSeek 做评判模型，测试AI系统输出的：
1. 正确性（GEval）
2. 幻觉检测（Hallucination）
3. 答案相关性（Answer Relevancy）

前置条件：
  export OPENAI_API_KEY='你的deepseek-key'
  export OPENAI_API_BASE_URL='https://api.deepseek.com'

运行：
  python3 test_deepseek_judge.py
"""

import os
import sys

# ============================================================
# 配置 DeepSeek 作为 Judge 模型
# ============================================================

# 验证环境变量
if not os.environ.get("OPENAI_API_KEY"):
    if "pytest" in sys.modules:
        import pytest

        pytest.skip("OPENAI_API_KEY is required for DeepSeek judge demos", allow_module_level=True)
    print("❌ 请先设置 OPENAI_API_KEY")
    print("   export OPENAI_API_KEY='你的deepseek-key'")
    sys.exit(1)

# DeepEval 通过环境变量 OPENAI_API_BASE_URL 自动识别自定义endpoint
# 所以不需要额外配置，直接用就行

from deepeval import assert_test
from deepeval.test_case import LLMTestCase
from deepeval.metrics import GEval, HallucinationMetric, AnswerRelevancyMetric


def run_test(name, test_case, metric, expect_pass=True):
    """运行单个测试并打印结果"""
    print(f"\n{'='*50}")
    print(f"测试: {name}")
    print(f"输入: {test_case.input}")
    print(f"实际输出: {test_case.actual_output[:80]}...")
    print(f"{'='*50}")
    
    try:
        metric.measure(test_case)
        score = metric.score
        reason = metric.reason
        
        passed = score >= metric.threshold
        status = "✅ 通过" if passed else "❌ 未通过"
        
        print(f"结果: {status}")
        print(f"得分: {score:.2f} (阈值: {metric.threshold})")
        print(f"原因: {reason}")
        
        if expect_pass and not passed:
            print("⚠️  预期通过但未通过")
        elif not expect_pass and passed:
            print("⚠️  预期失败但通过了（Judge可能不够严格）")
            
        return passed
        
    except Exception as e:
        print(f"❌ 运行出错: {e}")
        return False


def main():
    print("🚀 DeepEval + DeepSeek Judge 实战")
    print(f"API Base: {os.environ.get('OPENAI_API_BASE_URL', '默认OpenAI')}")
    print(f"Model: deepseek-chat")
    
    results = []
    
    # ----------------------------------------------------------
    # 场景1：正确性测试 - 应该通过
    # 模拟：客服机器人回答退货政策
    # ----------------------------------------------------------
    correctness_metric = GEval(
        name="Correctness",
        criteria="判断 actual_output 是否与 expected_output 语义一致，信息准确完整",
        evaluation_params=["actual_output", "expected_output"],
        threshold=0.5,
        model="deepseek-chat",  # 指定用 DeepSeek
    )
    
    test1 = LLMTestCase(
        input="你们的退货政策是什么？",
        actual_output="我们提供30天无理由退货，运费由我们承担，全额退款。",
        expected_output="客户享有30天全额退款政策，无需支付额外运费。",
    )
    results.append(("正确性-应通过", run_test("正确性测试（应通过）", test1, correctness_metric)))
    
    # ----------------------------------------------------------
    # 场景2：正确性测试 - 应该失败
    # 模拟：客服机器人给了错误的退货天数
    # ----------------------------------------------------------
    correctness_metric2 = GEval(
        name="Correctness",
        criteria="判断 actual_output 是否与 expected_output 语义一致，信息准确完整",
        evaluation_params=["actual_output", "expected_output"],
        threshold=0.5,
        model="deepseek-chat",
    )
    
    test2 = LLMTestCase(
        input="你们的退货政策是什么？",
        actual_output="我们提供7天退货，但运费需要客户自己承担。",  # 故意写错
        expected_output="客户享有30天全额退款政策，无需支付额外运费。",
    )
    results.append(("正确性-应失败", run_test("正确性测试（应失败）", test2, correctness_metric2, expect_pass=False)))
    
    # ----------------------------------------------------------
    # 场景3：幻觉检测 - 无幻觉（应通过）
    # 所有输出内容都有context支撑
    # ----------------------------------------------------------
    hallucination_metric = HallucinationMetric(
        threshold=0.5,
        model="deepseek-chat",
    )
    
    test3 = LLMTestCase(
        input="介绍一下你们公司的创始人",
        actual_output="我们公司由张三于2015年在上海创立，专注于跨境电商技术服务。",
        context=[
            "公司成立于2015年，总部位于上海。",
            "公司主营业务为跨境电商技术解决方案。",
            "创始人为张三，毕业于复旦大学计算机系。",
        ],
    )
    results.append(("幻觉检测-无幻觉", run_test("幻觉检测（无幻觉，应通过）", test3, hallucination_metric)))
    
    # ----------------------------------------------------------
    # 场景4：幻觉检测 - 有幻觉（应失败）
    # LLM编造了"红杉资本融资"信息
    # ----------------------------------------------------------
    hallucination_metric2 = HallucinationMetric(
        threshold=0.5,
        model="deepseek-chat",
    )
    
    test4 = LLMTestCase(
        input="介绍一下你们公司的创始人",
        actual_output="我们公司由张三于2015年在上海创立，已获得红杉资本A轮融资5000万美元，目前估值超过10亿。",
        context=[
            "公司成立于2015年，总部位于上海。",
            "公司主营业务为跨境电商技术解决方案。",
            "创始人为张三，毕业于复旦大学计算机系。",
        ],
    )
    results.append(("幻觉检测-有幻觉", run_test("幻觉检测（有幻觉，应失败）", test4, hallucination_metric2, expect_pass=False)))
    
    # ----------------------------------------------------------
    # 场景5：答案相关性 - 切题（应通过）
    # ----------------------------------------------------------
    relevancy_metric = AnswerRelevancyMetric(
        threshold=0.5,
        model="deepseek-chat",
    )
    
    test5 = LLMTestCase(
        input="Python中怎么读取CSV文件？",
        actual_output="你可以使用pandas库：import pandas as pd; df = pd.read_csv('data.csv')。也可以用内置的csv模块。",
    )
    results.append(("相关性-切题", run_test("答案相关性（切题，应通过）", test5, relevancy_metric)))
    
    # ----------------------------------------------------------
    # 场景6：答案相关性 - 跑题（应失败）
    # ----------------------------------------------------------
    relevancy_metric2 = AnswerRelevancyMetric(
        threshold=0.5,
        model="deepseek-chat",
    )
    
    test6 = LLMTestCase(
        input="Python中怎么读取CSV文件？",
        actual_output="Python是由Guido van Rossum在1991年发明的编程语言，名字来源于Monty Python喜剧团。",  # 完全跑题
    )
    results.append(("相关性-跑题", run_test("答案相关性（跑题，应失败）", test6, relevancy_metric2, expect_pass=False)))
    
    # ----------------------------------------------------------
    # 汇总结果
    # ----------------------------------------------------------
    print("\n" + "=" * 50)
    print("📊 测试汇总")
    print("=" * 50)
    
    for name, passed in results:
        status = "✅" if passed else "❌"
        print(f"  {status} {name}")
    
    total = len(results)
    passed_count = sum(1 for _, p in results if p)
    print(f"\n总计: {passed_count}/{total} 通过")
    
    print("\n💡 关键收获:")
    print("  - GEval: 用LLM做语义级别的正确性判断，不是简单字符串匹配")
    print("  - HallucinationMetric: 对比output和context，检测编造内容")
    print("  - AnswerRelevancyMetric: 判断回答是否切题")
    print("  - 这些就是AI测试和传统测试的核心区别")


if __name__ == "__main__":
    main()
