from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.exceptions import BusinessError, AuthError
from app.api.v1.endpoints import auth, orders, conversations, games, users

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    debug=settings.DEBUG
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/v1", tags=["auth"])
app.include_router(orders.router, prefix="/api/v1", tags=["orders"])
app.include_router(conversations.router, prefix="/api/v1", tags=["conversations"])
app.include_router(games.router, prefix="/api/v1", tags=["games"])
app.include_router(users.router, prefix="/api/v1", tags=["users"])


@app.exception_handler(BusinessError)
async def business_exception_handler(request: Request, exc: BusinessError):
    return JSONResponse(
        status_code=exc.code,
        content={"code": exc.code, "message": exc.message, "data": None}
    )


@app.exception_handler(AuthError)
async def auth_exception_handler(request: Request, exc: AuthError):
    return JSONResponse(
        status_code=exc.code,
        content={"code": exc.code, "message": exc.message, "data": None}
    )


@app.get("/")
async def root():
    return {
        "code": 0,
        "data": {
            "name": settings.PROJECT_NAME,
            "version": settings.VERSION
        },
        "message": "游戏代练交易平台 API"
    }


@app.get("/health")
async def health():
    return {"status": "ok"}
