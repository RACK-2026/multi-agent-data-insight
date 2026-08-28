"""
脚本管理 API 路由
包含：脚本生成、编导审核（打勾/打叉）、备注、提示词管理、版本历史
"""
import json
from datetime import datetime
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.database import db_service
from app.agents.script_generator import script_generator

router = APIRouter()


# ==================== 请求/响应模型 ====================

class GenerateRequest(BaseModel):
    record_id: str = ""
    director_notes: str = ""


class ReviewRequest(BaseModel):
    action: str  # "approved" 或 "rejected"
    notes: str = ""


class UpdateTagRequest(BaseModel):
    production_tag: str


class SavePromptRequest(BaseModel):
    category: str
    content: str
    version: str = ""
    notes: str = ""


# ==================== 脚本生成 ====================

@router.post("/generate")
async def generate_script(req: GenerateRequest):
    """基于视频数据生成3个不同角度的前10秒脚本文案（并行生成）"""
    from app.services.feishu_service import feishu_service

    # 获取视频数据
    if req.record_id:
        records = feishu_service.get_records("main", [req.record_id])
        if not records:
            raise HTTPException(404, "未找到该视频记录")
        video_data = records[0]
    else:
        records = feishu_service.query_records("main", sorts=["采集时间 desc"], max_records=1)
        if not records:
            raise HTTPException(400, "无可用视频数据")
        video_data = records[0]

    video_data["record_id"] = video_data.get("record_id", "")
    video_data["director_notes"] = req.director_notes

    # 3个不同角度的脚本 — 并行生成
    import asyncio

    focus_angles = [
        "以价格利益为核心卖点，强调性价比和优惠",
        "以使用场景为核心，展示产品如何解决日常痛点",
        "以品质信任为核心，用数据和权威背书建立信任",
    ]

    async def gen_one(angle: str) -> dict:
        data = {**video_data, "_focus_angle": angle}
        return await script_generator.safe_run(data, data.get("record_id", ""))

    results = await asyncio.gather(*[gen_one(a) for a in focus_angles])
    scripts = [r for r in results if r.get("script_id")]

    return {"scripts": scripts, "total": len(scripts)}


# ==================== 脚本管理 ====================

@router.get("/scripts")
async def get_scripts(
    status: str = "",
    limit: int = 50,
):
    """获取脚本列表"""
    scripts = db_service.get_scripts(status=status if status else None, limit=limit)
    return {
        "scripts": [
            script_generator.format_script_for_display(s) for s in scripts
        ]
    }


@router.get("/scripts/{script_id}")
async def get_script_detail(script_id: int):
    """获取单个脚本详情"""
    script = db_service.get_script_by_id(script_id)
    if not script:
        raise HTTPException(404, "未找到该脚本")
    return script_generator.format_script_for_display(script)


@router.post("/scripts/{script_id}/review")
async def review_script(script_id: int, req: ReviewRequest):
    """编导审核脚本：打勾(approved) / 打叉(rejected) + 备注"""
    if req.action not in ("approved", "rejected"):
        raise HTTPException(400, "action 必须是 approved 或 rejected")

    script = db_service.get_script_by_id(script_id)
    if not script:
        raise HTTPException(404, "未找到该脚本")

    # 更新脚本状态
    db_service.update_script_review(script_id, req.action, req.notes)

    # 保存反馈历史
    db_service.save_feedback(
        script_id=script_id,
        action=req.action,
        notes=req.notes or "",
        prompt_version=script.prompt_version or "1.0.0",
    )

    return {"status": "ok", "script_id": script_id, "action": req.action}


@router.patch("/scripts/{script_id}/tag")
async def update_script_tag(script_id: int, req: UpdateTagRequest):
    """更新脚本的制作标签"""
    valid_tags = {"AI完全生成", "真人+绿幕(低成本)", "真人+绿幕(高成本)", "真人+绿幕(模拟真实场景)"}
    if req.production_tag and req.production_tag not in valid_tags:
        raise HTTPException(400, f"无效的制作标签，可选: {', '.join(valid_tags)}")

    script = db_service.get_script_by_id(script_id)
    if not script:
        raise HTTPException(404, "未找到该脚本")

    db_service.update_script_tag(script_id, req.production_tag)
    return {"status": "ok", "script_id": script_id, "production_tag": req.production_tag}


@router.get("/scripts/{script_id}/feedback")
async def get_script_feedback(script_id: int):
    """获取某个脚本的反馈历史"""
    with db_service.get_session() as session:
        from app.database import ScriptFeedback
        feedbacks = session.query(ScriptFeedback).filter_by(
            script_id=script_id
        ).order_by(ScriptFeedback.created_at.desc()).all()

    return {
        "feedback": [
            {
                "id": f.id,
                "action": f.action,
                "notes": f.notes,
                "prompt_version": f.prompt_version,
                "created_at": str(f.created_at),
            }
            for f in feedbacks
        ]
    }


# ==================== 提示词管理（本地） ====================

