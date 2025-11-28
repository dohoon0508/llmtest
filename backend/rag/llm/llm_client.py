from openai import AsyncOpenAI
from openai import APIError, RateLimitError, APIConnectionError
from rag.utils.retry import retry_with_backoff
from rag.llm.prompts import SYSTEM_PROMPT, get_rag_prompt, format_context_chunks
from typing import List, Dict, Any

class LLMClient:
    def __init__(self, api_key: str, model: str = "gpt-4o-mini"):
        if not api_key or api_key == "":
            raise ValueError("OpenAI API 키가 설정되지 않았습니다.")
        self.client = AsyncOpenAI(api_key=api_key)
        self.model = model
    
    async def _call_openai(self, messages, temperature=0.7, max_tokens=1000):
        """OpenAI API 호출 (타임아웃 설정, 재시도 없음 - 빠른 실패)"""
        import asyncio
        import logging
        logger = logging.getLogger(__name__)
        
        try:
            # 타임아웃 설정: 15초 (재시도 없이 빠르게)
            return await asyncio.wait_for(
                self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    timeout=15.0  # OpenAI 클라이언트 타임아웃
                ),
                timeout=18.0  # 전체 타임아웃
            )
        except asyncio.TimeoutError:
            logger.error("OpenAI API 호출 타임아웃 (15초 초과)")
            raise TimeoutError("OpenAI API 호출이 15초를 초과했습니다.")
        except (APIError, RateLimitError, APIConnectionError) as e:
            logger.error(f"OpenAI API 오류: {str(e)}")
            raise
    
    async def generate_answer(
        self, 
        query: str, 
        context: str = None,
        chunks: List[Dict[str, Any]] = None,
        scenario: str = None,
        region: str = None
    ) -> str:
        """컨텍스트를 기반으로 답변 생성"""
        # 입력값 검증
        if not query or not query.strip():
            return "질문이 비어있습니다."
        
        # chunks가 제공된 경우 구조화된 컨텍스트 생성
        if chunks:
            context_text = format_context_chunks(chunks)
        elif context:
            context_text = context
        else:
            return "참고할 문서 내용이 없습니다."
        
        # 컨텍스트가 너무 길면 잘라내기 (대략 12000자 제한으로 증가)
        if len(context_text) > 12000:
            context_text = context_text[:12000] + "... (내용이 길어 일부 생략되었습니다)"
        
        # 프롬프트 템플릿 사용
        prompt = get_rag_prompt(query=query, context=context_text, scenario=scenario, region=region)
        
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt}
        ]
        
        try:
            # 성능 최적화: max_tokens 줄이고 temperature 조정 (더 빠른 응답)
            response = await self._call_openai(messages, max_tokens=1500, temperature=0.1)
            
            if not response:
                return "죄송합니다. 응답을 생성하는 중 오류가 발생했습니다."
            
            if not response.choices or len(response.choices) == 0:
                return "죄송합니다. 응답을 생성하는 중 오류가 발생했습니다."
            
            answer = response.choices[0].message.content
            if not answer or not answer.strip():
                return "죄송합니다. 응답을 생성할 수 없습니다. 다시 시도해주세요."
            
            return answer.strip()
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"LLM generate_answer error: {str(e)}", exc_info=True)
            error_msg = str(e)
            # 너무 긴 오류 메시지는 축약
            if len(error_msg) > 200:
                error_msg = error_msg[:200] + "..."
            return f"죄송합니다. 답변 생성 중 오류가 발생했습니다: {error_msg}"

