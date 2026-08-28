"""
脚本生成Agent - 结合数据+分析+反馈，生成编导可用的前10秒脚本
"""
import json
import re
from typing import Optional

from app.agents.base_agent import BaseAgent
from app.database import db_service, GeneratedScript
from app.services.llm_service import llm_service
from app.services.prompt_manager import prompt_manager


class ScriptGeneratorAgent(BaseAgent):
    """脚本生成Agent"""

    def __init__(self):
        super().__init__("script_generator")

    @staticmethod
    def _parse_llm_json(raw: str) -> dict:
        """从LLM原始输出中提取JSON，兼容markdown代码块和多余文本"""
        if not raw or raw.startswith("[LLM"):
            return {}
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            pass

        # 移除markdown代码块标记
        clean = raw.strip()
        clean = re.sub(r'^```(?:json)?\s*', '', clean)
        clean = re.sub(r'\s*```$', '', clean)

        # 提取第一个 { 到最后一个 } 之间的内容
        brace_start = clean.find('{')
        brace_end = clean.rfind('}')
        if brace_start != -1 and brace_end > brace_start:
            clean = clean[brace_start:brace_end + 1]

        try:
            return json.loads(clean)
        except json.JSONDecodeError:
            pass

        # 最后尝试：去掉转义引号中的多余反斜杠
        try:
            clean = clean.replace('\\"', '"')
            clean = clean.replace('\\n', '\n')
            return json.loads(clean)
        except json.JSONDecodeError:
            return {}

    async def run(self, data: dict) -> dict:
        """执行脚本生成"""
        # 收集历史反馈
        rejected_reasons = ""
        approved_types = ""
        director_notes = data.get("director_notes", "")

        # 从数据库获取历史反馈
        scripts = db_service.get_scripts(limit=20)
        approved = [s for s in scripts if s.review_status == "approved"]
        rejected = [s for s in scripts if s.review_status == "rejected"]

        if approved:
            types = [s.script_type for s in approved if s.script_type]
            approved_types = ", ".join(set(filter(None, types)))
        if rejected:
            notes = [s.review_notes for s in rejected if s.review_notes]
            rejected_reasons = "; ".join(notes[:5])

        # 从本地数据库获取活跃提示词
        local_prompt = db_service.get_local_prompt("script_generator")
        prompt_version = "1.0.0"
        if local_prompt:
            try:
                prompt_data = json.loads(local_prompt.prompt_content)
                prompt_version = prompt_data.get("version", local_prompt.version)
            except json.JSONDecodeError:
                pass

        # 准备LLM输入
        llm_data = {
            "video_name": data.get("视频名称", ""),
            "product_name": data.get("产品名称", ""),
            "brand": data.get("品牌", ""),
            "duration": data.get("时长", 0),
            "cost": data.get("视频消耗", 0),
            "roi": data.get("整体支付ROI", 0),
            "completion_rate": data.get("完播率", 0),
            "play_2s": data.get("2秒播放率", 0),
            "play_3s": data.get("3秒播放率", 0),
            "play_5s": data.get("5秒播放率", 0),
            "play_10s": data.get("10秒播放率", 0),
            "script_tags": str(data.get("脚本类型标签", [])),
            "hook_tags": str(data.get("五秒停留标签", [])),
            "appeal_tags": str(data.get("吸睛标签", [])),
            "reason_tags": str(data.get("转化理由标签", [])),
            "hook_analysis": str(data.get("前五秒停留分析.输出结果", ""))[:300],
            "selling_point_analysis": str(data.get("【卖点点击】.输出结果", ""))[:300],
            "visual_appeal": str(data.get("画面吸睛【方式】.输出结果", ""))[:300],
            "approved_types": approved_types,
            "rejected_reasons": rejected_reasons,
            "director_notes": director_notes,
            "focus_angle": data.get("_focus_angle", ""),
        }

        result = await self.call_llm(llm_data)

        # 增强JSON解析：移除markdown代码块、提取纯JSON
        parsed = self._parse_llm_json(result)

        script_text = parsed.get("script_text", "")
        script_type = parsed.get("script_type", "未知")
        hook_type = parsed.get("hook_type", "未知")
        focus_point = parsed.get("focus_point", "")
        production_tag = parsed.get("production_tag", "")

        # 如果解析后script_text为空或仍是JSON结构，说明提取失败，直接显示校验提醒
        if not script_text or script_text.startswith("{"):
            script_text = f"⚠️ 脚本生成异常，请重试。原始输出：{result[:200]}"

        # 校验制作标签合法性
        valid_tags = {"AI完全生成", "真人+绿幕(低成本)", "真人+绿幕(高成本)", "真人+绿幕(模拟真实场景)"}
        if production_tag not in valid_tags:
            production_tag = ""

        # 保存到数据库
        source_summary = json.dumps({
            "video": data.get("视频名称", ""),
            "product": data.get("产品名称", ""),
            "tags": {
                "script": str(data.get("脚本类型标签", [])),
                "hook": str(data.get("五秒停留标签", [])),
                "appeal": str(data.get("吸睛标签", [])),
            }
        }, ensure_ascii=False)

        script_id = db_service.save_script({
            "video_record_id": data.get("record_id", ""),
            "video_name": data.get("视频名称", ""),
            "product_name": data.get("产品名称", ""),
            "brand": data.get("品牌", ""),
            "script_text": script_text,
            "script_type": script_type,
            "focus_point": focus_point,
            "hook_type": hook_type,
            "production_tag": production_tag,
            "prompt_version": prompt_version,
            "source_data_summary": source_summary,
        })

        return {
            "agent": "script_generator",
            "script_id": script_id,
            "script_type": script_type,
            "hook_type": hook_type,
            "focus_point": focus_point,
            "script_text": script_text,
            "production_tag": production_tag,
            "design_rationale": parsed.get("design_rationale", ""),
            "prompt_version": prompt_version,
            "raw_llm_output": result,
        }

    def format_script_for_display(self, script: GeneratedScript) -> dict:
        """将数据库中的脚本格式化为Web展示"""
        return {
            "id": script.id,
            "video_name": script.video_name,
            "product_name": script.product_name,
            "script_type": script.script_type,
            "hook_type": script.hook_type,
            "focus_point": script.focus_point,
            "script_text": script.script_text,
            "production_tag": script.production_tag or "",
            "review_status": script.review_status,
            "review_notes": script.review_notes,
            "prompt_version": script.prompt_version,
            "generated_at": str(script.generated_at) if script.generated_at else "",
        }


# 全局单例
script_generator = ScriptGeneratorAgent()

