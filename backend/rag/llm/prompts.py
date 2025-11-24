"""LLM 프롬프트 템플릿"""
from typing import List, Dict, Any

SYSTEM_PROMPT = """당신은 건축 인허가 실무를 돕는 AI 어시스턴트입니다.
주어진 참고 자료(검토내용 + 법령내용)를 기반으로만 답변하세요.
검토내용을 기준으로 결론을 내고, 법령 조문을 근거로 제시하세요.
모를 때는 모른다고 말하고, 임의로 법령을 만들어내지 마세요.
답변은 구조화된 형식으로 작성하세요."""

USER_PROMPT_TEMPLATE = """당신은 건축 인허가 실무를 돕는 AI입니다.
아래는 "{scenario}" 시나리오에 대한 법령 조문과 검토내용입니다.

중요 지침:
1. "검토내용"은 실제 적용 요약입니다 - 이것을 기준으로 먼저 결론을 내세요.
2. "법령내용"은 법 조문 원문입니다 - 검토내용의 근거로 인용하세요.
3. 컨텍스트에 없는 정보는 추측하지 말고, 컨텍스트에 있는 정보만 사용하세요.
4. 답변은 반드시 다음 형식으로 작성하세요:

**답변 형식 (마크다운 사용 필수):**
- 제목은 `## [질문에 대한 답변 제목]` 형식으로 작성
- 번호가 매겨진 섹션은 `### 1. [섹션명]` 형식으로 작성
- 각 섹션 내에서 불릿 포인트는 `-` 또는 `*`로 시작
- 각 항목은 구체적이고 실용적으로 작성
- 법령 근거는 각 항목 뒤에 `[근거: 법령명 조문]` 형식으로 명시
- 마지막에 "더 자세한 내용이 필요하신가요?" 추가

**예시 형식 (마크다운):**
```markdown
## 건축허가에 필요한 서류

### 1. 건축허가 신청
- 신축 건축물을 건축하려면 특별시장·광역시장·특별자치시장·특별자치도지사·시장·군수·구청장의 허가를 받아야 합니다. [근거: 건축법 제11조]
- 건축허가를 받기 위해서는 건축물의 설계도서, 구조안전 확인, 대지의 조경계획서 등 관련 서류가 필요할 수 있습니다. [근거: 건축법 제23조, 제42조, 제48조]

### 2. 착공신고
- 건축허가를 받은 후에는 공사를 시작하기 전에 허가권자에게 공사계획을 신고해야 합니다. [근거: 건축법 제21조]

더 자세한 내용이 필요하신가요?
```

[참고 자료]
{context}

사용자 질문:
{query}

위 자료를 우선적으로 사용해서 한국어로 구조화된 형식으로 답변하세요."""

def get_rag_prompt(query: str, context: str, scenario: str = None) -> str:
    """RAG 프롬프트 생성"""
    scenario_text = scenario or "건축허가"
    return USER_PROMPT_TEMPLATE.format(
        scenario=scenario_text,
        context=context,
        query=query
    )

def format_context_chunks(chunks: List[Dict[str, Any]]) -> str:
    """구조화된 청크들을 프롬프트용 컨텍스트 텍스트로 변환"""
    context_blocks = []
    
    for i, chunk in enumerate(chunks, 1):
        block_parts = [f"[참고 자료 {i}]"]
        
        scenario = chunk.get("scenario") or chunk.get("metadata", {}).get("scenario")
        law_group = chunk.get("law_group") or chunk.get("metadata", {}).get("law_group")
        item_name = chunk.get("item_name") or chunk.get("metadata", {}).get("item_name")
        
        if scenario:
            block_parts.append(f"시나리오: {scenario}")
        if law_group:
            block_parts.append(f"법령 묶음: {law_group}")
        if item_name:
            block_parts.append(f"항목: {item_name}")
        
        # 조문 번호
        article_ids = chunk.get("article_ids") or chunk.get("metadata", {}).get("article_ids", [])
        if article_ids:
            block_parts.append(f"조문: {', '.join(article_ids)}")
        
        # 검토내용
        review_text = chunk.get("review_text") or chunk.get("metadata", {}).get("review_text")
        if review_text:
            block_parts.append(f"검토내용: {review_text}")
        
        # 법령내용 (너무 길면 자름)
        law_text = chunk.get("law_text") or chunk.get("metadata", {}).get("law_text") or chunk.get("content", "")
        if law_text:
            if len(law_text) > 1000:
                law_text = law_text[:1000] + "... (내용이 길어 일부 생략)"
            block_parts.append(f"법령내용: {law_text}")
        
        context_blocks.append("\n".join(block_parts))
    
    return "\n\n".join(context_blocks)

