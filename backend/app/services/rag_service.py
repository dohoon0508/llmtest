from typing import List, Dict, Any, Optional
from app.models.rag_models import QueryRequest, QueryResponse, DocumentChunk
from app.core.config import settings
from rag.chunking.chunker import Chunker
from rag.embedding.embedder import Embedder
from rag.retrieval.retriever import Retriever
from rag.llm.llm_client import LLMClient

class RAGService:
    def __init__(self):
        import logging
        logger = logging.getLogger(__name__)
        
        self.chunker = Chunker(
            chunk_size=settings.CHUNK_SIZE,
            chunk_overlap=settings.CHUNK_OVERLAP
        )
        
        # OpenAI API 키 확인
        if not settings.OPENAI_API_KEY or settings.OPENAI_API_KEY == "":
            logger.warning("OpenAI API 키가 설정되지 않았습니다. .env 파일을 확인해주세요.")
            self.embedder = None
            self.llm_client = None
        else:
            try:
                self.embedder = Embedder(
                    api_key=settings.OPENAI_API_KEY,
                    model=settings.OPENAI_EMBEDDING_MODEL
                )
                self.llm_client = LLMClient(
                    api_key=settings.OPENAI_API_KEY,
                    model=settings.OPENAI_MODEL
                )
            except Exception as e:
                logger.error(f"OpenAI 클라이언트 초기화 실패: {str(e)}")
                self.embedder = None
                self.llm_client = None
        
        self.retriever = Retriever(
            vector_store_path=settings.VECTOR_STORE_PATH,
            top_k=settings.TOP_K_DOCUMENTS,
            similarity_threshold=settings.SIMILARITY_THRESHOLD
        )
    
    async def query(
        self,
        request: QueryRequest,
        chunk_size: Optional[int] = None,
        chunk_overlap: Optional[int] = None,
        similarity_threshold: Optional[float] = None,
        top_k: Optional[int] = None
    ) -> QueryResponse:
        """RAG 쿼리 처리"""
        import logging
        logger = logging.getLogger(__name__)
        
        try:
            # OpenAI 클라이언트 확인
            if self.embedder is None or self.llm_client is None:
                logger.error("OpenAI 클라이언트가 초기화되지 않았습니다.")
                return QueryResponse(
                    answer="죄송합니다. OpenAI API 키가 설정되지 않았습니다. backend/.env 파일에 OPENAI_API_KEY를 설정하고 서버를 재시작해주세요.",
                    chunks=[],
                    sources=[]
                )
            
            # 설정 업데이트
            if chunk_size or chunk_overlap:
                self.chunker.update_config(
                    chunk_size=chunk_size or settings.CHUNK_SIZE,
                    chunk_overlap=chunk_overlap or settings.CHUNK_OVERLAP
                )
            
            if similarity_threshold or top_k:
                self.retriever.update_config(
                    similarity_threshold=similarity_threshold or settings.SIMILARITY_THRESHOLD,
                    top_k=top_k or request.top_k or settings.TOP_K_DOCUMENTS
                )
            
            # 폴더 필터링 확인 (필수)
            folder_filter = request.folder
            if not folder_filter or not folder_filter.strip():
                logger.warning("폴더가 선택되지 않았습니다.")
                return QueryResponse(
                    answer="건축 양식을 선택해주세요. 왼쪽 사이드바에서 건축 양식을 선택한 후 질문해주세요.",
                    chunks=[],
                    sources=[]
                )
            
            # OpenAI API 키 확인
            if not self.embedder or not self.llm_client:
                logger.error("OpenAI API 키가 설정되지 않았습니다.")
                return QueryResponse(
                    answer="죄송합니다. OpenAI API 키가 설정되지 않았습니다. 서버 관리자에게 문의해주세요.\n\n.env 파일에 OPENAI_API_KEY를 설정해야 합니다.",
                    chunks=[],
                    sources=[]
                )
            
            # 문서 검색
            logger.info(f"쿼리 임베딩 생성 시작: {request.query[:50]}...")
            try:
                # 쿼리 자체는 그대로 사용 (파일명 매칭은 임베딩에서 자동으로 처리됨)
                query_embedding = await self.embedder.embed_query(request.query)
                logger.info(f"쿼리 임베딩 생성 완료: {len(query_embedding)} 차원")
            except Exception as e:
                logger.error(f"쿼리 임베딩 생성 실패: {str(e)}", exc_info=True)
                return QueryResponse(
                    answer=f"죄송합니다. 질문을 처리하는 중 오류가 발생했습니다: {str(e)[:200]}",
                    chunks=[],
                    sources=[]
                )
            
            logger.info("문서 검색 시작...")
            
            # 파일 필터링 설정 (4, 5-1, 5-2 파일만)
            filename_filter = ["4.", "5-1.", "5-2."]
            
            logger.info(f"폴더 필터: {folder_filter}, 파일 필터: {filename_filter}")
            
            # 유사도 임계값 설정 (기본값을 낮춰서 더 많은 문서 검색)
            final_threshold = similarity_threshold or request.similarity_threshold or 0.1  # 최소 0.1로 설정
            
            logger.info(f"유사도 임계값: {final_threshold}")
            
            retrieved_chunks = await self.retriever.retrieve(
                query_embedding=query_embedding,
                top_k=top_k or request.top_k or settings.TOP_K_DOCUMENTS,
                similarity_threshold=final_threshold,
                folder_filter=folder_filter,
                filename_filter=filename_filter if folder_filter else None  # 폴더가 선택된 경우만 파일 필터링
            )
            logger.info(f"문서 검색 완료: {len(retrieved_chunks)}개 청크 발견")
        
            # 검색된 문서가 없는 경우 처리
            if not retrieved_chunks or len(retrieved_chunks) == 0:
                logger.warning(f"검색된 문서가 없습니다. (폴더: {folder_filter}, 쿼리: {request.query[:50]}...)")
                return QueryResponse(
                    answer=f"죄송합니다. 선택하신 건축 양식({folder_filter})의 문서에서 질문과 관련된 내용을 찾을 수 없습니다.\n\n다음 사항을 확인해주세요:\n1. 해당 폴더에 문서가 업로드되어 있는지\n2. 문서 이름이 '4.', '5-1.', '5-2.'로 시작하는지\n3. 질문을 다시 정리해서 시도해보세요",
                    chunks=[],
                    sources=[]
                )
            
            # 응답 구성 (안전한 데이터 접근) - LLM 호출 전에 먼저 처리
            document_chunks = []
            sources_set = set()
            context_parts = []
            
            for chunk in retrieved_chunks:
                try:
                    metadata = chunk.get("metadata") or {}
                    content = chunk.get("content", "")
                    
                    # 내용이 있고 비어있지 않은 경우만 추가
                    if content and content.strip():
                        # score 안전하게 처리 (None이거나 숫자가 아닌 경우 기본값 0.0)
                        score = chunk.get("score")
                        if score is None or not isinstance(score, (int, float)):
                            score = 0.0
                        else:
                            score = float(score)
                        
                        document_chunks.append(
                            DocumentChunk(
                                content=content.strip(),
                                metadata=metadata,
                                score=score
                            )
                        )
                        
                        # 컨텍스트용 텍스트 수집
                        context_parts.append(content.strip())
                        
                        # 출처 추가 (안전하게)
                        source = metadata.get("source")
                        if source and isinstance(source, str) and source.strip():
                            sources_set.add(source.strip())
                except Exception as e:
                    logger.warning(f"청크 처리 중 오류 (스킵): {str(e)}")
                    continue
            
            # 컨텍스트 구성
            context = "\n\n".join(context_parts)
            
            # 컨텍스트가 비어있는 경우 처리
            if not context.strip():
                logger.warning("컨텍스트가 비어있습니다.")
                if not retrieved_chunks or len(retrieved_chunks) == 0:
                    return QueryResponse(
                        answer=f"죄송합니다. '{folder_filter}' 폴더에서 질문과 관련된 문서를 찾을 수 없습니다.\n\n다음 사항을 확인해주세요:\n1. 해당 폴더에 문서가 업로드되어 있는지\n2. 문서 이름이 '4.', '5-1.', '5-2.'로 시작하는지\n3. 질문을 다시 정리해서 시도해보세요",
                        chunks=[],
                        sources=[]
                    )
                else:
                    # 청크는 있지만 내용이 비어있는 경우
                    return QueryResponse(
                        answer="죄송합니다. 관련 문서를 찾았지만 내용을 추출할 수 없습니다. 문서 형식을 확인해주세요.",
                        chunks=document_chunks,
                        sources=list(sources_set)
                    )
            
            logger.info(f"LLM 답변 생성 시작 (컨텍스트 길이: {len(context)} 문자, 청크 수: {len(document_chunks)}개)")
            try:
                # 구조화된 청크가 있는지 확인 (scenario, law_group 등의 필드 존재)
                has_structured_chunks = any(
                    (chunk.get("metadata") or {}).get("scenario") or 
                    (chunk.get("metadata") or {}).get("law_group")
                    for chunk in retrieved_chunks
                )
                
                # 구조화된 청크가 있으면 구조화된 형식으로 전달
                if has_structured_chunks:
                    from rag.llm.prompts import format_context_chunks
                    chunks_list = [
                        {
                            **chunk.get("metadata", {}),
                            "content": chunk.get("content", ""),
                            "review_text": chunk.get("metadata", {}).get("review_text", ""),
                            "law_text": chunk.get("metadata", {}).get("law_text", ""),
                        }
                        for chunk in retrieved_chunks
                    ]
                    answer = await self.llm_client.generate_answer(
                        query=request.query,
                        chunks=chunks_list,
                        scenario=folder_filter
                    )
                else:
                    # 기본 방식 (기존 구조화되지 않은 청크)
                    answer = await self.llm_client.generate_answer(
                        query=request.query,
                        context=context,
                        scenario=folder_filter
                    )
                logger.info("LLM 답변 생성 완료")
                
                # 답변 검증
                if not answer or not answer.strip():
                    logger.error("LLM이 빈 응답을 반환했습니다.")
                    return QueryResponse(
                        answer="죄송합니다. 답변 생성에 실패했습니다. 검색된 문서 정보는 아래 참고 문서에서 확인하실 수 있습니다.",
                        chunks=document_chunks,
                        sources=list(sources_set)
                    )
            except Exception as e:
                logger.error(f"LLM 답변 생성 실패: {str(e)}", exc_info=True)
                import traceback
                error_detail = traceback.format_exc()
                logger.error(f"상세 오류:\n{error_detail}")
                
                # 사용자 친화적인 에러 메시지
                error_msg = str(e)
                if "API key" in error_msg or "authentication" in error_msg.lower():
                    error_msg = "OpenAI API 키가 설정되지 않았거나 잘못되었습니다."
                elif len(error_msg) > 300:
                    error_msg = error_msg[:300] + "..."
                
                return QueryResponse(
                    answer=f"죄송합니다. 답변 생성 중 오류가 발생했습니다.\n\n오류: {error_msg}\n\n검색된 문서 정보는 아래 참고 문서에서 확인하실 수 있습니다.",
                    chunks=document_chunks,
                    sources=list(sources_set)
                )
            
            logger.info(f"응답 구성 완료: {len(document_chunks)}개 청크, {len(sources_set)}개 출처")
            return QueryResponse(
                answer=answer,
                chunks=document_chunks,
                sources=list(sources_set)
            )
        except ValueError as e:
            logger.error(f"ValueError in query: {str(e)}")
            return QueryResponse(
                answer=f"입력 오류: {str(e)}",
                chunks=[],
                sources=[]
            )
        except Exception as e:
            logger.error(f"Unexpected error in query: {str(e)}", exc_info=True)
            return QueryResponse(
                answer=f"죄송합니다. 처리 중 오류가 발생했습니다: {str(e)}",
                chunks=[],
                sources=[]
            )
    
    async def evaluate_retrieval_accuracy(
        self,
        query: str,
        expected_documents: List[str]
    ) -> Dict[str, Any]:
        """문서 매칭 정확도 평가"""
        query_embedding = await self.embedder.embed_query(query)
        retrieved_chunks = await self.retriever.retrieve(
            query_embedding=query_embedding,
            top_k=settings.TOP_K_DOCUMENTS,
            similarity_threshold=settings.SIMILARITY_THRESHOLD
        )
        
        retrieved_sources = [
            chunk.get("metadata", {}).get("source", "unknown")
            for chunk in retrieved_chunks
        ]
        
        matched = len(set(retrieved_sources) & set(expected_documents))
        precision = matched / len(retrieved_sources) if retrieved_sources else 0
        recall = matched / len(expected_documents) if expected_documents else 0
        f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
        
        return {
            "query": query,
            "expected_documents": expected_documents,
            "retrieved_documents": retrieved_sources,
            "matched_count": matched,
            "precision": precision,
            "recall": recall,
            "f1_score": f1
        }

