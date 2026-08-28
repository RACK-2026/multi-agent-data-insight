"""
智能优化建议 API 路由
基于数据分析和Agent分析结果，提供可操作的优化建议
"""
from collections import defaultdict
from fastapi import APIRouter
from app.services.feishu_service import feishu_service

router = APIRouter()


@router.get("/summary")
async def get_optimization_summary():
    """获取优化建议汇总"""
    records = feishu_service.query_records(
        "main",
        sorts=["视频消耗 desc"],
        max_records=500,
    )

    if not records:
        return {"total": 0, "suggestions": []}

    # 高低消耗分组（前20% vs 后20%）
    sorted_by_cost = sorted(records, key=lambda r: float(r.get("视频消耗", 0) or 0), reverse=True)
    threshold = max(len(sorted_by_cost) // 5, 1)
    high_cost = sorted_by_cost[:threshold]
    low_cost = sorted_by_cost[-threshold:] if threshold < len(sorted_by_cost) else []

    high_features = extract_features(high_cost, "高消耗")
    low_features = extract_features(low_cost, "低消耗")

    # 产品分析
    product_perf = defaultdict(lambda: {"count": 0, "total_cost": 0, "total_roi": 0, "count_roi": 0, "completions": [], "videos": []})
    for r in records:
        prod = r.get("产品名称", "未知") or "未知"
        p = product_perf[prod]
        p["count"] += 1
        p["total_cost"] += float(r.get("视频消耗", 0) or 0)
        roi = r.get("整体支付ROI")
        if roi is not None:
            p["total_roi"] += float(roi)
            p["count_roi"] += 1
        cr = r.get("完播率")
        if cr is not None:
            p["completions"].append(float(cr))
        p["videos"].append(r.get("视频名称", ""))

    # 编导分析
    director_perf = defaultdict(lambda: {"count": 0, "total_cost": 0, "total_roi": 0, "count_roi": 0, "completions": []})
    for r in records:
        d = r.get("编导", "") or "未填写编导名称"
        if d == "未填写编导名称":
            continue
        dp = director_perf[d]
        dp["count"] += 1
        dp["total_cost"] += float(r.get("视频消耗", 0) or 0)
        roi = r.get("整体支付ROI")
        if roi is not None:
            dp["total_roi"] += float(roi)
            dp["count_roi"] += 1
        cr = r.get("完播率")
        if cr is not None:
            dp["completions"].append(float(cr))

    suggestions = []

    # ====== 1. 总览级建议（管理层关注） ======
    total_cost = sum(float(r.get("视频消耗", 0) or 0) for r in records)
    roi_values = [float(r.get("整体支付ROI", 0) or 0) for r in records if r.get("整体支付ROI")]
    avg_roi = sum(roi_values) / len(roi_values) if roi_values else 0

    # ROI健康度
    low_roi_count = sum(1 for r in records if r.get("整体支付ROI") is not None and float(r.get("整体支付ROI", 0)) < 1)
    roi_health = round((1 - low_roi_count / len(roi_values)) * 100, 1) if roi_values else 0
    suggestions.append({
        "category": "总览",
        "title": f"ROI健康度 {roi_health}% — {low_roi_count}/{len(roi_values)} 条视频ROI低于1",
        "detail": f"大盘整体ROI {avg_roi:.1f}，总消耗 {total_cost:.0f}。低于1的产品需要注意：",
        "priority": "high",
        "metric": f"ROI<1占比 {100-roi_health:.1f}%",
    })

    # ====== 2. 产品级建议（管理层 + 编导） ======
    for prod, p in product_perf.items():
        avg_roi_p = p["total_roi"] / p["count_roi"] if p["count_roi"] else 0
        avg_cr = sum(p["completions"]) / len(p["completions"]) if p["completions"] else 0
        if p["count"] < 3:
            continue
        if avg_roi_p < 1.0 or avg_cr < 0.3:
            top_videos = p["videos"][:3]
            suggestions.append({
                "category": "产品策略",
                "title": f"产品「{prod}」表现不佳（ROI {avg_roi_p:.1f}，完播率 {avg_cr:.1%}）",
                "detail": f"共 {p['count']} 条视频，总消耗 {p['total_cost']:.0f}。参考视频：{'、'.join(top_videos)}。建议：① 重新评估目标人群定向 ② 测试不同脚本类型（痛点/场景/背书）③ 控制时长在30s以内提升完播率",
                "priority": "high" if avg_roi_p < 1 else "medium",
                "metric": f"ROI {avg_roi_p:.1f} / 完播 {avg_cr:.1%}",
            })
        elif avg_roi_p >= 2.0:
            suggestions.append({
                "category": "产品策略",
                "title": f"产品「{prod}」表现优秀（ROI {avg_roi_p:.1f}）",
                "detail": f"共 {p['count']} 条视频，总消耗 {p['total_cost']:.0f}。建议：① 加大该产品的投放预算 ② 复制优秀素材风格 ③ 测试更多人群包扩展",
                "priority": "low",
                "metric": f"ROI {avg_roi_p:.1f}",
            })

    # ====== 3. 完播率分析（编导关注） ======
    comp_records = [(r, float(r.get("完播率", 0) or 0)) for r in records if r.get("完播率") is not None]
    if comp_records:
        avg_comp = sum(cr for _, cr in comp_records) / len(comp_records)
        low_comp = [(r, cr) for r, cr in comp_records if cr < 0.25]
        if low_comp:
            low_names = [r.get("视频名称", "")[:20] for r, _ in low_comp[:5]]
            suggestions.append({
                "category": "内容策略",
                "title": f"完播率偏低：{len(low_comp)} 条视频完播率低于25%",
                "detail": f"大盘平均完播率 {avg_comp:.1%}。低完播视频：{'、'.join(low_names)}。建议编导：① 前3秒必须出现核心卖点/痛点 ② 减少铺垫，直接切入 ③ 用【提问钩子+痛点共鸣】代替平铺直叙",
                "priority": "high",
                "metric": f"平均 {avg_comp:.1%} / 最低 {min(cr for _, cr in low_comp):.1%}",
            })

    # ====== 4. 时长策略（编导关注） ======
    dur_records = [(r, float(r.get("时长", 0) or 0)) for r in records if r.get("时长")]
    if dur_records:
        avg_dur = sum(d for _, d in dur_records) / len(dur_records)
        high_comp_records = [r for r in records if r.get("完播率") is not None and float(r.get("完播率", 0) or 0) > 0.5]
        if high_comp_records:
            high_comp_durs = [float(r.get("时长", 0) or 0) for r in high_comp_records if r.get("时长")]
            best_dur = round(sum(high_comp_durs) / len(high_comp_durs)) if high_comp_durs else round(avg_dur)
            suggestions.append({
                "category": "内容策略",
                "title": f"建议视频时长控制在 {best_dur}s 左右",
                "detail": f"大盘平均时长 {avg_dur:.0f}s，高完播率(>50%)视频平均时长 {best_dur}s。建议编导：① 前10秒集中展示最大卖点 ② 去掉冗余铺垫，3秒内进主题 ③ 如需长视频，确保每15秒有一次信息/视觉刺激",
                "priority": "medium",
                "metric": f"最佳 {best_dur}s / 平均 {avg_dur:.0f}s",
            })

    # ====== 5. 编导绩效（管理层关注） ======
    if director_perf:
        best = max(director_perf.items(), key=lambda x: x[1]["total_roi"] / x[1]["count_roi"] if x[1]["count_roi"] else 0)
        best_roi = best[1]["total_roi"] / best[1]["count_roi"] if best[1]["count_roi"] else 0
        best_cr = sum(best[1]["completions"]) / len(best[1]["completions"]) if best[1]["completions"] else 0

        worst = min(director_perf.items(), key=lambda x: x[1]["total_roi"] / x[1]["count_roi"] if x[1]["count_roi"] else float('inf'))
        worst_roi = worst[1]["total_roi"] / worst[1]["count_roi"] if worst[1]["count_roi"] else 0

        suggestions.append({
            "category": "团队分析",
            "title": f"最佳编导「{best[0]}」ROI {best_roi:.1f}，建议总结其脚本风格",
            "detail": f"{best[0]} 共出 {best[1]['count']} 条视频，总消耗 {best[1]['total_cost']:.0f}，平均完播率 {best_cr:.1%}。建议：① 将该编导的脚本作为团队模板 ② 分析其前3秒钩子方式和画面风格 ③ 组织内部分享",
            "priority": "low",
            "metric": f"ROI {best_roi:.1f} / 完播 {best_cr:.1%}",
        })

        if worst[0] != best[0] and worst[1]["count"] >= 3:
            suggestions.append({
                "category": "团队分析",
                "title": f"编导「{worst[0]}」ROI {worst_roi:.1f}，需重点优化",
                "detail": f"{worst[0]} 共出 {worst[1]['count']} 条视频，总消耗 {worst[1]['total_cost']:.0f}。建议：① 复盘其近3条视频的脚本和画面 ② 参考最佳编导的创作方式 ③ 短期聚焦1-2个产品测试新方向",
                "priority": "medium",
                "metric": f"ROI {worst_roi:.1f}",
            })

    # 优先级排序
    priority_order = {"high": 0, "medium": 1, "low": 2}
    suggestions.sort(key=lambda s: priority_order.get(s["priority"], 99))

    # AI评分
    ai_scores = []
    for r in records:
        score_field = r.get("AI评分输出", "")
        if score_field:
            try:
                ai_scores.append(float(score_field))
            except (ValueError, TypeError):
                pass

    return {
        "total": len(records),
        "suggestions": suggestions,
        "high_cost_count": len(high_cost),
        "low_cost_count": len(low_cost),
        "high_cost_features": high_features,
        "low_cost_features": low_features,
        "ai_score_avg": round(sum(ai_scores) / len(ai_scores), 1) if ai_scores else None,
    }


def extract_features(records: list, label: str) -> dict:
    """提取一组视频的共性特征"""
    costs = [float(r.get("视频消耗", 0) or 0) for r in records]
    durations = [float(r.get("时长", 0) or 0) for r in records if r.get("时长")]
    completions = [float(r.get("完播率", 0) or 0) for r in records if r.get("完播率")]
    rois = [float(r.get("整体支付ROI", 0) or 0) for r in records if r.get("整体支付ROI")]
    click_rates = [float(r.get("整体点击率(%)", 0) or 0) for r in records if r.get("整体点击率(%)")]

    products = defaultdict(int)
    for r in records:
        p = r.get("产品名称", "未知") or "未知"
        products[p] += 1

    directors = defaultdict(int)
    for r in records:
        d = r.get("编导", "") or "未填写编导名称"
        directors[d] += 1

    return {
        "label": label,
        "count": len(records),
        "avg_cost": round(sum(costs) / len(costs), 2) if costs else 0,
        "avg_duration": round(sum(durations) / len(durations), 1) if durations else 0,
        "avg_completion": round(sum(completions) / len(completions), 4) if completions else 0,
        "avg_roi": round(sum(rois) / len(rois), 2) if rois else 0,
        "avg_click_rate": round(sum(click_rates) / len(click_rates), 2) if click_rates else 0,
        "top_products": [{"name": k, "count": v} for k, v in sorted(products.items(), key=lambda x: -x[1])[:3]],
        "top_directors": [{"name": k, "count": v} for k, v in sorted(directors.items(), key=lambda x: -x[1])[:3]],
    }