@router.get("/prompts/local")
async def get_local_prompts():
    """获取所有本地提示词的当前活跃版本"""
    categories = [
        "script_generator", "content_analyzer", "creative_analyzer",
        "scoring_agent", "consumption_agent",
    ]
    result = {}
    for cat in categories:
        prompt = db_service.get_local_prompt(cat)
        if prompt:
            try:
                content = json.loads(prompt.prompt_content)
            except json.JSONDecodeError:
                content = {"raw": prompt.prompt_content[:200]}
            result[cat] = {
                "id": prompt.id,
                "version": prompt.version,
                "content": prompt.prompt_content[:200] + "..." if len(prompt.prompt_content) > 200 else prompt.prompt_content,
                "full_content": prompt.prompt_content,
                "source": prompt.source,
                "notes": prompt.notes,
                "is_active": prompt.is_active,
                "created_at": str(prompt.created_at),
            }
    return {"prompts": result}


@router.get("/prompts/local/{category}")
async def get_local_prompt_detail(category: str):
    """获取指定分类的提示词详情"""
    prompt = db_service.get_local_prompt(category)
    if not prompt:
        raise HTTPException(404, f"未找到分类: {category}")

    history = db_service.get_prompt_history(category)

    return {
        "active": {
            "id": prompt.id,
            "version": prompt.version,
            "content": prompt.prompt_content,
            "source": prompt.source,
            "notes": prompt.notes,
            "created_at": str(prompt.created_at),
        },
        "history": [
            {
                "id": h.id,
                "version": h.version,
                "content": h.prompt_content[:100] + "..." if len(h.prompt_content) > 100 else h.prompt_content,
                "source": h.source,
                "notes": h.notes,
                "is_active": h.is_active,
                "created_at": str(h.created_at),
            }
            for h in history[:10]
        ],
    }


@router.post("/prompts/local/save")
async def save_local_prompt(req: SavePromptRequest):
    """保存/更新本地提示词"""
    version = req.version or datetime.now().strftime("%Y%m%d_%H%M%S")

    # 校验内容格式
    try:
        json.loads(req.content)
    except json.JSONDecodeError:
        # 如果不是JSON，包装一下
        req.content = json.dumps({
            "agent_name": req.category,
            "version": version,
            "prompt_content": req.content,
        }, ensure_ascii=False)

    db_service.save_local_prompt(
        category=req.category,
        version=version,
        content=req.content,
        notes=req.notes,
        source="manual",
    )
    return {"status": "ok", "category": req.category, "version": version}


# ==================== 优化闭环 ====================

@router.post("/optimize/feedback")
async def optimize_from_feedback():
    """基于编导反馈自动优化脚本生成提示词"""
    # 获取最近的审核反馈
    with db_service.get_session() as session:
        from app.database import ScriptFeedback
        feedbacks = session.query(ScriptFeedback).order_by(
            ScriptFeedback.created_at.desc()
        ).limit(20).all()

    if not feedbacks:
        raise HTTPException(400, "暂无编导反馈数据")

    # 统计反馈
    approved_count = sum(1 for f in feedbacks if f.action == "approved")
    rejected_count = sum(1 for f in feedbacks if f.action == "rejected")
    rejected_notes = [f.notes for f in feedbacks if f.action == "rejected" and f.notes]

    # 获取当前提示词
    current_prompt = db_service.get_local_prompt("script_generator")
    if not current_prompt:
        raise HTTPException(400, "未找到脚本生成提示词")

    # 构建优化数据
    feedback_summary = (
        f"最近{len(feedbacks)}次反馈：{approved_count}次通过，{rejected_count}次拒绝\n"
        f"拒绝原因：{'；'.join(rejected_notes[:5])}"
    )

    # 调用优化提示词Agent
    from app.agents.orchestrator import orchestrator
    optimizer = orchestrator.agents["prompt_optimizer"]
    optimize_result = await optimizer.safe_run({
        "target_agent": "script_generator",
        "current_prompt": json.loads(current_prompt.prompt_content) if isinstance(current_prompt.prompt_content, str) else current_prompt.prompt_content,
        "review_feedback": feedback_summary,
        "optimization_notes": "编导反馈驱动的提示词优化",
    }, "")

    if optimize_result.get("status") == "optimized" or "optimized_prompt" in optimize_result:
        new_content = optimize_result.get("optimized_prompt") or optimize_result
        version = optimize_result.get("new_version", datetime.now().strftime("%Y%m%d_%H%M%S"))
        db_service.save_local_prompt(
            category="script_generator",
            version=version,
            content=json.dumps(new_content, ensure_ascii=False) if isinstance(new_content, dict) else str(new_content),
            notes=f"基于编导反馈自动优化（{approved_count}通过/{rejected_count}拒绝）",
            source="auto_optimized",
        )
        return {
            "status": "optimized",
            "version": version,
            "feedback_summary": feedback_summary,
            "changes": optimize_result.get("changes", []),
        }

    return {
        "status": "no_change",
        "feedback_summary": feedback_summary,
        "message": "当前提示词无需优化",
    }

