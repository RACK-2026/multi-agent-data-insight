"""
复盘报告 API 路由
从千川复盘表获取数据，提供周期性的数据汇总和分析
"""
from collections import defaultdict
from fastapi import APIRouter, Query
from app.services.feishu_service import feishu_service

router = APIRouter()


@router.get("/summary")
async def get_review_summary():
    """获取复盘汇总指标"""
    records = feishu_service.query_records(
        "review",
        sorts=["采集时间 desc"],
        max_records=1000,
    )
    if not records:
        return {"total": 0, "summary": {}}

    total = len(records)
    total_cost = sum(float(r.get("视频消耗", 0) or 0) for r in records)
    total_rois = [float(r.get("整体支付ROI", 0) or 0) for r in records if r.get("整体支付ROI")]
    avg_roi = sum(total_rois) / len(total_rois) if total_rois else 0

    click_rates = [float(r.get("整体点击率(%)", 0) or 0) for r in records if r.get("整体点击率(%)")]
    conv_rates = [float(r.get("整体转化率(%)", 0) or 0) for r in records if r.get("整体转化率(%)")]

    # 脚本类型统计
    script_types = defaultdict(int)
    for r in records:
        tags = r.get("脚本结构【标签】", [])
        if isinstance(tags, list):
            for t in tags:
                script_types[t] += 1

    # 前3秒标签统计
    hook_tags = defaultdict(int)
    for r in records:
        tags = r.get("标签【前三秒】", [])
        if isinstance(tags, list):
            for t in tags:
                hook_tags[t] += 1

    # 画面吸睛标签
    visual_tags = defaultdict(int)
    for r in records:
        tags = r.get("画面吸睛标签", [])
        if isinstance(tags, list):
            for t in tags:
                visual_tags[t] += 1

    return {
        "total": total,
        "summary": {
            "total_cost": round(total_cost, 2),
            "avg_roi": round(avg_roi, 2),
            "avg_click_rate": round(sum(click_rates) / len(click_rates), 2) if click_rates else 0,
            "avg_conversion_rate": round(sum(conv_rates) / len(conv_rates), 2) if conv_rates else 0,
        },
        "script_type_stats": dict(sorted(script_types.items(), key=lambda x: -x[1])),
        "hook_tag_stats": dict(sorted(hook_tags.items(), key=lambda x: -x[1])),
        "visual_tag_stats": dict(sorted(visual_tags.items(), key=lambda x: -x[1])),
    }


@router.get("/top")
async def get_review_top(
    limit: int = Query(10, ge=1, le=50),
    sort_by: str = Query("视频消耗", description="排序字段"),
):
    """获取复盘表中的Top视频"""
    sort_str = f"{sort_by} desc"
    records = feishu_service.query_records(
        "review",
        sorts=[sort_str],
        max_records=limit,
    )

    items = []
    for r in records:
        items.append({
            "record_id": r.get("record_id", ""),
            "视频名称": r.get("视频名称", ""),
            "产品名称": r.get("产品名称", ""),
            "视频消耗": r.get("视频消耗"),
            "整体支付ROI": r.get("整体支付ROI"),
            "整体点击率": r.get("整体点击率(%)"),
            "整体转化率": r.get("整体转化率(%)"),
            "千次展现费用": r.get("千次展现费用"),
            "采集时间": str(r.get("采集时间", "")) if r.get("采集时间") else "",
            "脚本结构类型": r.get("脚本结构类型.输出结果", ""),
            "AI评分": r.get("AI评分.输出结果", ""),
            "最终总结": r.get("最终总结.输出结果", ""),
        })

    return {"sort_by": sort_by, "items": items}


@router.get("/trend")
async def get_review_trend(
    field: str = Query("视频消耗", description="趋势字段"),
    days: int = Query(30, ge=1, le=90),
):
    """获取复盘数据趋势"""
    records = feishu_service.query_records(
        "review",
        sorts=["采集时间 desc"],
        max_records=500,
    )

    daily = defaultdict(lambda: {"count": 0, "total": 0})
    for r in records:
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

    trend = [
        {"date": k, "value": round(v["total"] / v["count"], 2) if v["count"] else 0}
        for k, v in sorted(daily.items())[-days:]
    ]

    # 计算环比
    if len(trend) >= 2:
        prev = trend[-2]["value"]
        curr = trend[-1]["value"]
        change = round((curr - prev) / prev * 100, 1) if prev else 0
    else:
        change = 0

    return {"field": field, "trend": trend, "change_percent": change}


