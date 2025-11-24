from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import rag_router, document_router
from app.core.config import settings
from app.services.document_service import DocumentService
import logging
import asyncio

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
    logger.info("서버 시작 중... documents 폴더의 기존 문서를 로드합니다.")
    
    try:
        document_service = DocumentService()
        loaded_count = await document_service.load_existing_documents()
        logger.info(f"서버 시작 완료. {loaded_count}개의 문서가 자동으로 로드되었습니다.")
    except Exception as e:
        logger.error(f"문서 자동 로드 중 오류 발생: {str(e)}")
        # 오류가 있어도 서버는 계속 실행

