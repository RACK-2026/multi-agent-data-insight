"""
Agent管理 API 路由
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sqlalchemy import func, case

from app.agents.orchestrator import orchestrator
from app.services.feishu_service import feishu_service
from app.services.prompt_manager import prompt_manager

router = APIRouter()


class AnalyzeRequest(BaseModel):
    """单条分析请求"""
    record_id: str = ""


class BatchAnalyzeRequest(BaseModel):
    """批量分析请求"""
    limit: int = 10
    record_ids: list[str] = []


@router.post("/analyze")
async def analyze_video(req: AnalyzeRequest):
    """分析单条视频"""
    if not req.record_id:
        # 获取最新一条记录
        records = feishu_service.query_records("main", sorts=["采集时间 desc"], max_records=1)
        if not records:
            raise HTTPException(400, "无可用数据")
        record = records[0]
        record["record_id"] = record.get("record_id", "")
    else:
        records = feishu_service.get_records("main", [req.record_id])
        if not records:
            raise HTTPException(404, "未找到该记录")
        record = records[0]

    result = await orchestrator.analyze_video(record)
    return result


@router.post("/analyze/batch")
async def batch_analyze(req: BatchAnalyzeRequest):
    """批量分析视频（含审核闭环）"""
    if req.record_ids:
        records = feishu_service.get_records("main", req.record_ids)
    else:
        records = feishu_service.query_records("main", sorts=["采集时间 desc"], max_records=req.limit)

    if not records:
        raise HTTPException(400, "无可用数据")

    # 补充record_id
    for r in records:
        if "record_id" not in r:
            r["record_id"] = ""

    result = await orchestrator.full_analysis({"records": records})
    return result


@router.get("/review/status")
async def get_review_status():
    """获取各Agent的审核状态和提示词版本信息"""
    agents = prompt_manager.load_all_prompts()
    return {"agents": agents}


@router.post("/review/trigger")
async def trigger_review():
    """触发全量审核+优化闭环"""
    # 获取最近的分析结果（从数据库读取）
    from app.database import db_service, AgentLog
    with db_service.get_session() as session:
        logs = session.query(AgentLog).filter_by(
            status="success"
        ).order_by(AgentLog.id.desc()).limit(20).all()

    # 构建审核数据
    agent_outputs = []
    for log in logs:
        agent_outputs.append({
            "agent_name": log.agent_name,
            "output": {"summary": log.output_summary},
            "data_summary": log.input_summary,
        })

    result = await orchestrator.review_and_optimize({
        "agent_outputs": agent_outputs,
        "new_data_features": "",
    })
    return result


@router.get("/prompts")
async def get_all_prompts():
    """获取所有Agent的提示词信息"""
    agents = prompt_manager.load_all_prompts()

    # 扩展每个Agent的分析维度说明
    dimension_map = {
        "content_analyzer": {"name": "内容分析Agent", "dimensions": ["脚本结构类型", "前5秒留存分析", "卖点分析", "转化引导", "画面吸睛方式", "用户标签分布"]},
        "creative_analyzer": {"name": "创意拆解Agent", "dimensions": ["千川创意元素拆解", "卖点点击顺序", "脚本结构转化引导", "转化理由提取"]},
        "scoring_agent": {"name": "评分总结Agent", "dimensions": ["内容质量评分", "转化力评分", "留存力评分", "综合评分", "优缺点分析", "优化建议"]},
        "consumption_agent": {"name": "高低消耗分析Agent", "dimensions": ["消耗级别判断", "高消耗特征提取", "低消耗特征提取", "完播率分析", "转化分析", "优化方向"]},
        "review_agent": {"name": "审核Agent", "dimensions": ["一致性评分", "有价值度评分", "完整性评分", "清晰度评分", "综合评分", "优化建议"]},
        "prompt_optimizer": {"name": "提示词优化Agent", "dimensions": ["提示词分析", "优化版本生成", "变更说明", "预期改善分析"]},
    }

    extended = {}
    for key, info in agents.items():
        dim_info = dimension_map.get(key, {"name": key, "dimensions": []})
        extended[key] = {
            **info,
            "display_name": dim_info["name"],
            "analysis_dimensions": dim_info["dimensions"],
        }

    return {"agents": extended}


@router.get("/prompts/{agent_name}")
async def get_prompt_detail(agent_name: str):
    """获取指定Agent的提示词详情"""
    prompt = prompt_manager.get_active_prompt(agent_name)
    if not prompt:
        raise HTTPException(404, f"未找到Agent: {agent_name}")

    # 解析analysis_dimensions并展开system_prompt的关键部分
    system_prompt = prompt.get("system_prompt", "")
    # 提取分析维度列表（按行分割）
    lines = [l.strip() for l in system_prompt.split("\n") if l.strip() and any(c.isalpha() for c in l)]

    return {
        "agent": agent_name,
        "prompt": prompt,
        "preview": {
            "system_summary": system_prompt[:200] + "..." if len(system_prompt) > 200 else system_prompt,
            "total_lines": len(lines),
            "has_json_output": "JSON" in system_prompt or "json" in system_prompt,
        },
    }


@router.get("/logs")
async def get_agent_logs(limit: int = 50):
    """获取Agent执行日志"""
    from app.database import db_service, AgentLog
    with db_service.get_session() as session:
        logs = session.query(AgentLog).order_by(
            AgentLog.id.desc()
        ).limit(limit).all()

    return {
        "logs": [
            {
                "id": log.id,
                "agent": log.agent_name,
                "record_id": log.record_id,
                "status": log.status,
                "duration_ms": log.duration_ms,
                "input": log.input_summary,
                "output": log.output_summary,
                "error": log.error,
                "time": str(log.created_at),
            }
            for log in logs
        ]
    }


@router.get("/stats")
async def get_agent_stats():
    """获取各Agent的聚合统计（供管理层查看）"""
    from app.database import db_service, AgentLog
    from sqlalchemy import func
    with db_service.get_session() as session:
        rows = session.query(
            AgentLog.agent_name,
            func.count(AgentLog.id),
            func.sum(AgentLog.duration_ms),
            func.sum(case((AgentLog.status == "success", 1), else_=0)),
        ).group_by(AgentLog.agent_name).all()

    agent_names = {
        "content_analyzer": "内容分析",
        "creative_analyzer": "创意拆解",
        "scoring_agent": "评分总结",
        "consumption_agent": "消耗分析",
        "review_agent": "审核",
        "prompt_optimizer": "提示词优化",
        "script_generator": "脚本生成",
    }

    stats = []
    for name, count, total_ms, success_count in rows:
        success_rate = round(success_count / count * 100, 1) if count else 0
        avg_ms = round(total_ms / count) if count else 0
        stats.append({
            "agent": name,
            "display_name": agent_names.get(name, name),
            "total_runs": count,
            "success_runs": success_count,
            "failed_runs": count - success_count,
            "success_rate": success_rate,
            "avg_duration_ms": avg_ms,
            "avg_duration_sec": round(avg_ms / 1000, 1),
        })

    return {"stats": stats}

