"""
数据看板 API 路由
"""
from typing import Optional
from collections import defaultdict

from fastapi import APIRouter, Query
from app.services.feishu_service import feishu_service

router = APIRouter()


def _load_records(max_records=500):
    """加载主表记录"""
    return feishu_service.query_records("main", sorts=["采集时间 desc"], max_records=max_records)


def _extract_filter_options(records: list) -> dict:
    """从记录中提取产品和编导的可用选项列表"""
    products = set()
    directors = set()
    for r in records:
        p = r.get("产品名称", "") or ""
        if p:
            products.add(p)
        d = r.get("编导", "") or ""
        if d:
            directors.add(d)
    return {
        "products": sorted(products),
        "directors": sorted(directors),
    }


def _apply_filters(records: list, product: str = None, director: str = None) -> list:
    """按产品/编导过滤记录"""
    filtered = records
    if product:
        filtered = [r for r in filtered if (r.get("产品名称", "") or "") == product]
    if director:
        filtered = [r for r in filtered if (r.get("编导", "") or "") == director]
    return filtered


@router.get("/summary")
async def get_dashboard_summary(
    product: str = Query("", description="按产品筛选"),
    director: str = Query("", description="按编导筛选"),
):
    """获取数据总看板的关键指标（支持按产品/编导筛选）"""
    records = _load_records(500)
    if not records:
        return {"total_records": 0, "summary": {}, "records": [], "filter_options": {}, "product_stats": [], "tag_stats": {}}

    # 提取筛选选项（基于全量数据）
    filter_options = _extract_filter_options(records)

    # 按筛选条件过滤
    filtered = _apply_filters(records, product or None, director or None)

    if not filtered:
        return {
            "total_records": 0,
            "summary": {},
            "records": [],
            "filter_options": filter_options,
            "product_stats": [],
            "tag_stats": {},
            "active_filter": {"product": product or "", "director": director or ""},
        }

    # 统计
    total_records = len(filtered)
    total_cost = sum(float(r.get("视频消耗", 0) or 0) for r in filtered)
    roi_values = [float(r.get("整体支付ROI", 0) or 0) for r in filtered if r.get("整体支付ROI") is not None]
    avg_roi = sum(roi_values) / len(roi_values) if roi_values else 0
    comp_rates = [float(r.get("完播率", 0) or 0) for r in filtered if r.get("完播率") is not None]
    avg_comp_rate = sum(comp_rates) / len(comp_rates) if comp_rates else 0
    click_rates = [float(r.get("整体点击率(%)", 0) or 0) for r in filtered if r.get("整体点击率(%)") is not None]
    conv_rates = [float(r.get("整体转化率(%)", 0) or 0) for r in filtered if r.get("整体转化率(%)") is not None]
    net_roi_values = [float(r.get("净成交ROI", 0) or 0) for r in filtered if r.get("净成交ROI") is not None]
    cpm_values = [float(r.get("千次展现费用", 0) or 0) for r in filtered if r.get("千次展现费用") is not None]

    # 标签维度统计
    script_tags = defaultdict(int)
    hook_tags = defaultdict(int)
    appeal_tags = defaultdict(int)
    reason_tags = defaultdict(int)
    for r in filtered:
        for t in (r.get("脚本类型标签") or []):
            if isinstance(t, str): script_tags[t] += 1
        for t in (r.get("五秒停留标签") or []):
            if isinstance(t, str): hook_tags[t] += 1
        for t in (r.get("吸睛标签") or []):
            if isinstance(t, str): appeal_tags[t] += 1
        for t in (r.get("转化理由标签") or []):
            if isinstance(t, str): reason_tags[t] += 1

    # 产品维度（在过滤后的数据上统计）
    product_data = {}
    for r in filtered:
        prod = r.get("产品名称", "未知") or "未知"
        cost = float(r.get("视频消耗", 0) or 0)
        if prod not in product_data:
            product_data[prod] = {"count": 0, "total_cost": 0, "total_roi": 0, "count_roi": 0}
        product_data[prod]["count"] += 1
        product_data[prod]["total_cost"] += cost
        roi = r.get("整体支付ROI")
        if roi is not None:
            product_data[prod]["total_roi"] += float(roi)
            product_data[prod]["count_roi"] += 1
    product_summary = [{"name": p, **s} for p, s in sorted(product_data.items(), key=lambda x: -x[1]["total_cost"])]

    # 返回包含AI分析字段的记录
    enriched = []
    for r in filtered[:50]:
        enriched.append({
            "record_id": r.get("record_id"),
            "视频名称": r.get("视频名称"),
            "产品名称": r.get("产品名称"),
            "视频消耗": r.get("视频消耗"),
            "整体支付ROI": r.get("整体支付ROI"),
            "完播率": r.get("完播率"),
            "采集时间": str(r.get("采集时间", "")) if r.get("采集时间") else "",
            "编导": r.get("编导"),
            "AI评分输出": r.get("AI评分输出", ""),
            "总结输出": r.get("总结输出", ""),
            "脚本类型标签": r.get("脚本类型标签", []),
            "五秒停留标签": r.get("五秒停留标签", []),
            "吸睛标签": r.get("吸睛标签", []),
            "转化理由标签": r.get("转化理由标签", []),
        })

    return {
        "total_records": total_records,
        "summary": {
            "total_cost": round(total_cost, 2),
            "avg_roi": round(avg_roi, 2),
            "avg_completion_rate": round(avg_comp_rate, 2),
            "avg_click_rate": round(sum(click_rates) / len(click_rates), 2) if click_rates else 0,
            "avg_conversion_rate": round(sum(conv_rates) / len(conv_rates), 2) if conv_rates else 0,
            "avg_net_roi": round(sum(net_roi_values) / len(net_roi_values), 2) if net_roi_values else 0,
            "avg_cpm": round(sum(cpm_values) / len(cpm_values), 2) if cpm_values else 0,
            "product_count": len(product_summary),
        },
        "product_stats": product_summary,
        "tag_stats": {
            "脚本类型标签": [{"name": k, "count": v} for k, v in sorted(script_tags.items(), key=lambda x: -x[1])[:10]],
            "五秒停留标签": [{"name": k, "count": v} for k, v in sorted(hook_tags.items(), key=lambda x: -x[1])[:10]],
            "吸睛标签": [{"name": k, "count": v} for k, v in sorted(appeal_tags.items(), key=lambda x: -x[1])[:10]],
            "转化理由标签": [{"name": k, "count": v} for k, v in sorted(reason_tags.items(), key=lambda x: -x[1])[:10]],
        },
        "records": enriched,
        "filter_options": filter_options,
        "active_filter": {"product": product or "", "director": director or ""},
    }


