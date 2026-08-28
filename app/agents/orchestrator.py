"""
调度主Agent（Orchestrator）- 负责任务编排、子Agent调度、结果汇总、闭环触发
"""
import json
from typing import Optional

from app.agents.base_agent import BaseAgent
from app.agents.content_analyzer import ContentAnalyzerAgent
from app.agents.creative_analyzer import CreativeAnalyzerAgent
from app.agents.scoring_agent import ScoringAgent
from app.agents.consumption_agent import ConsumptionAgent
from app.agents.review_agent import ReviewAgent
from app.agents.prompt_optimizer import PromptOptimizerAgent
from app.services.prompt_manager import prompt_manager


class OrchestratorAgent(BaseAgent):
    """调度主Agent - 编排所有子Agent的协作"""

    def __init__(self):
        super().__init__("orchestrator")
        # 初始化子Agent
        self.agents = {
            "content_analyzer": ContentAnalyzerAgent(),
            "creative_analyzer": CreativeAnalyzerAgent(),
            "scoring_agent": ScoringAgent(),
            "consumption_agent": ConsumptionAgent(),
            "review_agent": ReviewAgent(),
            "prompt_optimizer": PromptOptimizerAgent(),
        }

    async def run(self, data: dict) -> dict:
        """执行任务调度（基类要求，实际用下面的具体方法）"""
        task_type = data.get("task_type", "analyze")
        if task_type == "analyze":
            return await self.analyze_video(data)
        elif task_type == "full_analysis":
            return await self.full_analysis(data)
        elif task_type == "review_cycle":
            return await self.review_and_optimize(data)
        return {"error": f"未知任务类型: {task_type}"}

    async def analyze_video(self, video_data: dict) -> dict:
        """
        单条视频串行分析流程
        Agent-A(内容分析) → Agent-B(创意拆解) → Agent-C(评分总结) → Agent-D(消耗分析)
        """
        record_id = video_data.get("record_id", "")

        # 步骤1: 内容分析 (Agent-A)
        content_agent = self.agents["content_analyzer"]
        content_result = await content_agent.safe_run(video_data, record_id)

        if "error" in content_result:
            # Agent-A失败，跳过后续依赖Agent
            return {"status": "partial", "error": "内容分析失败", "content_result": content_result}

        # 步骤2: 创意拆解 (Agent-B)
        creative_agent = self.agents["creative_analyzer"]
        creative_data = {**video_data, "content_analysis": content_result}
        creative_result = await creative_agent.safe_run(creative_data, record_id)

        # 步骤3: 评分总结 (Agent-C)- 需要Agent-A的结果
        scoring_agent = self.agents["scoring_agent"]
        scoring_data = {**video_data, "content_analysis": content_result}
        scoring_result = await scoring_agent.safe_run(scoring_data, record_id)

        # 步骤4: 高低消耗分析 (Agent-D)
        consumption_agent = self.agents["consumption_agent"]
        consumption_result = await consumption_agent.safe_run(video_data, record_id)

        # 汇总
        summary = self._build_summary(video_data, content_result, creative_result, scoring_result, consumption_result)

        return {
            "status": "success",
            "record_id": record_id,
            "video_name": video_data.get("视频名称", ""),
            "content_analysis": content_result,
            "creative_analysis": creative_result,
            "scoring": scoring_result,
            "consumption_analysis": consumption_result,
            "summary": summary,
        }

    async def full_analysis(self, data: dict) -> dict:
        """
        批量分析 + 审核 + 优化闭环
        """
        records = data.get("records", [])
        results = []

        for record in records:
            result = await self.analyze_video(record)
            results.append(result)

        # 抽样审核（取最新3条或全部）
        sample_size = min(3, len(results))
        review_results = []
        for i in range(sample_size):
            r = results[i]
            if r.get("status") != "success":
                continue

            # 审核各Agent的输出
            for agent_name in ["content_analyzer", "scoring_agent", "consumption_agent"]:
                agent_output = r.get(f"{agent_name.replace('_', '_')}_analysis", r.get(agent_name))
                if not agent_output:
                    agent_output = r.get("content_analysis") if agent_name == "content_analyzer" \
                        else r.get("scoring") if agent_name == "scoring_agent" \
                        else r.get("consumption_analysis")

                if not agent_output or "error" in str(agent_output):
                    continue

                review_result = await self.review_agent_output(
                    agent_name=agent_name,
                    agent_output=agent_output,
                    data_summary=f"视频: {record.get('视频名称', '')}",
                )
                review_results.append(review_result)

        # 判断是否需要优化
        need_optimize = any(
            r.get("should_optimize_prompt", False)
            for r in review_results
        )

        optimization_result = None
        if need_optimize:
            optimization_result = await self.auto_optimize(review_results)

        return {
            "status": "success",
            "total_analyzed": len(results),
            "results": results,
            "reviews": review_results,
            "optimization": optimization_result,
            "summary": f"分析了{len(results)}条视频，{'触发了提示词优化' if need_optimize else '无需优化，一切正常'}",
        }

    async def review_agent_output(self, agent_name: str, agent_output: dict,
                                   data_summary: str) -> dict:
        """审核单个Agent的输出质量"""
        review_agent = self.agents["review_agent"]
        prompt_info = prompt_manager.get_active_prompt(agent_name)

        review_data = {
            "agent_name": agent_name,
            "prompt_version": prompt_info.get("version", "0.0.0"),
            "agent_output": json.dumps(agent_output, ensure_ascii=False),
            "data_summary": data_summary,
        }
        return await review_agent.safe_run(review_data, "")

    async def auto_optimize(self, review_results: list[dict]) -> dict:
        """根据审核结果自动优化提示词"""
        optimizer = self.agents["prompt_optimizer"]
        results = {}

        for review in review_results:
            agent_name = review.get("agent_name")
            if not agent_name or not review.get("should_optimize_prompt"):
                continue

            current_prompt = prompt_manager.get_active_prompt(agent_name)
            feedback = review.get("improvement_suggestions", [])
            weaknesses = review.get("weaknesses", [])

            optimize_data = {
                "target_agent": agent_name,
                "current_prompt": current_prompt,
                "review_feedback": f"问题: {'; '.join(weaknesses)}\n改进建议: {'; '.join(feedback)}",
                "optimization_notes": "自动优化：根据审核反馈修复提示词问题",
            }

            result = await optimizer.safe_run(optimize_data, "")
            results[agent_name] = result

        return results

    async def review_and_optimize(self, data: dict) -> dict:
        """
        独立的审核+优化闭环（不执行分析，只做审查询问）
        用于周期性审核或新增数据后触发
        """
        agent_outputs = data.get("agent_outputs", [])
        new_data_features = data.get("new_data_features", "")

        review_results = []
        for item in agent_outputs:
            result = await self.review_agent_output(
                item.get("agent_name", ""),
                item.get("output", {}),
                item.get("data_summary", ""),
            )
            review_results.append(result)

        need_optimize = any(r.get("should_optimize_prompt", False) for r in review_results)

        optimization_result = None
        if need_optimize or new_data_features:
            optimization_result = await self.auto_optimize(review_results)

        return {
            "status": "success",
            "reviews": review_results,
            "optimization": optimization_result,
            "need_optimize": need_optimize,
            "summary": f"审核了{len(review_results)}个Agent输出，{'已触发优化' if need_optimize else '无需优化'}",
        }

    def _build_summary(self, video_data: dict, content: dict, creative: dict,
                       scoring: dict, consumption: dict) -> str:
        """构建分析汇总"""
        score_info = scoring.get("overall_score", 0) if isinstance(scoring.get("overall_score"), (int, float)) \
            else (scoring.get("overall_score") if isinstance(scoring.get("overall_score"), (int, float))
                  else scoring.get("scores", {}).get("overall", 0))

        lines = [
            f"【{video_data.get('视频名称', '未知视频')}】分析报告",
            f"综合评分: {score_info}/100 (等级: {scoring.get('level', 'N/A')})",
            f"脚本类型: {content.get('script_analysis', {}).get('type', 'N/A')}",
            f"消耗级别: {consumption.get('consumption_level', 'N/A')} ({consumption.get('consumption_value', 0)})",
        ]
        return "\n".join(lines)


# 全局单例
orchestrator = OrchestratorAgent()

