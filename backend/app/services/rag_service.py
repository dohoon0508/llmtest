from typing import List, Dict, Any, Optional
import time
import asyncio
import logging
from app.models.rag_models import QueryRequest, QueryResponse, DocumentChunk
from app.core.config import settings
from rag.retrieval.json_index import JSONIndex
from rag.llm.llm_client import LLMClient

class RAGService:
    def __init__(self):
        logger = logging.getLogger(__name__)
        
        # OpenAI API 키 확인 (LLM만 사용)
        if not settings.OPENAI_API_KEY or settings.OPENAI_API_KEY == "":
            logger.warning("OpenAI API 키가 설정되지 않았습니다. .env 파일을 확인해주세요.")
            self.llm_client = None
        else:
            try:
                self.llm_client = LLMClient(
                    api_key=settings.OPENAI_API_KEY,
                    model=settings.OPENAI_MODEL
                )
                logger.info("OpenAI LLM 클라이언트 초기화 완료")
            except Exception as e:
                logger.error(f"OpenAI LLM 클라이언트 초기화 실패: {str(e)}", exc_info=True)
                self.llm_client = None
        
        # JSON 인덱스 초기화 (JSON만 사용)
        try:
            self.json_index = JSONIndex()
            self._load_json_index()
            logger.info("JSON 인덱스 초기화 완료")
        except Exception as e:
            logger.error(f"JSON 인덱스 초기화 실패: {str(e)}", exc_info=True)
            raise RuntimeError(f"JSON 인덱스 초기화 실패: {str(e)}") from e
    
    def _load_json_index(self):
        """documents 폴더의 JSON 파일들을 JSON 인덱스에 로드"""
        logger = logging.getLogger(__name__)
        
        from pathlib import Path
        documents_dir = Path(settings.DOCUMENTS_DIR)
        
        if not documents_dir.exists():
            logger.warning(f"documents 폴더가 없습니다: {documents_dir}")
            return
        
        json_count = 0
        
        # 모든 폴더에서 JSON 파일 찾기
        for folder_path in documents_dir.iterdir():
            if not folder_path.is_dir():
                continue
            
            folder_name = folder_path.name
            
            # 폴더 내의 JSON 파일 찾기
            for json_file in folder_path.glob("*.json"):
                if json_file.name.startswith('~$'):
                    continue
                if self.json_index.load_json_file(json_file, folder_name):
                    json_count += 1
        
        # 루트 폴더의 JSON 파일도 찾기
        for json_file in documents_dir.glob("*.json"):
            if json_file.name.startswith('~$'):
                continue
            if self.json_index.load_json_file(json_file, ""):
                json_count += 1
        
        # region 폴더의 JSON 파일 (지역명을 폴더명으로 사용)
        # 파일명 매핑: Jeonju_Construction_Ordinance.json -> 전주시
        region_folder = documents_dir / "region"
        if region_folder.exists():
            # 지역명 매핑 (JSON 파일명 -> 지역명)
            region_file_mapping = {
                "Jeonju_Construction_Ordinance.json": "전주시"
                # 향후 다른 지역 추가:
                # "Seoul_Construction_Ordinance.json": "서울시",
                # "Busan_Construction_Ordinance.json": "부산시",
            }
            
            for json_file in region_folder.glob("*.json"):
                if json_file.name.startswith('~$'):
                    continue
                
                # 파일명으로 지역명 찾기
                region_name = region_file_mapping.get(json_file.name)
                if not region_name:
                    # 매핑에 없으면 파일명에서 추출 시도
                    if "Jeonju" in json_file.name or "전주" in json_file.name:
                        region_name = "전주시"
                    else:
                        # 기본값으로 "region" 사용 (향후 확장 고려)
                        region_name = "region"
                
                if self.json_index.load_json_file(json_file, region_name):
                    json_count += 1
                    logger.info(f"지역 JSON 파일 인덱싱: {region_name}/{json_file.name}")
        
        logger.info(f"JSON 인덱스 로드 완료: {json_count}개 JSON 파일 인덱싱됨")
    
    async def query(
        self,
        request: QueryRequest,
        top_k: Optional[int] = None
    ) -> QueryResponse:
        """RAG 쿼리 처리 (JSON만 사용)"""
        logger = logging.getLogger(__name__)
        
        try:
            # OpenAI LLM 클라이언트 확인
            if self.llm_client is None:
                logger.error("OpenAI LLM 클라이언트가 초기화되지 않았습니다.")
                return QueryResponse(
                    answer="죄송합니다. OpenAI API 키가 설정되지 않았습니다. backend/.env 파일에 OPENAI_API_KEY를 설정하고 서버를 재시작해주세요.",
                    chunks=[],
                    sources=[]
                )
            
            # JSON 인덱스 확인
            if self.json_index is None:
                logger.error("JSON 인덱스가 초기화되지 않았습니다.")
                return QueryResponse(
                    answer="죄송합니다. JSON 인덱스 초기화에 실패했습니다. 서버 로그를 확인해주세요.",
                    chunks=[],
                    sources=[]
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
            
            # 지역 필터링 (선택사항)
            region_filter = request.region
            if region_filter:
                region_filter = region_filter.strip()
                logger.info(f"지역 필터 적용: {region_filter}")
            
            logger.info(f"검색 필터 - 건물 타입: {folder_filter}, 지역: {region_filter or '없음'}")
            
            # JSON 인덱스 검색 (JSON만 사용)
            start_time = time.time()
            json_results = []
            
            try:
                search_top_k = top_k or request.top_k or 5
                json_results = self.json_index.search(
                    query=request.query,
                    folder_filter=folder_filter,
                    region_filter=region_filter,
                    top_k=search_top_k
                )
                search_time = time.time() - start_time
                
                if json_results:
                    logger.info(f"JSON 인덱스 검색 완료: {len(json_results)}개 결과, {search_time:.3f}초")
                else:
                    logger.warning(f"JSON 검색 결과 없음: {search_time:.3f}초")
            except Exception as e:
                logger.error(f"JSON 인덱스 검색 실패: {str(e)}", exc_info=True)
                return QueryResponse(
                    answer=f"죄송합니다. 검색 중 오류가 발생했습니다: {str(e)[:200]}",
                    chunks=[],
                    sources=[]
                )
            
            # 검색된 문서가 없는 경우 처리
            if not json_results or len(json_results) == 0:
                logger.warning(f"검색된 문서가 없습니다. (폴더: {folder_filter}, 쿼리: {request.query[:50]}...)")
                return QueryResponse(
                    answer=f"죄송합니다. 선택하신 건축 양식({folder_filter})의 JSON 문서에서 질문과 관련된 내용을 찾을 수 없습니다.\n\n다음 사항을 확인해주세요:\n1. 해당 폴더에 Construction_law_qa.json 파일이 있는지\n2. 질문을 다시 정리해서 시도해보세요",
                    chunks=[],
                    sources=[]
                )
            
            # JSON 결과를 retrieved_chunks로 변환
            retrieved_chunks = []
            for json_result in json_results:
                retrieved_chunks.append({
                    "content": json_result["content"],
                    "metadata": json_result["metadata"],
                    "score": json_result.get("score", 1.0)
                })
            
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
                        # score 안전하게 처리
                        score = chunk.get("score")
                        if score is None or not isinstance(score, (int, float)):
                            score = 1.0
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
                        
                        # 출처 추가
                        source = metadata.get("source")
                        if source and isinstance(source, str) and source.strip():
                            sources_set.add(source.strip())
                        elif metadata.get("filename"):
                            folder = metadata.get("folder", "")
                            if folder:
                                sources_set.add(f"{folder}/{metadata.get('filename')}")
                            else:
                                sources_set.add(metadata.get("filename"))
                except Exception as e:
                    logger.warning(f"청크 처리 중 오류 (스킵): {str(e)}")
                    continue
            
            # 컨텍스트 구성
            context = "\n\n".join(context_parts)
            
            # 컨텍스트가 비어있는 경우 처리
            if not context.strip():
                logger.warning("컨텍스트가 비어있습니다.")
                return QueryResponse(
                    answer=f"죄송합니다. '{folder_filter}' 폴더의 JSON 문서에서 질문과 관련된 내용을 찾을 수 없습니다.",
                    chunks=[],
                    sources=[]
                )
            
            # LLM 답변 생성
            llm_start = time.time()
            logger.info(f"LLM 답변 생성 시작 (컨텍스트: {len(context)}자, 청크: {len(document_chunks)}개)")
            try:
                # 타임아웃 설정: 최대 20초
                answer = await asyncio.wait_for(
                    self.llm_client.generate_answer(
                        query=request.query,
                        context=context,
                        scenario=folder_filter,
                        region=region_filter
                    ),
                    timeout=20.0
                )
                llm_time = time.time() - llm_start
                logger.info(f"LLM 답변 생성 완료: {llm_time:.2f}초")
            except asyncio.TimeoutError:
                logger.error("LLM 답변 생성 타임아웃 (20초 초과)")
                return QueryResponse(
                    answer="죄송합니다. 답변 생성 시간이 초과되었습니다. 질문을 더 간단하게 다시 시도해주세요.",
                    chunks=document_chunks,
                    sources=list(sources_set)
                )
            except Exception as e:
                logger.error(f"LLM 답변 생성 실패: {str(e)}", exc_info=True)
                return QueryResponse(
                    answer="죄송합니다. 답변 생성 중 오류가 발생했습니다. 검색된 문서 정보는 아래 참고 문서에서 확인하실 수 있습니다.",
                    chunks=document_chunks,
                    sources=list(sources_set)
                )
            
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
    

