"""
产品分析Agent - 从上传文件/飞书链接解析产品信息，生成产品详情标签
"""
import json
import re
from app.agents.base_agent import BaseAgent


class ProductAnalyzerAgent(BaseAgent):
    """产品分析Agent"""

    def __init__(self):
        super().__init__("product_analyzer")

    async def run(self, data: dict) -> dict:
        """分析产品数据，生成产品标签"""
        raw_text = data.get("raw_text", "")
        product_name = data.get("product_name", "")

        # 如果文本为空，返回空
        if not raw_text and not product_name:
            return {"product_name": product_name, "details": "", "tags": [], "suggested_tags": []}

        # 准备LLM输入
        llm_data = {
            "raw_text": raw_text[:2000],
            "product_name": product_name,
        }

        result = await self.call_llm(llm_data)

        # 解析JSON
        parsed = {}
        try:
            parsed = json.loads(result)
        except json.JSONDecodeError:
            clean = result.strip()
            clean = re.sub(r'^```(?:json)?\s*', '', clean)
            clean = re.sub(r'\s*```$', '', clean)
            try:
                parsed = json.loads(clean)
            except json.JSONDecodeError:
                parsed = {}

        return {
            "product_name": parsed.get("product_name", product_name),
            "details": parsed.get("details", raw_text[:500]),
            "tags": parsed.get("tags", []),
            "suggested_tags": parsed.get("suggested_tags", []),
            "raw_llm_output": result,
        }


product_analyzer = ProductAnalyzerAgent()