@router.get("/trend")
async def get_trend(
    field: str = Query("视频消耗", description="趋势字段"),
    days: int = Query(30, description="天数"),
    product: str = Query("", description="按产品筛选"),
    director: str = Query("", description="按编导筛选"),
):
    """获取指标趋势数据（支持筛选）"""
    records = _load_records(500)
    filtered = _apply_filters(records, product or None, director or None)

    daily = defaultdict(lambda: {"count": 0, "total": 0})
    for r in filtered:
        t = r.get("采集时间")
        if not t:
            continue
        date_key = t.strftime("%Y-%m-%d") if hasattr(t, "strftime") else str(t)[:10]
        val = r.get(field)
        if val is not None:
            try:
                daily[date_key]["total"] += float(val)
                daily[date_key]["count"] += 1
            except (ValueError, TypeError):
                pass

    trend_data = [
        {"date": k, "value": round(v["total"] / v["count"], 2) if v["count"] else 0}
        for k, v in sorted(daily.items())[-days:]
    ]
    return {"field": field, "trend": trend_data}


@router.get("/videos")
async def get_videos(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    sort_by: str = Query("采集时间", description="排序字段"),
    sort_desc: bool = Query(True, description="是否降序"),
    product: str = Query("", description="按产品筛选"),
    director: str = Query("", description="按编导筛选"),
):
    """获取视频列表（支持按产品/编导筛选）"""
    sort_str = f"{sort_by} {'desc' if sort_desc else 'asc'}"
    fetch_size = max(page * page_size, 500)
    records = feishu_service.query_records("main", sorts=[sort_str], max_records=fetch_size)
    filter_options = _extract_filter_options(records)

    filtered = _apply_filters(records, product or None, director or None)
    total = len(filtered)
    start = (page - 1) * page_size
    end = start + page_size
    page_records = filtered[start:end]

    simplified = []
    for r in page_records:
        simplified.append({
            "record_id": r.get("record_id"),
            "视频名称": r.get("视频名称"),
            "产品名称": r.get("产品名称"),
            "视频消耗": r.get("视频消耗"),
            "整体支付ROI": r.get("整体支付ROI"),
            "完播率": r.get("完播率"),
            "2秒播放率": r.get("2秒播放率"),
            "3秒播放率": r.get("3秒播放率"),
            "整体点击率": r.get("整体点击率(%)"),
            "整体转化率": r.get("整体转化率(%)"),
            "千次展现费用": r.get("千次展现费用"),
            "净成交ROI": r.get("净成交ROI"),
            "采集时间": str(r.get("采集时间", "")) if r.get("采集时间") else "",
            "编导": r.get("编导"),
            "剪辑": r.get("剪辑"),
            "时长": r.get("时长"),
            "品牌": r.get("品牌"),
            "AI评分输出": r.get("AI评分输出", ""),
            "最终总结": r.get("总结输出", ""),
            "脚本类型标签": r.get("脚本类型标签", []),
            "五秒停留标签": r.get("五秒停留标签", []),
            "吸睛标签": r.get("吸睛标签", []),
            "转化理由标签": r.get("转化理由标签", []),
        })

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": simplified,
        "filter_options": filter_options,
    }


