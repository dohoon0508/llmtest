from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from app.models.rag_models import QueryRequest, QueryResponse, ChunkConfig, SimilarityConfig, RAGWeightConfig
from app.services.rag_service import RAGService
import traceback
import logging

logger = logging.getLogger(__name__)

router = APIRouter()
rag_service = None

def get_rag_service():
    """RAG 서비스 인스턴스 가져오기 (지연 초기화)"""
    global rag_service
    if rag_service is None:
        try:
            logger.info("RAG 서비스 초기화 시작...")
            rag_service = RAGService()
            logger.info("RAG 서비스 초기화 완료")
        except Exception as e:
            error_detail = f"{str(e)}\n{traceback.format_exc()}"
            logger.error(f"RAG 서비스 초기화 실패: {error_detail}")
            raise RuntimeError(f"RAG 서비스 초기화 실패: {str(e)}") from e
    return rag_service

@router.post("/query", response_model=QueryResponse)
async def query_documents(
    request: QueryRequest,
    top_k: Optional[int] = Query(None, ge=1, le=20)
):
    """RAG 쿼리 처리 (JSON만 사용)"""
    try:
        logger.info(f"쿼리 요청 받음: query='{request.query[:100] if request.query else 'None'}...', folder='{request.folder}', region='{request.region}'")
        logger.info(f"요청 상세: {request.dict()}")
        
        # 요청 검증
        if not request.query or not request.query.strip():
            logger.warning("빈 쿼리 요청")
            return QueryResponse(
                answer="질문을 입력해주세요.",
                chunks=[],
                sources=[]
            )
        
        # RAG 서비스 가져오기 (지연 초기화)
        try:
            service = get_rag_service()
        except Exception as e:
            logger.error(f"RAG 서비스 초기화 실패: {str(e)}", exc_info=True)
            return QueryResponse(
                answer=f"서버 초기화 오류가 발생했습니다: {str(e)[:200]}",
                chunks=[],
                sources=[]
            )
        
        response = await service.query(
            request=request,
            top_k=top_k
        )
        logger.info("쿼리 처리 완료")
        return response
    except ValueError as e:
        logger.error(f"ValueError in query: {str(e)}", exc_info=True)
        return QueryResponse(
            answer=f"입력 오류: {str(e)}",
            chunks=[],
            sources=[]
        )
    except Exception as e:
        error_detail = f"{str(e)}\n{traceback.format_exc()}"
        logger.error(f"RAG query error: {error_detail}")
        # 500 에러 대신 에러 메시지가 포함된 정상 응답 반환
        error_msg = str(e)
        # 너무 긴 에러 메시지는 줄이기
        if len(error_msg) > 200:
            error_msg = error_msg[:200] + "..."
        return QueryResponse(
            answer=f"죄송합니다. 처리 중 오류가 발생했습니다: {error_msg}",
            chunks=[],
            sources=[]
        )


