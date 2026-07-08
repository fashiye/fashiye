import asyncio                                           # 提供异步任务管理，用于启动/停止后台日志清理任务
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.核心.配置 import 配置对象
from app.核心.异常 import 业务逻辑错误, 认证错误
from app.api.v1.端点 import 认证, 订单, 会话, 游戏, 用户, 数据库管理, 管理员管理, 支付
from app.服务.验证码服务 import 验证码服务对象
from app.服务.支付服务 import 支付服务对象
from app.核心.日志 import 初始化日志记录, 获取日志记录器, 启动定期日志清理
from app.数据库.会话 import 引擎, 数据库基类

初始化日志记录()
日志记录器 = 获取日志记录器(__name__)


@asynccontextmanager
async def 应用生命周期(app: FastAPI):
    """管理应用启动和关闭时的生命周期事件"""
    日志记录器.info("Application starting up...")

    # 调用库函数：创建所有未创建的表（如 payment_records）
    # 传入：数据库引擎（bind）
    # 作用：扫描所有继承自数据库基类的模型，在数据库中创建缺失的表
    # 传出：无返回值
    async with 引擎.begin() as 连接:
        await 连接.run_sync(数据库基类.metadata.create_all)
    日志记录器.info("Database tables synchronized")

    await 验证码服务对象.启动清理任务()
    日志记录器.info("Verification service cleanup task started")

    # 调用库函数：检测 iaitouzi 支付平台配置是否完整
    # 传入：无
    # 作用：检查应用 ID 和应用密钥配置是否完整
    # 传出：True=配置完整
    try:
        await 支付服务对象.自动初始化支付平台()
    except Exception as e:
        日志记录器.error(f"iaitouzi 支付平台配置检查失败: {e}")

    # 启动后台日志清理任务（每小时检查一次，压缩过期日志）
    日志清理任务 = asyncio.create_task(启动定期日志清理(
        Path(配置对象.日志目录),
        配置对象.日志归档天数
    ))

    yield
    日志记录器.info("Application shutting down...")
    # 取消后台日志清理任务
    日志清理任务.cancel()
    try:
        await 日志清理任务
    except asyncio.CancelledError:
        日志记录器.info("Log cleanup task cancelled")
    await 验证码服务对象.关闭()
    日志记录器.info("Application shutdown complete")


app = FastAPI(
    title=配置对象.项目名称,
    version=配置对象.版本号,
    debug=配置对象.调试模式,
    lifespan=应用生命周期
)

# CORS 配置
允许的来源 = 配置对象.允许的跨域来源
if 允许的来源 == "*":
    跨域来源列表 = ["*"]
else:
    跨域来源列表 = [origin.strip() for origin in 允许的来源.split(",")]

app.add_middleware(
    CORSMiddleware,
    allow_origins=跨域来源列表,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(认证.router, prefix="/api/v1", tags=["auth"])
app.include_router(订单.router, prefix="/api/v1", tags=["orders"])
app.include_router(会话.router, prefix="/api/v1", tags=["conversations"])
app.include_router(游戏.router, prefix="/api/v1", tags=["games"])
app.include_router(用户.router, prefix="/api/v1", tags=["users"])
app.include_router(数据库管理.router, prefix="/api/v1", tags=["database-admin"])
app.include_router(管理员管理.router, prefix="/api/v1", tags=["admin-management"])
app.include_router(支付.router, prefix="/api/v1", tags=["payment"])


@app.exception_handler(业务逻辑错误)
async def 业务错误处理器(request: Request, exc: 业务逻辑错误):
    """全局业务逻辑错误异常处理器"""
    日志记录器.warning(f"Business error: {exc.错误消息}", extra={
        "request_url": str(request.url),
        "request_method": request.method,
        "status_code": exc.状态码
    })
    return JSONResponse(
        status_code=exc.状态码,
        content={"code": exc.状态码, "message": exc.错误消息, "data": None}
    )


@app.exception_handler(认证错误)
async def 认证错误处理器(request: Request, exc: 认证错误):
    """全局认证错误异常处理器"""
    日志记录器.warning(f"Auth error: {exc.错误消息}", extra={
        "request_url": str(request.url),
        "request_method": request.method,
        "status_code": exc.状态码
    })
    return JSONResponse(
        status_code=exc.状态码,
        content={"code": exc.状态码, "message": exc.错误消息, "data": None}
    )


@app.get("/health")
async def 健康检查():
    return {"status": "ok"}


# ---------------------------------------------------------------------------
# 前端静态页面路由
# ---------------------------------------------------------------------------
静态文件目录 = Path(__file__).resolve().parent.parent / "static"
if 静态文件目录.exists():
    # 调用库函数：挂载静态文件目录到 /static 路径
    # 传入：目录路径，挂载前缀
    # 作用：让 FastAPI 能够直接提供 static/ 目录下的静态资源文件
    # 传出：无返回值
    app.mount("/static", StaticFiles(directory=str(静态文件目录)), name="static")


@app.get("/game-order", response_class=HTMLResponse, include_in_schema=False)
async def 游戏下单页面():
    """返回游戏下单页面（game.fashiye.cn 入口）"""
    html路径 = 静态文件目录 / "game-order.html"
    if html路径.exists():
        return HTMLResponse(content=html路径.read_text(encoding="utf-8"))
    return HTMLResponse(content="<h1>页面未找到</h1>", status_code=404)


@app.get("/order-lookup", response_class=HTMLResponse, include_in_schema=False)
async def 凭据查询页面():
    """返回凭据查询页面（docs.fashiye.com 入口）"""
    html路径 = 静态文件目录 / "order-lookup.html"
    if html路径.exists():
        return HTMLResponse(content=html路径.read_text(encoding="utf-8"))
    return HTMLResponse(content="<h1>页面未找到</h1>", status_code=404)


@app.get("/order-detail", response_class=HTMLResponse, include_in_schema=False)
async def 订单详情页面():
    """返回订单详情页（含聊天功能）"""
    html路径 = 静态文件目录 / "order-detail.html"
    if html路径.exists():
        return HTMLResponse(content=html路径.read_text(encoding="utf-8"))
    return HTMLResponse(content="<h1>页面未找到</h1>", status_code=404)


# 前端页面别名路由（方便域名绑定）
@app.get("/", response_class=HTMLResponse, include_in_schema=False)
async def 首页():
    """返回游戏下单页面（根路径）"""
    html路径 = 静态文件目录 / "game-order.html"
    if html路径.exists():
        return HTMLResponse(content=html路径.read_text(encoding="utf-8"))
    # 回退到 API 首页
    return JSONResponse({
        "code": 0,
        "data": {
            "name": 配置对象.项目名称,
            "version": 配置对象.版本号
        },
        "message": "游戏代练交易平台 API"
    })