@router.get("/tags")
async def get_review_tags():
    """获取所有标签的汇总统计（用于词云/分布图）"""
    records = feishu_service.query_records(
        "review",
        sorts=["采集时间 desc"],
        max_records=1000,
    )

    tag_groups = {
        "脚本结构": defaultdict(int),
        "前三秒": defaultdict(int),
        "画面吸睛": defaultdict(int),
        "卖点排序": defaultdict(int),
        "尾部引导": defaultdict(int),
        "尾部转化": defaultdict(int),
    }

    for r in records:
        for tag in (r.get("脚本结构【标签】") or []):
            if isinstance(tag, str):
                tag_groups["脚本结构"][tag] += 1
        for tag in (r.get("标签【前三秒】") or []):
            if isinstance(tag, str):
                tag_groups["前三秒"][tag] += 1
        for tag in (r.get("画面吸睛标签") or []):
            if isinstance(tag, str):
                tag_groups["画面吸睛"][tag] += 1
        for tag in (r.get("卖点排序【标签】") or []):
            if isinstance(tag, str):
                tag_groups["卖点排序"][tag] += 1
        for tag in (r.get("标签【尾部引导】") or []):
            if isinstance(tag, str):
                tag_groups["尾部引导"][tag] += 1
        for tag in (r.get("尾部转化标签") or []):
            if isinstance(tag, str):
                tag_groups["尾部转化"][tag] += 1

    result = {}
    for group, tags in tag_groups.items():
        sorted_tags = sorted(tags.items(), key=lambda x: -x[1])
        result[group] = [{"name": k, "count": v} for k, v in sorted_tags]

    return {"tag_groups": result}


@router.get("/ai-analysis")
async def get_review_ai_analysis(limit: int = Query(20, ge=1, le=50)):
    """获取复盘表中的AI分析结果汇总"""
    records = feishu_service.query_records(
        "review",
        sorts=["采集时间 desc"],
        max_records=limit,
    )

    items = []
    for r in records:
        items.append({
            "record_id": r.get("record_id", ""),
            "视频名称": r.get("视频名称", ""),
            "产品名称": r.get("产品名称", ""),
            "视频消耗": r.get("视频消耗"),
            "整体支付ROI": r.get("整体支付ROI"),
            "AI内容分析": r.get("AI内容分析.输出结果", ""),
            "脚本结构": r.get("脚本结构类型.输出结果", ""),
            "最终总结": r.get("最终总结.输出结果", ""),
            "AI评分": r.get("AI评分.输出结果", ""),
            "AI云文档": r.get("AI 创建飞书云文档", ""),
            "采集时间": str(r.get("采集时间", "")) if r.get("采集时间") else "",
        })

    return {"items": items}


