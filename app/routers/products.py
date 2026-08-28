"""
产品管理 API 路由
支持上传文件/飞书链接导入产品，生成产品标签
"""
import json
import io
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Query
from pydantic import BaseModel
from app.database import db_service
from app.agents.product_analyzer import product_analyzer

router = APIRouter()


class FeishuImportRequest(BaseModel):
    url: str
    product_name: str = ""


@router.post("/upload")
async def upload_product_file(
    file: UploadFile = File(...),
    product_name: str = Form(""),
):
    """上传产品文件（支持txt/csv/xlsx/pdf/jpg/png）"""
    content = await file.read()
    filename = file.filename or "未命名"
    ext = filename.lower().rsplit(".", 1)[-1] if "." in filename else ""

    supported = {"txt", "csv", "xlsx", "xls", "pdf", "jpg", "jpeg", "png"}
    if ext not in supported:
        raise HTTPException(400, f"不支持的文件格式: .{ext}，支持 {', '.join(sorted(supported))}")

    # 提取文本内容
    raw_text = ""
    if ext in ("txt", "csv"):
        raw_text = content.decode("utf-8", errors="replace")[:3000]
    elif ext in ("xlsx", "xls"):
        try:
            import openpyxl
            wb = openpyxl.load_workbook(io.BytesIO(content), read_only=True)
            for row in wb.active.iter_rows(values_only=True):
                raw_text += " ".join(str(c or "") for c in row) + "\n"
                if len(raw_text) > 3000:
                    break
        except Exception:
            raw_text = f"[无法解析Excel内容，文件: {filename}]"
    elif ext in ("jpg", "jpeg", "png"):
        raw_text = f"[图片文件: {filename}，请手动输入产品名称和详情]"
    elif ext == "pdf":
        raw_text = f"[PDF文件: {filename}，请手动输入产品名称和详情]"

    # 用AI分析产品
    name = product_name or filename.rsplit(".", 1)[0]
    ai_result = await product_analyzer.safe_run({
        "raw_text": raw_text or f"文件名: {filename}",
        "product_name": name,
    }, "")

    pname = ai_result.get("product_name", name) or name
    details = ai_result.get("details", raw_text[:500]) or raw_text[:500]
    tags = ai_result.get("tags", []) or []

    product_id = db_service.save_product({
        "name": pname,
        "details": details,
        "tags": tags,
        "source_type": "upload",
        "source_name": filename,
    })

    return {
        "id": product_id,
        "name": pname,
        "details": details,
        "tags": tags,
        "message": f"产品「{pname}」已导入",
    }


@router.post("/feishu")
async def import_product_from_feishu(req: FeishuImportRequest):
    """从飞书链接导入产品信息"""
    # 简单解析飞书链接，提取文本内容
    raw_text = f"飞书链接: {req.url}"
    name = req.product_name or "飞书导入产品"

    ai_result = await product_analyzer.safe_run({
        "raw_text": raw_text,
        "product_name": name,
    }, "")

    pname = ai_result.get("product_name", name) or name
    details = ai_result.get("details", raw_text[:500]) or raw_text[:500]
    tags = ai_result.get("tags", []) or []

    product_id = db_service.save_product({
        "name": pname,
        "details": details,
        "tags": tags,
        "source_type": "feishu",
        "source_name": req.url,
    })

    return {
        "id": product_id,
        "name": pname,
        "details": details,
        "tags": tags,
    }


@router.post("/manual")
async def add_product_manual(
    name: str = Form(...),
    details: str = Form(""),
    tags: str = Form(""),
):
    """手动添加产品"""
    tag_list = [t.strip() for t in tags.split(",") if t.strip()] if tags else []
    product_id = db_service.save_product({
        "name": name,
        "details": details,
        "tags": tag_list,
        "source_type": "manual",
    })
    return {"id": product_id, "name": name, "tags": tag_list}


@router.get("")
async def get_products():
    """获取产品列表"""
    products = db_service.get_products(100)
    return {
        "products": [
            {
                "id": p.id,
                "name": p.name,
                "details": (p.details or "")[:200],
                "tags": p.tags or [],
                "source_type": p.source_type,
                "source_name": p.source_name,
                "created_at": str(p.created_at)[:19] if p.created_at else "",
            }
            for p in products
        ]
    }


@router.get("/{product_id}")
async def get_product_detail(product_id: int):
    """获取产品详情"""
    p = db_service.get_product_by_id(product_id)
    if not p:
        raise HTTPException(404, "未找到该产品")
    return {
        "id": p.id,
        "name": p.name,
        "details": p.details or "",
        "tags": p.tags or [],
        "source_type": p.source_type,
        "source_name": p.source_name,
        "created_at": str(p.created_at)[:19] if p.created_at else "",
    }


@router.post("/{product_id}/generate-tags")
async def generate_product_tags(product_id: int):
    """AI生成产品标签"""
    p = db_service.get_product_by_id(product_id)
    if not p:
        raise HTTPException(404, "未找到该产品")

    ai_result = await product_analyzer.safe_run({
        "raw_text": p.details or "",
        "product_name": p.name,
    }, "")

    tags = ai_result.get("tags", []) or []
    db_service.save_product({"name": p.name, "details": p.details, "tags": tags})
    return {"id": product_id, "tags": tags}


@router.delete("/{product_id}")
async def delete_product(product_id: int):
    """删除产品"""
    db_service.delete_product(product_id)
    return {"status": "deleted"}

