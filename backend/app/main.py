from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from app.api import rag_router, document_router
from app.core.config import settings
import logging
import traceback

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

app = FastAPI(
    title="RAG API",
    description="RAG 실습을 위한 API",
    version="1.0.0"
)

# 전역 예외 핸들러 추가
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Pydantic validation error 처리"""
    logger = logging.getLogger(__name__)
    logger.error(f"Validation error: {exc.errors()}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": exc.errors(),
            "message": "요청 데이터 검증 실패"
        }
    )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """전역 예외 처리"""
    logger = logging.getLogger(__name__)
    error_detail = f"{str(exc)}\n{traceback.format_exc()}"
    logger.error(f"Unhandled exception: {error_detail}")
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": str(exc),
            "message": "서버 내부 오류가 발생했습니다."
        }
    )

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 등록
app.include_router(rag_router.router, prefix="/api/rag", tags=["RAG"])
app.include_router(document_router.router, prefix="/api/documents", tags=["Documents"])

@app.get("/")
async def root():
    return {"message": "RAG API Server"}

@app.get("/health")
async def health():
    return {"status": "healthy"}

@app.on_event("startup")
async def startup_event():
    """서버 시작 시 실행되는 이벤트"""
    logger = logging.getLogger(__name__)
    logger.info("서버 시작 완료. JSON 인덱스는 RAGService 초기화 시 자동으로 로드됩니다.")