@router.get("/videos/{record_id}")
async def get_video_detail(record_id: str):
    """获取单条视频的详细数据（含全部AI分析字段）"""
    records = feishu_service.get_records("main", [record_id])
    if not records:
        return {"error": "未找到该记录"}
    return records[0]


@router.get("/videos/{record_id}/full")
async def get_video_full_detail(record_id: str):
    """获取单条视频的完整原始数据"""
    records = feishu_service.get_records("main", [record_id])
    if not records:
        return {"error": "未找到该记录"}
    record = records[0]
    # 将所有非dict/list的值转为字符串（处理datetime等问题）
    def safe_val(v):
        if isinstance(v, (str, int, float, bool, type(None))):
            return v
        if isinstance(v, (list, dict)):
            return v
        return str(v)
    safe_record = {k: safe_val(v) for k, v in record.items()}
    ai_fields = {}
    for k, v in safe_record.items():
        if any(keyword in k for keyword in ["AI", "分析", "总结", "评分", "拆解", "标签", "脚本", "输出", "人群"]):
            ai_fields[k] = v
    return {
        "basic": {k: v for k, v in safe_record.items() if k not in ai_fields and k != "record_id"},
        "ai_analysis": ai_fields,
        "record_id": safe_record.get("record_id"),
    }


@router.get("/products")
async def get_product_stats():
    """获取产品维度的统计分析"""
    records = feishu_service.query_records("main", sorts=["视频消耗 desc"], max_records=500)
    product_data = defaultdict(lambda: {"count": 0, "total_cost": 0, "total_roi": 0, "count_roi": 0, "completion_rates": [], "videos": []})
    for r in records:
        prod = r.get("产品名称", "未知") or "未知"
        d = product_data[prod]
        d["count"] += 1
        d["total_cost"] += float(r.get("视频消耗", 0) or 0)
        roi = r.get("整体支付ROI")
        if roi is not None:
            d["total_roi"] += float(roi)
            d["count_roi"] += 1
        cr = r.get("完播率")
        if cr is not None:
            d["completion_rates"].append(float(cr))
        d["videos"].append(r.get("视频名称", ""))

    result = []
    for prod, d in sorted(product_data.items(), key=lambda x: -x[1]["total_cost"]):
        avg_cr = sum(d["completion_rates"]) / len(d["completion_rates"]) if d["completion_rates"] else 0
        result.append({
            "name": prod,
            "count": d["count"],
            "total_cost": round(d["total_cost"], 2),
            "avg_roi": round(d["total_roi"] / d["count_roi"], 2) if d["count_roi"] else 0,
            "avg_completion_rate": round(avg_cr, 2),
            "video_samples": d["videos"][:5],
        })
    return {"products": result}

