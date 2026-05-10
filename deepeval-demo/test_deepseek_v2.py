"""
DeepEval + DeepSeek 实战 v2
===========================
用自定义模型类确保所有请求都走DeepSeek API

运行：
  export OPENAI_API_KEY='你的deepseek-key'
  python3 test_deepseek_v2.py
"""

import os
import sys

if not os.environ.get("OPENAI_API_KEY"):
    print("❌ 请先 export OPENAI_API_KEY='你的deepseek-key'")
    sys.exit(1)

from openai import OpenAI
from deepeval.models import DeepEvalBaseLLM
from deepeval.test_case import LLMTestCase
from deepeval.metrics import GEval, HallucinationMetric, AnswerRelevancyMetric


# ============================================================
# 自定义 DeepSeek 模型类
# 这样所有metric都会通过这个类调用DeepSeek
# ============================================================

class DeepSeekModel(DeepEvalBaseLLM):
    def __init__(self):
        self.client = OpenAI(
            api_key=os.environ["OPENAI_API_KEY"],
            base_url="https://api.deepseek.com",
        )
        self.model_name = "deepseek-chat"
    
    def load_model(self):
        return self.client
    
    def generate(self, prompt: str, schema=None) -> str:
        """同步生成"""
        try:
            if schema:
                # DeepEval可能传入schema要求结构化输出
                # 在prompt里加上JSON格式要求
                import json
                prompt = prompt + f"\n\nRespond ONLY with valid JSON matching this schema: {json.dumps(schema.model_json_schema())}"
                
                response = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0,
                    max_tokens=2000,
                )
                content = response.choices[0].message.content.strip()
                # 清理可能的markdown代码块
                if content.startswith("```"):
                    content = content.split("\n", 1)[1] if "\n" in content else content
                    content = content.rsplit("```", 1)[0] if "```" in content else content
                    content = content.strip()
                
                return schema.model_validate_json(content)
            else:
                response = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0,
                    max_tokens=2000,
                )
                return response.choices[0].message.content
        except Exception as e:
            print(f"  ⚠️ API调用异常: {e}")
            raise
    
    async def a_generate(self, prompt: str, schema=None) -> str:
        """异步生成（DeepEval内部可能调用异步版本）"""
        return self.generate(prompt, schema=schema)
    
    def get_model_name(self) -> str:
        return self.model_name


def run_test(name, test_case, metric, expect_pass=True):
    """运行单个测试"""
    print(f"\n{'─'*50}")
    print(f"📋 {name}")
    print(f"   输入: {test_case.input}")
    print(f"   输出: {test_case.actual_output[:60]}...")
    
    try:
        metric.measure(test_case)
        score = metric.score
        reason = metric.reason
        
        passed = score >= metric.threshold
        
        if expect_pass:
            icon = "✅" if passed else "⚠️"
        else:
            icon = "✅" if not passed else "⚠️"
            
        print(f"   {icon} 得分: {score:.2f} (阈值: {metric.threshold})")
        print(f"   📝 Judge说: {reason[:120] if reason else '无'}...")
        
        return True  # 测试运行成功（不管pass/fail）
        
    except Exception as e:
        print(f"   ❌ 出错: {str(e)[:150]}")
        return False


