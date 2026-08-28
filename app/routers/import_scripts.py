"""
脚本导入API - 从飞书链接/Excel/CSV/TXT导入编导脚本
"""
import json
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from pydantic import BaseModel
from app.services.script_import_service import ScriptImportService

router = APIRouter()


class FeishuImportRequest(BaseModel):
    url: str
    director: str = ""


@router.post("/feishu")
async def import_from_feishu(req: FeishuImportRequest):
    """从飞书Bitable链接导入编导脚本"""
    scripts = await ScriptImportService.import_from_feishu(req.url, req.director)
    if not scripts:
        raise HTTPException(400, "未从链接中解析到脚本内容，请确认链接正确且包含脚本数据")

    result = ScriptImportService.import_scripts(scripts)
    return {
        **result,
        "scripts": [{"script_text": s["script_text"][:100], "source": s["source"]} for s in scripts[:5]],
    }


@router.post("/file")
async def import_from_file(
    file: UploadFile = File(...),
    director: str = Form(""),
):
    """从上传文件导入编导脚本（支持 .txt / .csv / .xlsx）"""
    content = await file.read()
    filename = file.filename or "未命名文件"

    if not content or len(content) < 10:
        raise HTTPException(400, "文件内容为空")

    # 根据扩展名选择解析方式
    ext = filename.lower().rsplit(".", 1)[-1] if "." in filename else ""
    scripts = []

    if ext == "txt":
        text = content.decode("utf-8", errors="replace")
        scripts = ScriptImportService.parse_txt(text, filename)
    elif ext == "csv":
        scripts = ScriptImportService.parse_csv(content, filename)
    elif ext in ("xlsx", "xls"):
        scripts = ScriptImportService.parse_excel(content, filename)
    else:
        # 尝试按TXT解析
        try:
            text = content.decode("utf-8", errors="replace")
            scripts = ScriptImportService.parse_txt(text, filename)
        except Exception:
            raise HTTPException(400, f"不支持的文件格式: .{ext}，支持 txt/csv/xlsx")

    if not scripts:
        raise HTTPException(400, "未能从文件中解析出脚本内容，请检查文件格式")

    # 补充编导信息
    for s in scripts:
        if director and not s.get("director"):
            s["director"] = director

    result = ScriptImportService.import_scripts(scripts)
    return {
        **result,
        "scripts": [{"script_text": s["script_text"][:100], "type": s.get("script_type", "")} for s in scripts[:5]],
    }


@router.get("/list")
async def list_imported_scripts(limit: int = 50, source: str = ""):
    """查看已导入的脚本列表"""
    scripts = db_service.get_imported_scripts(source=source if source else None, limit=limit)
    return {
        "scripts": [
            {
                "id": s.id,
                "source": s.source,
                "source_name": s.source_name,
                "script_text": s.script_text[:200] + ("..." if len(s.script_text) > 200 else ""),
                "script_type": s.script_type,
                "product_name": s.product_name,
                "director": s.director,
                "notes": s.notes,
                "created_at": str(s.created_at),
            }
            for s in scripts
        ]
    }


@router.delete("/{script_id}")
async def delete_imported_script(script_id: int):
    """删除一条导入的脚本"""
    with db_service.get_session() as session:
        from app.database import ImportedScript
        s = session.query(ImportedScript).filter_by(id=script_id).first()
        if not s:
            raise HTTPException(404, "未找到该脚本")
        session.delete(s)
        session.commit()
    return {"status": "deleted"}


@router.post("/optimize-prompt")
async def optimize_prompt_with_imported():
    """使用导入的编导脚本来优化脚本生成提示词"""
    scripts = db_service.get_imported_scripts(limit=50)
    if not scripts:
        raise HTTPException(400, "暂无导入的参考脚本")

    # 提取脚本特征
    script_texts = [s.script_text for s in scripts if s.script_text]
    script_types = [s.script_type for s in scripts if s.script_type]
    products = [s.product_name for s in scripts if s.product_name]

    # 统计
    from collections import Counter
    type_stats = Counter(script_types).most_common(5)
    product_set = list(set(filter(None, products)))[:5]

    # 获取当前提示词
    current_prompt = db_service.get_local_prompt("script_generator")
    if not current_prompt:
        raise HTTPException(400, "未找到脚本生成提示词")

    # 构建优化输入
    feedback = (
        f"已导入{len(scripts)}条编导参考脚本\n"
        f"脚本类型分布: {dict(type_stats)}\n"
        f"涉及产品: {', '.join(product_set) if product_set else '无'}\n"
        f"参考脚本样例: {script_texts[0][:500] if script_texts else '无'}"
    )

    # 调用优化Agent
    import json as j
    from app.agents.orchestrator import orchestrator
    optimizer = orchestrator.agents["prompt_optimizer"]
    optimize_result = await optimizer.safe_run({
        "target_agent": "script_generator",
        "current_prompt": j.loads(current_prompt.prompt_content) if isinstance(current_prompt.prompt_content, str) else current_prompt.prompt_content,
        "review_feedback": feedback,
        "optimization_notes": "基于导入的编导参考脚本优化提示词，使其更贴近编导的实际脚本风格",
    }, "")

    if optimize_result.get("status") == "optimized" or "optimized_prompt" in optimize_result:
        new_content = optimize_result.get("optimized_prompt") or optimize_result
        from datetime import datetime
        version = optimize_result.get("new_version", datetime.now().strftime("%Y%m%d_%H%M%S"))
        db_service.save_local_prompt(
            category="script_generator",
            version=version,
            content=j.dumps(new_content, ensure_ascii=False) if isinstance(new_content, dict) else str(new_content),
            notes=f"基于{len(scripts)}条导入的编导脚本优化",
            source="auto_optimized",
        )
        return {
            "status": "optimized",
            "version": version,
            "script_count": len(scripts),
            "changes": optimize_result.get("changes", []),
        }

    return {"status": "no_change", "message": "当前提示词无需优化"}


# 导入 db_service
from app.database import db_service

