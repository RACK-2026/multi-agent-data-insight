"""
创意工坊 API 路由
"""
from fastapi import APIRouter
from pydantic import BaseModel
from app.database import db_service

router = APIRouter()


class SuggestionRequest(BaseModel):
    type: str  # script / title
    content: str


@router.post("/suggestion")
async def submit_suggestion(req: SuggestionRequest):
    """提交创意建议"""
    if req.type not in ("script", "title"):
        return {"status": "error", "message": "type 必须是 script 或 title"}

    db_service.save_suggestion({
        "type": req.type,
        "content": req.content,
    })

    msg = "提交成功，感谢您对优化脚本的支持！" if req.type == "script" else "提交成功，感谢您对标题创新的建议。"
    return {"status": "ok", "message": msg}


@router.get("/suggestions")
async def get_suggestions(type: str = "", status: str = ""):
    """获取建议列表"""
    items = db_service.get_suggestions(
        stype=type or None,
        status=status or None,
        limit=100,
    )
    return {
        "suggestions": [
            {
                "id": s.id,
                "type": s.type,
                "content": s.content,
                "status": s.status,
                "created_at": str(s.created_at)[:19] if s.created_at else "",
            }
            for s in items
        ]
    }


@router.post("/optimize")
async def trigger_optimize():
    """触发AI评审建议并优化提示词"""
    from app.agents.orchestrator import orchestrator
    from app.services.prompt_manager import prompt_manager

    # 获取待评审的建议
    script_suggestions = db_service.get_suggestions(stype="script", status="pending", limit=20)
    title_suggestions = db_service.get_suggestions(stype="title", status="pending", limit=20)

    results = []

    # 评审编导脚本建议 - 优化编导相关提示词
    if script_suggestions:
        contents = "\n".join([f"- {s.content}" for s in script_suggestions])
        prompt = prompt_manager.get_active_prompt("prompt_optimizer")
        if prompt:
            try:
                result = await orchestrator.agents["prompt_optimizer"].safe_run({
                    "target_agent": "script_generator",
                    "current_prompt": prompt,
                    "review_feedback": f"编导创意建议：\n{contents}",
                    "optimization_notes": "基于编导创意建议的提示词优化",
                }, "")
                if result.get("status") == "optimized" or "optimized_prompt" in result:
                    results.append("script")
            except Exception:
                pass
        # 标记已评审
        for s in script_suggestions:
            db_service.mark_suggestion_reviewed(s.id)

    # 评审标题创新建议 - 优化标题提示词
    if title_suggestions:
        contents = "\n".join([f"- {s.content}" for s in title_suggestions])
        prompt = prompt_manager.get_active_prompt("prompt_optimizer")
        if prompt:
            try:
                result = await orchestrator.agents["prompt_optimizer"].safe_run({
                    "target_agent": "title_generator",
                    "current_prompt": prompt,
                    "review_feedback": f"标题创新建议：\n{contents}",
                    "optimization_notes": "基于标题创意建议的提示词优化",
                }, "")
                if result.get("status") == "optimized" or "optimized_prompt" in result:
                    results.append("title")
            except Exception:
                pass
        for s in title_suggestions:
            db_service.mark_suggestion_reviewed(s.id)

    return {"status": "ok", "optimized": results}

