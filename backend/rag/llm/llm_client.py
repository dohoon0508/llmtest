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
    
    @retry_with_backoff(
        max_retries=3,
        initial_delay=1.0,
        max_delay=10.0,
        exponential_base=2.0,
        exceptions=(APIError, RateLimitError, APIConnectionError, Exception)
    )
    async def _call_openai(self, messages, temperature=0.7, max_tokens=1000):
        """OpenAI API 호출 (재시도 로직 포함)"""
        return await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens
        )
    
    async def generate_answer(
        self, 
        query: str, 
        context: str = None,
        chunks: List[Dict[str, Any]] = None,
        scenario: str = None
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
        prompt = get_rag_prompt(query=query, context=context_text, scenario=scenario)
        
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt}
        ]
        
        try:
            response = await self._call_openai(messages, max_tokens=3000, temperature=0.3)
            
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

