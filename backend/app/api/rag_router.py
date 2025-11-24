from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from app.models.rag_models import QueryRequest, QueryResponse, ChunkConfig, SimilarityConfig, RAGWeightConfig
from app.services.rag_service import RAGService
import traceback
import logging

logger = logging.getLogger(__name__)

router = APIRouter()
rag_service = RAGService()

@router.post("/query", response_model=QueryResponse)
async def query_documents(
    request: QueryRequest,
    chunk_size: Optional[int] = Query(None, ge=100, le=5000),
    chunk_overlap: Optional[int] = Query(None, ge=0, le=1000),
    similarity_threshold: Optional[float] = Query(None, ge=0.0, le=1.0),
    top_k: Optional[int] = Query(None, ge=1, le=20)
):
    """RAG 쿼리 처리"""
    try:
        logger.info(f"쿼리 요청 받음: query='{request.query[:100] if request.query else 'None'}...', folder='{request.folder}'")
        
        # 요청 검증
        if not request.query or not request.query.strip():
            return QueryResponse(
                answer="질문을 입력해주세요.",
                chunks=[],
                sources=[]
            )
        
        response = await rag_service.query(
            request=request,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            similarity_threshold=similarity_threshold,
            top_k=top_k
        )
        logger.info("쿼리 처리 완료")
        return response
    except ValueError as e:
        logger.error(f"ValueError in query: {str(e)}")
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

@router.post("/evaluate")
async def evaluate_retrieval(
    query: str,
    expected_documents: list[str]
):
    """문서 매칭 정확도 평가"""
    try:
        result = await rag_service.evaluate_retrieval_accuracy(
            query=query,
            expected_documents=expected_documents
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/similarity-config")
async def update_similarity_config(config: SimilarityConfig):
    """유사도 설정 업데이트"""
    try:
        rag_service.retriever.update_config(
            similarity_threshold=config.similarity_threshold,
            top_k=config.top_k
        )
        return {"message": "Similarity configuration updated", "config": config}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/chunk-config")
async def update_chunk_config(config: ChunkConfig):
    """청킹 설정 업데이트 (Row 단위 청킹 포함)"""
    try:
        rag_service.chunker.update_config(
            chunk_size=config.chunk_size,
            chunk_overlap=config.chunk_overlap,
            chunk_by_row=config.chunk_by_row
        )
        return {"message": "Chunk configuration updated", "config": config}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/weight-config")
async def update_weight_config(config: RAGWeightConfig):
    """RAG 가중치 설정 업데이트"""
    try:
        rag_service.retriever.update_config(
            similarity_weight=config.similarity_weight,
            recency_weight=config.recency_weight,
            source_weight=config.source_weight
        )
        return {"message": "Weight configuration updated", "config": config}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

