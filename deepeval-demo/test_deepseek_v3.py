"""
DeepEval + DeepSeek 实战 v3 (修复版)
====================================
GEval在DeepSeek上有兼容性bug，用自定义正确性评估替代

运行：
  export OPENAI_API_KEY='你的deepseek-key'
  python3 test_deepseek_v3.py
"""

import os
import sys
import json

if not os.environ.get("OPENAI_API_KEY"):
    print("❌ 请先 export OPENAI_API_KEY='你的deepseek-key'")
    sys.exit(1)

from openai import OpenAI
from deepeval.models import DeepEvalBaseLLM
from deepeval.test_case import LLMTestCase
from deepeval.metrics import HallucinationMetric, AnswerRelevancyMetric


# ============================================================
# DeepSeek 模型
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
        try:
            if schema:
                import json as j
                prompt = prompt + f"\n\nRespond ONLY with valid JSON matching this schema: {j.dumps(schema.model_json_schema())}"
                response = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0,
                    max_tokens=2000,
                )
                content = response.choices[0].message.content.strip()
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
        return self.generate(prompt, schema=schema)
    
    def get_model_name(self) -> str:
        return self.model_name


# ============================================================
# 自定义正确性评估（替代有bug的GEval）
# 本质就是手写一个LLM-as-Judge的prompt
# 这也是实际工作中最常用的方式
# ============================================================

def eval_correctness(client, actual_output, expected_output, input_text):
    """
    手动实现LLM-as-Judge正确性评估
    实际工作中你经常需要自定义评估逻辑，不能完全依赖框架
    """
    prompt = f"""你是一个严格的AI输出质量评估专家。

用户问题: {input_text}
AI实际输出: {actual_output}
标准答案: {expected_output}

请评估AI实际输出与标准答案是否语义一致，关键信息是否匹配。

请严格用以下JSON格式回复，不要包含其他内容:
{{"score": 0.0到1.0之间的数字, "reason": "评估理由"}}

评分标准:
- 1.0: 完全一致，关键信息全部匹配
- 0.7-0.9: 大体一致，细节略有不同但不影响理解
- 0.4-0.6: 部分一致，有重要信息缺失或不同
- 0.0-0.3: 严重不一致，关键信息错误"""

    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
        max_tokens=500,
    )
    
    content = response.choices[0].message.content.strip()
    # 清理markdown代码块
    if content.startswith("```"):
        content = content.split("\n", 1)[1] if "\n" in content else content
        content = content.rsplit("```", 1)[0] if "```" in content else content
        content = content.strip()
    
    result = json.loads(content)
    return result["score"], result["reason"]