@router.get("/daily-report")
async def get_daily_report(
    start_date: str = Query("", description="开始日期 YYYY-MM-DD"),
    end_date: str = Query("", description="结束日期 YYYY-MM-DD"),
):
    """获取每日数据分析报告（基于主表数据，支持日期范围选择）"""
    from datetime import datetime, timedelta

    def parse_date(v):
        """统一日期解析：支持datetime/字符串/时间戳"""
        if not v:
            return None
        if hasattr(v, "strftime"):
            return v.strftime("%Y-%m-%d")
        if isinstance(v, (int, float)):
            # 飞书时间戳是毫秒
            try:
                return datetime.fromtimestamp(v / 1000).strftime("%Y-%m-%d")
            except Exception:
                return None
        s = str(v).strip()
        # 尝试各种日期格式
        for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%Y年%m月%d日", "%m-%d-%Y", "%m/%d/%Y"):
            try:
                return datetime.strptime(s[:10], fmt).strftime("%Y-%m-%d")
            except ValueError:
                continue
        # 最后尝试提取数字
        import re
        nums = re.findall(r"\d+", s)
        if len(nums) >= 3:
            return f"{nums[0]}-{nums[1].zfill(2)}-{nums[2].zfill(2)}"
        return None

    records = feishu_service.query_records("main", sorts=["采集时间 desc"], max_records=500)
    if not records:
        return {"total": 0, "days": [], "summary": {}}

    # 按日期聚合
    daily_data = defaultdict(lambda: {
        "videos": [], "total_cost": 0, "rois": [], "completions": [],
        "click_rates": [], "conv_rates": [], "products": defaultdict(int),
        "directors": defaultdict(int),
    })

    for r in records:
        date_key = parse_date(r.get("采集时间"))
        if not date_key:
            continue
        daily_data[date_key]["videos"].append(r)
        daily_data[date_key]["total_cost"] += float(r.get("视频消耗", 0) or 0)
        roi = r.get("整体支付ROI")
        if roi is not None:
            daily_data[date_key]["rois"].append(float(roi))
        cr = r.get("完播率")
        if cr is not None:
            daily_data[date_key]["completions"].append(float(cr))
        ctr = r.get("整体点击率(%)")
        if ctr is not None:
            daily_data[date_key]["click_rates"].append(float(ctr))
        cvr = r.get("整体转化率(%)")
        if cvr is not None:
            daily_data[date_key]["conv_rates"].append(float(cvr))
        prod = r.get("产品名称", "") or "未填写"
        daily_data[date_key]["products"][prod] += 1
        director = r.get("编导", "") or "未填写编导名称"
        daily_data[date_key]["directors"][director] += 1

    # 筛选日期范围
    sorted_dates = sorted(daily_data.keys())
    if start_date:
        sorted_dates = [d for d in sorted_dates if d >= start_date]
    if end_date:
        sorted_dates = [d for d in sorted_dates if d <= end_date]

    # 构建每日报告
    days_report = []
    for date_str in sorted_dates:
        dd = daily_data[date_str]
        rois = dd["rois"]
        completions = dd["completions"]
        days_report.append({
            "date": date_str,
            "video_count": len(dd["videos"]),
            "total_cost": round(dd["total_cost"], 2),
            "avg_roi": round(sum(rois) / len(rois), 2) if rois else 0,
            "avg_completion": round(sum(completions) / len(completions), 4) if completions else 0,
            "avg_click_rate": round(sum(dd["click_rates"]) / len(dd["click_rates"]), 2) if dd["click_rates"] else 0,
            "avg_conversion": round(sum(dd["conv_rates"]) / len(dd["conv_rates"]), 2) if dd["conv_rates"] else 0,
            "top_products": sorted(dd["products"].items(), key=lambda x: -x[1])[:5],
            "top_directors": sorted(dd["directors"].items(), key=lambda x: -x[1])[:5],
        })

    # 计算汇总（基于有日期的记录）
    total_cost = sum(d["total_cost"] for d in days_report)
    total_videos = sum(d["video_count"] for d in days_report)
    all_roi_vals = []
    for dd in days_report:
        # 从原始数据重新收集roi
        for r in daily_data.get(dd["date"], {}).get("rois", []):
            all_roi_vals.append(r)

    change = None
    if len(days_report) >= 2:
        prev = days_report[-2]
        curr = days_report[-1]
        change = {
            "cost_change": round(curr["total_cost"] - prev["total_cost"], 2),
            "roi_change": round(curr["avg_roi"] - prev["avg_roi"], 2),
            "cost_change_pct": round((curr["total_cost"] - prev["total_cost"]) / prev["total_cost"] * 100, 1) if prev["total_cost"] else 0,
        }

    return {
        "total": len(days_report),
        "days": days_report,
        "summary": {
            "total_cost": round(total_cost, 2),
            "total_videos": total_videos,
            "avg_roi": round(sum(all_roi_vals) / len(all_roi_vals), 2) if all_roi_vals else 0,
            "avg_daily_videos": round(total_videos / len(days_report), 1) if days_report else 0,
            "avg_daily_cost": round(total_cost / len(days_report), 2) if days_report else 0,
        },
        "change": change,
    }

