"""
标题生成 API 路由
"""
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from app.database import db_service

router = APIRouter()


class GenerateTitleRequest(BaseModel):
    platform: str = "douyin"
    product_name: str = ""
    brand: str = ""
    focus_point: str = ""
    product_id: int = 0


class TitleReviewRequest(BaseModel):
    action: str  # approved / rejected
    notes: str = ""


@router.post("/generate")
async def generate_titles(req: GenerateTitleRequest):
    """为指定平台生成电商短视频标题（支持关联产品）"""
    from app.agents.title_generator import title_generator
    result = await title_generator.safe_run({
        "platform": req.platform,
        "product_id": req.product_id,
        "product_name": req.product_name,
        "brand": req.brand,
        "focus_point": req.focus_point,
    }, "")

    if result.get("titles"):
        for t in result["titles"]:
            db_service.save_title({
                "platform": req.platform,
                "title_text": t.get("title", ""),
                "style_tag": t.get("style_tag", ""),
                "reason": t.get("reason", ""),
                "reference_title": t.get("reference_title", "") or "",
                "reference_likes": t.get("reference_likes", "") or "",
            })
    return result


@router.get("/list")
async def get_title_list(
    platform: str = Query("", description="平台筛选"),
    limit: int = Query(50, ge=1, le=200),
):
    """获取生成的标题列表"""
    titles = db_service.get_titles(platform=platform or None, limit=limit)
    return {
        "titles": [
            {
                "id": t.id,
                "platform": t.platform,
                "title_text": t.title_text,
                "style_tag": t.style_tag,
                "reason": t.reason,
                "reference_title": t.reference_title or "",
                "reference_likes": t.reference_likes or "",
                "review_status": t.review_status,
                "review_notes": t.review_notes or "",
                "generated_at": str(t.generated_at)[:19] if t.generated_at else "",
            }
            for t in titles
        ]
    }


@router.post("/{title_id}/review")
async def review_title(title_id: int, req: TitleReviewRequest):
    """审核标题：打勾(approved) / 打叉(rejected) + 备注"""
    if req.action not in ("approved", "rejected"):
        raise HTTPException(400, "action 必须是 approved 或 rejected")

    db_service.update_title_review(title_id, req.action, req.notes)
    db_service.save_title_feedback(title_id, req.action, req.notes or "")
    return {"status": "ok", "title_id": title_id, "action": req.action}


@router.get("/platforms")
async def get_platforms():
    """获取支持的平台列表"""
    return {
        "platforms": [
            {"key": "douyin", "name": "抖音", "icon": "🎵"},
            {"key": "xiaohongshu", "name": "小红书", "icon": "📕"},
            {"key": "kuaishou", "name": "快手", "icon": "🎬"},
            {"key": "shipinhao", "name": "视频号", "icon": "💬"},
        ]
    }

