"""
千川数据多Agent联动分析平台 - FastAPI主入口
"""
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from app.config import settings
from app.routers import dashboard, agents, review, optimization, scripts, import_scripts, titles, workshop, products
from app.services.feishu_service import feishu_service
from app.services.llm_service import llm_service


# 前端静态文件目录（构建后的）
FRONTEND_DIR = Path(__file__).resolve().parent.parent / "web" / "dist"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    print(f"[启动] {settings.APP_NAME} v{settings.APP_VERSION}")
    print(f"[启动] 飞书Bitable连接状态: {'OK' if feishu_service.get_table('main') else '失败'}")
    print(f"[启动] LLM服务状态: {'可用' if llm_service.is_available() else '未配置（请设置LLM_API_KEY）'}")
    if FRONTEND_DIR.exists():
        print(f"[启动] 前端页面: http://localhost:{settings.PORT}/")
    else:
        print(f"[启动] 前端未构建，请 cd web && npm install && npm run build")
    yield
    print("[关闭] 应用停止")


app = FastAPI(
    title=settings.APP_NAME + "【测试版】",
    version=settings.APP_VERSION,
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# SPA中间件：API返回404时，尝试返回前端index.html
if FRONTEND_DIR.exists():
    INDEX_HTML = (FRONTEND_DIR / "index.html").read_text(encoding="utf-8")

    @app.middleware("http")
    async def spa_fallback(request: Request, call_next):
        path = request.url.path
        # API请求直接通过
        if path.startswith("/api/") or path.startswith("/docs") or path.startswith("/openapi"):
            return await call_next(request)

        # 先检查是否是静态资源
        if path.startswith("/assets/"):
            static_path = FRONTEND_DIR / path.lstrip("/")
            if static_path.exists():
                from starlette.responses import FileResponse
                return FileResponse(str(static_path))
            # assets找不到也回退到SPA
            return HTMLResponse(INDEX_HTML)

        # 其他路径：先尝试调用API，404则返回前端页面
        response = await call_next(request)
        if response.status_code == 404 and response.headers.get("content-type", "").startswith("application/json"):
            return HTMLResponse(INDEX_HTML)
        return response


# 注册API路由（在中间件之前注册，确保API优先）
app.include_router(dashboard.router, prefix="/api/dashboard", tags=["数据看板"])
app.include_router(agents.router, prefix="/api/agents", tags=["Agent管理"])
app.include_router(review.router, prefix="/api/review", tags=["复盘报告"])
app.include_router(optimization.router, prefix="/api/optimization", tags=["优化建议"])
app.include_router(scripts.router, prefix="/api/scripts", tags=["脚本生成"])
app.include_router(import_scripts.router, prefix="/api/import", tags=["脚本导入"])
app.include_router(titles.router, prefix="/api/titles", tags=["标题生成"])
app.include_router(workshop.router, prefix="/api/workshop", tags=["创意工坊"])
app.include_router(products.router, prefix="/api/products", tags=["产品管理"])


@app.get("/api/health")
async def health():
    """健康检查接口"""
    return {
        "status": "ok",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "feishu": "connected" if feishu_service.get_table("main") else "disconnected",
        "llm": "configured" if llm_service.is_available() else "not_configured",
    }


# ============ 多Agent管理平台兼容接口 ============

@app.get("/api/self/health")
async def self_health():
    """供多Agent管理平台检测健康状况"""
    return await health()


@app.get("/api/self/info")
async def self_info():
    """供多Agent管理平台读取本服务信息"""
    import os, time
    return {
        "id": "qianchuan_agent",
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "host": "192.168.130.20",
        "port": settings.PORT,
        "role": "qianchuan_analyzer",
        "status": "online",
        "pid": os.getpid(),
        "workdir": str(Path(__file__).resolve().parent.parent),
        "uptime": time.time(),
        "capabilities": [
            "data_dashboard", "video_analysis", "script_generation",
            "script_import", "ai_agent_orchestration", "prompt_optimization",
        ],
        "feishu": "connected" if feishu_service.get_table("main") else "disconnected",
        "llm": "configured" if llm_service.is_available() else "not_configured",
    }


@app.post("/api/self/shutdown")
async def self_shutdown():
    """供多Agent管理平台关闭本服务（优雅退出）"""
    import asyncio, os, signal
    asyncio.get_event_loop().call_later(1, lambda: os.kill(os.getpid(), signal.SIGTERM))
    return {"status": "shutting_down", "pid": os.getpid()}


@app.get("/api/heartbeat")
async def heartbeat():
    """心跳检测接口（供其他Agent检测本服务状态）"""
    import time
    return {
        "status": "alive",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "port": settings.PORT,
        "feishu": "connected" if feishu_service.get_table("main") else "disconnected",
        "llm": "configured" if llm_service.is_available() else "not_configured",
        "timestamp": time.time(),
        "agent_type": "qianchuan_analyzer",
        "capabilities": [
            "data_dashboard",
            "video_analysis",
            "script_generation",
            "script_import",
            "ai_agent_orchestration",
            "prompt_optimization",
            "review_report",
        ],
    }


@app.get("/api/config")
async def get_config():
    """获取前端配置（不暴露敏感信息）"""
    return {
        "app_name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "llm_provider": settings.LLM_PROVIDER,
    }


@app.get("/manual.html")
async def get_manual():
    """返回员工使用手册"""
    from fastapi.responses import FileResponse
    manual_path = FRONTEND_DIR / "manual.html"
    if manual_path.exists():
        return FileResponse(str(manual_path), media_type="text/html")
    return HTMLResponse("<h1>手册文件未找到</h1>", status_code=404)

