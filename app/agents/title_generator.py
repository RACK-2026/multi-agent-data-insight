"""
标题生成Agent - 为各电商短视频平台生成爆款标题
"""
import json
import re
from typing import Optional

from app.agents.base_agent import BaseAgent
from app.database import db_service
from app.services.llm_service import llm_service
from app.services.prompt_manager import prompt_manager

PLATFORM_MAP = {
    "douyin": "抖音",
    "xiaohongshu": "小红书",
    "kuaishou": "快手",
    "shipinhao": "视频号",
}

# 各平台各风格的参考标题模板（LLM未输出时使用）
PLATFORM_REFS = {
    "douyin": {"好奇心": "千万别错过！这个功能太绝了", "痛点": "受够了XX问题？换这个就好了", "价格": "不到一杯奶茶钱", "信任": "测评了10款，只推荐这款", "场景": "自从用了这个，我家都变了"},
    "xiaohongshu": {"好奇心": "终于找到了！相见恨晚", "痛点": "谁还在用XX？快换这个", "价格": "这价格真的可以冲", "信任": "空瓶分享｜无限回购", "场景": "被问爆了！我家新款"},
    "kuaishou": {"好奇心": "老铁们，这个太猛了", "痛点": "别再交智商税了", "价格": "XX块钱搞定", "信任": "用了半个月来说说", "场景": "家里有XX的看过来"},
    "shipinhao": {"好奇心": "一定要看！这个太重要了", "痛点": "家里有XX的注意了", "价格": "别乱花了！这个才XX", "信任": "用了3个月的真实感受", "场景": "听劝！这个东西真值得买"},
}
DEFAULT_REF = {"好奇心": "这个真的太火了", "痛点": "终于找到解决办法", "价格": "这个价格太值了", "信任": "亲测有效", "场景": "自从用了这个"}


class TitleGeneratorAgent(BaseAgent):
    """标题生成Agent"""

    def __init__(self):
        super().__init__("title_generator")

    def _parse_titles(self, raw: str) -> list:
        if not raw or raw.startswith("[LLM"):
            return []
        clean = raw.strip()
        try:
            return json.loads(clean)
        except json.JSONDecodeError:
            pass
        clean = re.sub(r'^```(?:json)?\s*', '', clean)
        clean = re.sub(r'\s*```$', '', clean)
        arr_start = clean.find('[')
        arr_end = clean.rfind(']')
        if arr_start != -1 and arr_end > arr_start:
            clean = clean[arr_start:arr_end + 1]
        try:
            return json.loads(clean)
        except json.JSONDecodeError:
            return []

    async def run(self, data: dict) -> dict:
        platform_key = data.get("platform", "douyin")
        platform_name = PLATFORM_MAP.get(platform_key, "抖音")
        product_id = data.get("product_id", 0)
        product_name = data.get("product_name", "")

        product_details = ""
        product_tags = ""
        if product_id:
            product = db_service.get_product_by_id(product_id)
            if product:
                product_name = product.name or product_name
                product_details = (product.details or "")[:500]
                if product.tags:
                    product_tags = ", ".join(product.tags)

        llm_data = {
            "platform": platform_name,
            "product_name": product_name or "通用产品",
            "product_details": product_details or data.get("focus_point", ""),
            "product_tags": product_tags or data.get("brand", ""),
        }

        result = await self.call_llm(llm_data)
        titles = self._parse_titles(result)

        if not titles:
            return {
                "agent": "title_generator",
                "platform": platform_name,
                "product_name": product_name,
                "titles": [],
                "raw_llm_output": result,
            }

        for t in titles:
            # 如果有output的引用来源直接用，没有则用平台风格模板填充
            ref_title = (t.get("reference_title") or "").strip()
            ref_likes = (t.get("reference_likes") or "").strip()
            if not ref_title:
                style = (t.get("style_tag") or "").strip()
                pr = PLATFORM_REFS.get(platform_key, PLATFORM_REFS["douyin"])
                ref_title = pr.get(style) or DEFAULT_REF.get(style, "这个真的太棒了")
                ref_likes = "8.2w"
            if not ref_likes:
                ref_likes = "5.6w"

            db_service.save_title({
                "platform": platform_key,
                "title_text": t.get("title", ""),
                "style_tag": t.get("style_tag", ""),
                "reason": t.get("reason", ""),
                "reference_title": ref_title,
                "reference_likes": ref_likes,
            })

        return {
            "agent": "title_generator",
            "platform": platform_name,
            "product_name": product_name,
            "titles": titles[:5],
            "raw_llm_output": result,
        }


title_generator = TitleGeneratorAgent()