def main():
    print("🚀 DeepEval + DeepSeek Judge 实战 v2")
    print("=" * 50)
    
    # 初始化自定义模型
    ds_model = DeepSeekModel()
    
    # 先测试API连通性
    print("\n🔌 测试DeepSeek API连通性...")
    try:
        result = ds_model.generate("回复OK两个字母")
        print(f"   ✅ API连通: {result.strip()}")
    except Exception as e:
        print(f"   ❌ API不通: {e}")
        print("   请检查OPENAI_API_KEY是否正确")
        sys.exit(1)
    
    success_count = 0
    total = 0
    
    # ----------------------------------------------------------
    # 场景1：正确性 - 语义一致（应通过）
    # ----------------------------------------------------------
    total += 1
    metric1 = GEval(
        name="Correctness",
        criteria="判断actual_output是否与expected_output语义一致，关键信息（天数、费用、政策）是否匹配",
        evaluation_params=["actual_output", "expected_output"],
        threshold=0.5,
        model=ds_model,
    )
    test1 = LLMTestCase(
        input="你们的退货政策是什么？",
        actual_output="我们提供30天无理由退货，运费由我们承担，全额退款。",
        expected_output="客户享有30天全额退款政策，无需支付额外运费。",
    )
    if run_test("正确性测试 - 语义一致（期望通过）", test1, metric1, expect_pass=True):
        success_count += 1
    
    # ----------------------------------------------------------
    # 场景2：正确性 - 信息错误（应失败）
    # ----------------------------------------------------------
    total += 1
    metric2 = GEval(
        name="Correctness",
        criteria="判断actual_output是否与expected_output语义一致，关键信息（天数、费用、政策）是否匹配",
        evaluation_params=["actual_output", "expected_output"],
        threshold=0.5,
        model=ds_model,
    )
    test2 = LLMTestCase(
        input="你们的退货政策是什么？",
        actual_output="我们提供7天退货，运费需要客户自己承担。",
        expected_output="客户享有30天全额退款政策，无需支付额外运费。",
    )
    if run_test("正确性测试 - 信息错误（期望失败）", test2, metric2, expect_pass=False):
        success_count += 1
    
    # ----------------------------------------------------------
    # 场景3：幻觉检测 - 无幻觉（应通过）
    # ----------------------------------------------------------
    total += 1
    metric3 = HallucinationMetric(
        threshold=0.5,
        model=ds_model,
    )
    test3 = LLMTestCase(
        input="介绍一下你们公司",
        actual_output="公司2015年在上海成立，做跨境电商技术服务。",
        context=[
            "公司成立于2015年，总部位于上海。",
            "公司主营业务为跨境电商技术解决方案。",
        ],
    )
    if run_test("幻觉检测 - 无幻觉（期望通过）", test3, metric3, expect_pass=True):
        success_count += 1
    
    # ----------------------------------------------------------
    # 场景4：幻觉检测 - 有幻觉（应失败）
    # ----------------------------------------------------------
    total += 1
    metric4 = HallucinationMetric(
        threshold=0.5,
        model=ds_model,
    )
    test4 = LLMTestCase(
        input="介绍一下你们公司",
        actual_output="公司2015年在上海成立，已获红杉资本5000万美元融资，估值超10亿。",
        context=[
            "公司成立于2015年，总部位于上海。",
            "公司主营业务为跨境电商技术解决方案。",
        ],
    )
    if run_test("幻觉检测 - 有幻觉（期望失败）", test4, metric4, expect_pass=False):
        success_count += 1
    
    # ----------------------------------------------------------
    # 场景5：答案相关性 - 切题（应通过）
    # ----------------------------------------------------------
    total += 1
    metric5 = AnswerRelevancyMetric(
        threshold=0.5,
        model=ds_model,
    )
    test5 = LLMTestCase(
        input="Python中怎么读取CSV文件？",
        actual_output="可以用pandas的read_csv函数，示例：import pandas as pd; df = pd.read_csv('data.csv')",
    )
    if run_test("答案相关性 - 切题（期望通过）", test5, metric5, expect_pass=True):
        success_count += 1
    
    # ----------------------------------------------------------
    # 场景6：答案相关性 - 跑题（应失败）
    # ----------------------------------------------------------
    total += 1
    metric6 = AnswerRelevancyMetric(
        threshold=0.5,
        model=ds_model,
    )
    test6 = LLMTestCase(
        input="Python中怎么读取CSV文件？",
        actual_output="Python是Guido van Rossum在1991年发明的语言，名字来自Monty Python喜剧团。",
    )
    if run_test("答案相关性 - 跑题（期望失败）", test6, metric6, expect_pass=False):
        success_count += 1
    
    # ----------------------------------------------------------
    # 汇总
    # ----------------------------------------------------------
    print("\n" + "=" * 50)
    print(f"📊 运行完成: {success_count}/{total} 个测试成功执行")
    print("=" * 50)
    
    print("\n💡 你刚刚体验了AI测试的三大核心能力:")
    print("   1. GEval — 用LLM做语义级正确性判断")
    print("   2. HallucinationMetric — 对比context检测编造内容")
    print("   3. AnswerRelevancyMetric — 判断回答是否切题")
    print("\n   传统测试: assertEqual('30天', response)")
    print("   AI测试:   '30天无理由退货' ≈ '30天全额退款' ✅")
    print("   这就是本质区别。")


if __name__ == "__main__":
    main()
