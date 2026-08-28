"""
提示词优化Agent - 根据审核反馈优化提示词
"""
import json

from app.agents.base_agent import BaseAgent
from app.services.prompt_manager import prompt_manager


class PromptOptimizerAgent(BaseAgent):
    """提示词优化Agent"""

    def __init__(self):
        super().__init__("prompt_optimizer")

    async def run(self, data: dict) -> dict:
        """执行提示词优化"""
        agent_name = data.get("target_agent", "")
        current_prompt = data.get("current_prompt", {})
        review_feedback = data.get("review_feedback", "")
        optimization_notes = data.get("optimization_notes", "")

        if not agent_name:
            return {"error": "未指定目标Agent", "status": "failed"}

        current_version = current_prompt.get("version", "0.0.0")
        prompt_content = json.dumps(current_prompt, ensure_ascii=True)

        llm_data = {
            "agent_name": agent_name,
            "current_version": current_version,
            "current_prompt": prompt_content,
            "review_feedback": review_feedback,
            "optimization_notes": optimization_notes,
        }

        result = await self.call_llm(llm_data, response_format={"type": "json_object"})

        try:
            parsed = json.loads(result)
        except json.JSONDecodeError:
            return {"error": "优化结果JSON解析失败", "raw_llm_output": result}

        # 保存优化后的提示词
        try:
            prompt_manager.save_optimized_prompt(agent_name, parsed)
        except Exception as e:
            return {"error": f"保存提示词失败: {e}", "optimized": parsed}

        return {
            "agent": "prompt_optimizer",
            "target_agent": agent_name,
            "new_version": parsed.get("new_version", f"v{current_version}_optimized"),
            "changes": parsed.get("changes", []),
            "optimized_prompt": parsed.get("optimized_prompt", {}),
            "expected_improvement": parsed.get("expected_improvement", ""),
            "status": "optimized",
        }

