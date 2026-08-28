"""
Agent-B: 创意拆解Agent
分析：创意元素拆解、卖点点击顺序、脚本结构转化、转化理由
"""
import json

from app.agents.base_agent import BaseAgent


class CreativeAnalyzerAgent(BaseAgent):
    """创意拆解Agent"""

    def __init__(self):
        super().__init__("creative_analyzer")

    async def run(self, data: dict) -> dict:
        """执行创意拆解"""
        llm_data = {
            "视频名称": data.get("视频名称", ""),
            "产品名称": data.get("产品名称", ""),
            "品牌": data.get("品牌", ""),
            "千川自带脚本": data.get("千川自带脚本", ""),
            "千川创意元素拆解": data.get("千川创意元素拆解", ""),
        }

        result = await self.call_llm(llm_data, response_format={"type": "json_object"})

        try:
            parsed = json.loads(result)
        except json.JSONDecodeError:
            parsed = {"raw_output": result, "error": "JSON解析失败"}

        return {
            "agent": "creative_analyzer",
            "element_breakdown": parsed.get("element_breakdown", parsed),
            "selling_point_order": parsed.get("selling_point_order", ""),
            "script_conversion": parsed.get("script_conversion", ""),
            "conversion_reason": parsed.get("conversion_reason", ""),
            "raw_llm_output": result,
        }

