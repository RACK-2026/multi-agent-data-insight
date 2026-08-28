"""
Agent-C: 评分总结Agent
综合视频效果数据和内容分析结果，给出质量评分和总结
"""
import json

from app.agents.base_agent import BaseAgent


class ScoringAgent(BaseAgent):
    """评分总结Agent"""

    def __init__(self):
        super().__init__("scoring_agent")

    async def run(self, data: dict) -> dict:
        """执行综合评分"""
        # 收集内容分析的摘要
        content_analysis = data.get("content_analysis", {})
        if isinstance(content_analysis, dict):
            ai_summary = json.dumps({
                "script": content_analysis.get("script_analysis", {}),
                "hook": content_analysis.get("hook_analysis", {}),
                "summary": content_analysis.get("summary", ""),
            }, ensure_ascii=False)
        else:
            ai_summary = str(content_analysis)

        llm_data = {
            "视频名称": data.get("视频名称", ""),
            "产品名称": data.get("产品名称", ""),
            "品牌": data.get("品牌", ""),
            "时长": data.get("时长", 0),
            "视频消耗": data.get("视频消耗", 0),
            "完播率": data.get("完播率", 0),
            "_2秒播放率": data.get("2秒播放率", 0),
            "_3秒播放率": data.get("3秒播放率", 0),
            "整体点击率": data.get("整体点击率(%)", 0),
            "整体转化率": data.get("整体转化率(%)", 0),
            "整体支付ROI": data.get("整体支付ROI", 0),
            "千次展现费用": data.get("千次展现费用", 0),
            "ai_analysis_summary": ai_summary,
        }

        result = await self.call_llm(llm_data, response_format={"type": "json_object"})

        try:
            parsed = json.loads(result)
        except json.JSONDecodeError:
            parsed = {"raw_output": result, "error": "JSON解析失败"}

        return {
            "agent": "scoring_agent",
            "content_score": parsed.get("content_score", 0),
            "conversion_score": parsed.get("conversion_score", 0),
            "retention_score": parsed.get("retention_score", 0),
            "overall_score": parsed.get("overall_score", 0),
            "level": parsed.get("level", "未评估"),
            "strengths": parsed.get("strengths", []),
            "weaknesses": parsed.get("weaknesses", []),
            "optimization_suggestions": parsed.get("optimization_suggestions", []),
            "summary": parsed.get("summary", ""),
            "raw_llm_output": result,
        }

