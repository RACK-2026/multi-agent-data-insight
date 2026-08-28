"""
Agent-D: 高/低消耗分析Agent
分析视频消耗表现，识别高/低消耗视频特征
"""
import json

from app.agents.base_agent import BaseAgent


class ConsumptionAgent(BaseAgent):
    """高低消耗分析Agent"""

    def __init__(self):
        super().__init__("consumption_agent")

    async def run(self, data: dict) -> dict:
        """执行消耗分析"""
        llm_data = {
            "视频名称": data.get("视频名称", ""),
            "产品名称": data.get("产品名称", ""),
            "品牌": data.get("品牌", ""),
            "时长": data.get("时长", 0),
            "视频消耗": data.get("视频消耗", 0),
            "完播率": data.get("完播率", 0),
            "_2秒播放率": data.get("2秒播放率", 0),
            "整体点击率": data.get("整体点击率(%)", 0),
            "整体转化率": data.get("整体转化率(%)", 0),
            "整体支付ROI": data.get("整体支付ROI", 0),
            "千川自带脚本": data.get("千川自带脚本", ""),
        }

        result = await self.call_llm(llm_data, response_format={"type": "json_object"})

        try:
            parsed = json.loads(result)
        except json.JSONDecodeError:
            parsed = {"raw_output": result, "error": "JSON解析失败"}

        # 判断消耗级别
        cost = float(data.get("视频消耗", 0) or 0)
        consumption_level = "高消耗" if cost >= 500 else "低消耗"

        return {
            "agent": "consumption_agent",
            "consumption_level": consumption_level,
            "consumption_value": cost,
            "key_features": parsed.get("key_features", []),
            "completion_analysis": parsed.get("completion_analysis", ""),
            "conversion_analysis": parsed.get("conversion_analysis", ""),
            "comparison": parsed.get("comparison_to_average", ""),
            "suggestions": parsed.get("suggestions", []),
            "raw_llm_output": result,
        }