def main():
    print("🚀 DeepEval + DeepSeek Judge 实战 v3")
    print("=" * 55)
    
    ds_model = DeepSeekModel()
    client = ds_model.client
    
    # 测试连通性
    print("\n🔌 测试API连通性...")
    try:
        result = ds_model.generate("回复OK")
        print(f"   ✅ 连通成功")
    except Exception as e:
        print(f"   ❌ 连不上: {e}")
        sys.exit(1)
    
    print("\n")
    
    # ==========================================================
    # 场景1：正确性 - 语义一致（应通过）
    # ==========================================================
    print("─" * 55)
    print("📋 场景1: 正确性测试 - 语义一致（期望高分）")
    print("   输入: 你们的退货政策是什么？")
    print("   输出: 我们提供30天无理由退货，运费由我们承担，全额退款。")
    print("   期望: 客户享有30天全额退款政策，无需支付额外运费。")
    
    score, reason = eval_correctness(
        client,
        actual_output="我们提供30天无理由退货，运费由我们承担，全额退款。",
        expected_output="客户享有30天全额退款政策，无需支付额外运费。",
        input_text="你们的退货政策是什么？",
    )
    icon = "✅" if score >= 0.5 else "❌"
    print(f"   {icon} 得分: {score}")
    print(f"   📝 Judge说: {reason}")
    
    # ==========================================================
    # 场景2：正确性 - 信息错误（应失败）
    # ==========================================================
    print("\n" + "─" * 55)
    print("📋 场景2: 正确性测试 - 信息错误（期望低分）")
    print("   输入: 你们的退货政策是什么？")
    print("   输出: 我们提供7天退货，运费需要客户自己承担。")
    print("   期望: 客户享有30天全额退款政策，无需支付额外运费。")
    
    score2, reason2 = eval_correctness(
        client,
        actual_output="我们提供7天退货，运费需要客户自己承担。",
        expected_output="客户享有30天全额退款政策，无需支付额外运费。",
        input_text="你们的退货政策是什么？",
    )
    icon2 = "✅" if score2 < 0.5 else "⚠️"
    print(f"   {icon2} 得分: {score2}")
    print(f"   📝 Judge说: {reason2}")
    
    # ==========================================================
    # 场景3：幻觉检测 - 无幻觉（应通过）
    # ==========================================================
    print("\n" + "─" * 55)
    print("📋 场景3: 幻觉检测 - 无幻觉（期望通过）")
    
    metric3 = HallucinationMetric(threshold=0.5, model=ds_model)
    test3 = LLMTestCase(
        input="介绍一下你们公司",
        actual_output="公司2015年在上海成立，做跨境电商技术服务。",
        context=[
            "公司成立于2015年，总部位于上海。",
            "公司主营业务为跨境电商技术解决方案。",
        ],
    )
    try:
        metric3.measure(test3)
        # HallucinationMetric: 分数越低越好（0=无幻觉）
        icon3 = "✅" if metric3.score <= 0.5 else "⚠️"
        print(f"   输出: {test3.actual_output}")
        print(f"   {icon3} 幻觉分: {metric3.score:.2f} (越低越好, 阈值0.5)")
        print(f"   📝 Judge说: {metric3.reason[:120]}...")
    except Exception as e:
        print(f"   ❌ 出错: {e}")
    
    # ==========================================================
    # 场景4：幻觉检测 - 有幻觉（应检测出）
    # ==========================================================
    print("\n" + "─" * 55)
    print("📋 场景4: 幻觉检测 - 有幻觉（期望检测出）")
    
    metric4 = HallucinationMetric(threshold=0.5, model=ds_model)
    test4 = LLMTestCase(
        input="介绍一下你们公司",
        actual_output="公司2015年在上海成立，已获红杉资本5000万美元融资，估值超10亿。",
        context=[
            "公司成立于2015年，总部位于上海。",
            "公司主营业务为跨境电商技术解决方案。",
        ],
    )
    try:
        metric4.measure(test4)
        icon4 = "✅" if metric4.score > 0.3 else "⚠️"
        print(f"   输出: {test4.actual_output}")
        print(f"   {icon4} 幻觉分: {metric4.score:.2f} (编造内容应得高分)")
        print(f"   📝 Judge说: {metric4.reason[:120]}...")
    except Exception as e:
        print(f"   ❌ 出错: {e}")
    
    # ==========================================================
    # 场景5：答案相关性 - 切题
    # ==========================================================
    print("\n" + "─" * 55)
    print("📋 场景5: 答案相关性 - 切题（期望高分）")
    
    metric5 = AnswerRelevancyMetric(threshold=0.5, model=ds_model)
    test5 = LLMTestCase(
        input="Python中怎么读取CSV文件？",
        actual_output="可以用pandas的read_csv函数：import pandas as pd; df = pd.read_csv('data.csv')",
    )
    try:
        metric5.measure(test5)
        icon5 = "✅" if metric5.score >= 0.5 else "⚠️"
        print(f"   {icon5} 相关性: {metric5.score:.2f}")
        print(f"   📝 Judge说: {metric5.reason[:120]}...")
    except Exception as e:
        print(f"   ❌ 出错: {e}")
    
    # ==========================================================
    # 场景6：答案相关性 - 跑题
    # ==========================================================
    print("\n" + "─" * 55)
    print("📋 场景6: 答案相关性 - 跑题（期望低分）")
    
    metric6 = AnswerRelevancyMetric(threshold=0.5, model=ds_model)
    test6 = LLMTestCase(
        input="Python中怎么读取CSV文件？",
        actual_output="Python是Guido van Rossum在1991年发明的，名字来自Monty Python喜剧团。",
    )
    try:
        metric6.measure(test6)
        icon6 = "✅" if metric6.score < 0.5 else "⚠️"
        print(f"   {icon6} 相关性: {metric6.score:.2f}")
        print(f"   📝 Judge说: {metric6.reason[:120]}...")
    except Exception as e:
        print(f"   ❌ 出错: {e}")
    
    # ==========================================================
    # 汇总
    # ==========================================================
    print("\n" + "=" * 55)
    print("📊 6个场景全部执行完毕")
    print("=" * 55)
    print()
    print("💡 关键收获:")
    print("   场景1-2: 自定义LLM-as-Judge（实际工作中最常用）")
    print("          → 框架有bug？自己写prompt照样能评估")
    print("          → 这也是AI测试工程师的核心技能")
    print()
    print("   场景3-4: 幻觉检测")
    print("          → 对比context和output，找出编造内容")
    print("          → 传统测试完全没有的概念")
    print()
    print("   场景5-6: 答案相关性")
    print("          → 不管对不对，先看有没有跑题")
    print("          → 大模型经常答非所问，这个指标很实用")


if __name__ == "__main__":
    main()
