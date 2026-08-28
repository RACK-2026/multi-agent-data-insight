"""
审核Agent - 审查各小Agent的输出质量
"""
import json

from app.agents.base_agent import BaseAgent
from app.config import settings


class ReviewAgent(BaseAgent):
    """质量审核Agent"""

    def __init__(self):
        super().__init__("review_agent")

    async def run(self, data: dict) -> dict:
        """执行审核"""
        agent_name = data.get("agent_name", "unknown")
        prompt_version = data.get("prompt_version", "0.0.0")
        agent_output = data.get("agent_output", "")
        data_summary = data.get("data_summary", "")

        llm_data = {
            "agent_name": agent_name,
            "prompt_version": prompt_version,
            "data_summary": data_summary,
            "agent_output": agent_output[:2000],  # 截断过长内容
            "threshold": settings.REVIEW_SCORE_THRESHOLD,
        }

        result = await self.call_llm(llm_data, response_format={"type": "json_object"})

        try:
            parsed = json.loads(result)
        except json.JSONDecodeError:
            parsed = {"overall_score": 0, "error": "JSON解析失败"}

        overall_score = parsed.get("overall_score", 0)
        should_optimize = parsed.get("should_optimize_prompt", False)

        # 低于阈值自动触发优化标记
        if overall_score < settings.REVIEW_SCORE_THRESHOLD:
            should_optimize = True

        return {
            "agent": "review_agent",
            "scores": {
                "consistency": parsed.get("consistency_score", 0),
                "value": parsed.get("value_score", 0),
                "completeness": parsed.get("completeness_score", 0),
                "clarity": parsed.get("clarity_score", 0),
                "overall": overall_score,
            },
            "strengths": parsed.get("strengths", []),
            "weaknesses": parsed.get("weaknesses", []),
            "improvement_suggestions": parsed.get("improvement_suggestions", []),
            "should_optimize_prompt": should_optimize,
            "optimization_reason": parsed.get("optimization_reason", ""),
            "raw_llm_output": result,
        }

