"""TenantGuard FastAPI 애플리케이션 진입점"""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from app.config import settings
from app.api.v1.applications import router as applications_router
from app.api.v1.address import router as address_router
from app.api.v1.connectivity import router as connectivity_router

logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s — %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"TenantGuard API 시작 (v{settings.APP_VERSION})")
    yield
    logger.info("TenantGuard API 종료")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=(
        "전세사기 피해자를 위한 임차권등기명령 자동화 서비스 API.\n\n"
        "공동인증서 + 기본 정보만 입력하면 필요 서류를 자동 수집하고 "
        "대법원 전자소송 시스템에 신청서를 자동 입력합니다."
    ),
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── 미들웨어 ──────────────────────────────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── 라우터 ─────────────────────────────────────────────────────────────────────

app.include_router(applications_router, prefix="/api/v1")
app.include_router(address_router, prefix="/api/v1")
app.include_router(connectivity_router, prefix="/api/v1")


@app.get("/health", tags=["System"])
async def health_check():
    return {"status": "ok", "version": settings.APP_VERSION}
