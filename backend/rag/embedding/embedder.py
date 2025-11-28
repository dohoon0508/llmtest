from typing import List
import numpy as np
from openai import AsyncOpenAI
from openai import APIError, RateLimitError, APIConnectionError
from rag.utils.retry import retry_with_backoff

class Embedder:
    def __init__(self, api_key: str, model: str = "text-embedding-3-small"):
        if not api_key or api_key == "":
            raise ValueError("OpenAI API 키가 설정되지 않았습니다.")
        self.client = AsyncOpenAI(api_key=api_key)
        self.model = model
    
    async def _call_openai_embedding(self, input_data):
        """OpenAI Embedding API 호출 (타임아웃 설정, 재시도 없음 - 빠른 실패)"""
        import asyncio
        import logging
        logger = logging.getLogger(__name__)
        
        try:
            # 타임아웃 설정: 10초 (재시도 없이 빠르게)
            return await asyncio.wait_for(
                self.client.embeddings.create(
                    model=self.model,
                    input=input_data,
                    timeout=10.0  # OpenAI 클라이언트 타임아웃
                ),
                timeout=12.0  # 전체 타임아웃
            )
        except asyncio.TimeoutError:
            logger.error("OpenAI Embedding API 호출 타임아웃 (10초 초과)")
            raise TimeoutError("임베딩 생성이 10초를 초과했습니다.")
        except (APIError, RateLimitError, APIConnectionError) as e:
            logger.error(f"OpenAI Embedding API 오류: {str(e)}")
            raise
    
    async def embed_text(self, text: str) -> List[float]:
        """텍스트 임베딩 생성"""
        if not text or not text.strip():
            raise ValueError("빈 텍스트는 임베딩할 수 없습니다.")
        
        response = await self._call_openai_embedding(text)
        
        if not response or not response.data or len(response.data) == 0:
            raise ValueError("OpenAI API에서 임베딩을 받지 못했습니다.")
        
        return response.data[0].embedding
    
    async def embed_query(self, query: str) -> List[float]:
        """쿼리 임베딩 생성"""
        return await self.embed_text(query)
    
    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """배치 임베딩 생성"""
        if not texts or len(texts) == 0:
            raise ValueError("빈 텍스트 리스트는 임베딩할 수 없습니다.")
        
        # 빈 텍스트 필터링
        valid_texts = [t for t in texts if t and t.strip()]
        if not valid_texts:
            raise ValueError("유효한 텍스트가 없습니다.")
        
        response = await self._call_openai_embedding(valid_texts)
        
        if not response or not response.data:
            raise ValueError("OpenAI API에서 임베딩을 받지 못했습니다.")
        
        return [item.embedding for item in response.data]
    
    def cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """코사인 유사도 계산"""
        vec1_array = np.array(vec1)
        vec2_array = np.array(vec2)
        
        dot_product = np.dot(vec1_array, vec2_array)
        norm1 = np.linalg.norm(vec1_array)
        norm2 = np.linalg.norm(vec2_array)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return float(dot_product / (norm1 * norm2))

