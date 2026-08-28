"""
Agent-A: 视频内容结构分析Agent
分析：脚本类型、内容结构、前5秒留存、卖点、转化引导
"""
from app.agents.base_agent import BaseAgent


class ContentAnalyzerAgent(BaseAgent):
    """内容分析Agent"""

    def __init__(self):
        super().__init__("content_analyzer")

    async def run(self, data: dict) -> dict:
        """执行内容分析"""
        # 准备LLM输入数据
        llm_data = {
            "视频名称": data.get("视频名称", ""),
            "产品名称": data.get("产品名称", ""),
            "品牌": data.get("品牌", ""),
            "时长": data.get("时长", 0),
            "千川自带脚本": data.get("千川自带脚本", ""),
            "视频消耗": data.get("视频消耗", 0),
            "完播率": data.get("完播率", 0),
            "_2秒播放率": data.get("2秒播放率", 0),
            "_3秒播放率": data.get("3秒播放率", 0),
            "_5秒播放率": data.get("5秒播放率", 0),
            "_10秒播放率": data.get("10秒播放率", 0),
        }

        result = await self.call_llm(llm_data, response_format={"type": "json_object"})

        # 解析结果
        import json
        try:
            parsed = json.loads(result)
        except json.JSONDecodeError:
            parsed = {"raw_output": result, "error": "JSON解析失败"}

        return {
            "agent": "content_analyzer",
            "script_analysis": parsed.get("script_type", {}),
            "hook_analysis": parsed.get("hook_analysis", {}),
            "selling_point_analysis": parsed.get("selling_point", {}),
            "conversion_analysis": parsed.get("conversion", {}),
            "visual_analysis": parsed.get("visual_appeal", {}),
            "summary": parsed.get("summary", ""),
            "tags": (
                parsed.get("script_type", {}).get("tags", []) +
                parsed.get("hook_analysis", {}).get("tags", []) +
                parsed.get("selling_point", {}).get("tags", [])
            ),
            "raw_llm_output": result,
        }

