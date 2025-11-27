# RAG (Retrieval-Augmented Generation) 모듈

이 폴더는 RAG 시스템의 핵심 컴포넌트들을 포함하고 있습니다. 문서 검색 및 생성(Retrieval-Augmented Generation) 파이프라인을 구현하여, 사용자 질문에 대해 관련 문서를 검색하고 LLM을 통해 답변을 생성합니다.

## 📁 폴더 구조

```
rag/
├── __init__.py
├── chunking/          # 텍스트 청킹 모듈
│   ├── __init__.py
│   └── chunker.py     # 텍스트를 청크로 분할
├── embedding/         # 임베딩 모듈
│   ├── __init__.py
│   └── embedder.py   # 텍스트를 벡터로 변환
├── retrieval/        # 검색 모듈
│   ├── __init__.py
│   └── retriever.py  # 벡터 유사도 검색
├── llm/              # LLM 모듈
│   ├── __init__.py
│   ├── llm_client.py # LLM API 클라이언트
│   └── prompts.py    # 프롬프트 템플릿
├── parsers/          # 파일 파서 모듈
│   ├── __init__.py
│   ├── file_parser.py      # 범용 파일 파서
│   └── law_table_parser.py # 법령 테이블 전용 파서
└── utils/            # 유틸리티 모듈
    ├── __init__.py
    └── retry.py      # 재시도 로직
```

## 🔄 RAG 파이프라인 흐름

```
문서 업로드
    ↓
파일 파싱 (parsers/)
    ↓
텍스트 청킹 (chunking/)
    ↓
임베딩 생성 (embedding/)
    ↓
벡터 저장소 저장 (retrieval/)
    ↓
[사용자 질문]
    ↓
질문 임베딩 생성 (embedding/)
    ↓
유사도 검색 (retrieval/)
    ↓
관련 문서 컨텍스트 추출
    ↓
LLM 답변 생성 (llm/)
    ↓
최종 답변 반환
```

## 📦 모듈 상세 설명

### 1. `chunking/chunker.py` - 텍스트 청킹

텍스트를 의미 있는 단위로 분할하는 모듈입니다.

#### 주요 기능
- **문장 단위 청킹**: 문장 구분자(`.`, `!`, `?`)를 기준으로 텍스트를 분할
- **줄 단위 청킹**: 문장 구분자가 없는 경우 줄바꿈(`\n`)을 기준으로 분할
- **행 단위 청킹**: 구조화된 데이터(CSV, Excel)의 경우 행 단위로 분할
- **오버랩 처리**: 청크 간 연속성을 위해 일정 길이만큼 오버랩 허용

#### 클래스: `Chunker`

```python
Chunker(
    chunk_size: int = 1000,      # 청크 최대 크기 (문자 수)
    chunk_overlap: int = 200,     # 청크 간 오버랩 크기
    chunk_by_row: bool = False    # 행 단위 청킹 여부
)
```

#### 주요 메서드

- `chunk_text(text: str, metadata: Optional[Dict]) -> List[str]`
  - 텍스트를 청크 리스트로 분할
  - `metadata`에 `is_structured_data=True`가 있으면 행 단위 청킹 수행

- `_chunk_by_row(text: str) -> List[str]`
  - 행 단위 청킹 (CSV/Excel 데이터용)
  - `'행 '`으로 시작하는 줄을 새로운 청크의 시작으로 인식

- `update_config(chunk_size, chunk_overlap, chunk_by_row)`
  - 청킹 설정을 동적으로 업데이트

#### 사용 예시

```python
from rag.chunking.chunker import Chunker

chunker = Chunker(chunk_size=1000, chunk_overlap=200)
chunks = chunker.chunk_text("긴 텍스트 내용...")
```

---

### 2. `embedding/embedder.py` - 텍스트 임베딩

텍스트를 벡터로 변환하여 의미적 유사도를 계산할 수 있게 하는 모듈입니다.

#### 주요 기능
- **OpenAI Embedding API 사용**: `text-embedding-3-small` 모델 사용
- **단일 텍스트 임베딩**: 하나의 텍스트를 벡터로 변환
- **배치 임베딩**: 여러 텍스트를 한 번에 임베딩 (효율성 향상)
- **코사인 유사도 계산**: 두 벡터 간의 유사도 측정
- **재시도 로직**: API 오류 시 자동 재시도 (지수 백오프)

#### 클래스: `Embedder`

```python
Embedder(
    api_key: str,                    # OpenAI API 키
    model: str = "text-embedding-3-small"  # 임베딩 모델
)
```

#### 주요 메서드

- `embed_text(text: str) -> List[float]`
  - 단일 텍스트를 벡터로 변환
  - 빈 텍스트는 `ValueError` 발생

- `embed_query(query: str) -> List[float]`
  - 쿼리 텍스트를 임베딩 (내부적으로 `embed_text` 호출)

- `embed_batch(texts: List[str]) -> List[List[float]]`
  - 여러 텍스트를 배치로 임베딩
  - 빈 텍스트는 자동으로 필터링

- `cosine_similarity(vec1: List[float], vec2: List[float]) -> float`
  - 두 벡터 간의 코사인 유사도 계산 (0~1 범위)
  - 유사도가 높을수록 1에 가까움

#### 사용 예시

```python
from rag.embedding.embedder import Embedder

embedder = Embedder(api_key="your-api-key")
vector = await embedder.embed_text("텍스트 내용")
similarity = embedder.cosine_similarity(vec1, vec2)
```

---

### 3. `retrieval/retriever.py` - 벡터 검색

벡터 저장소에서 유사한 문서를 검색하는 모듈입니다.

#### 주요 기능
- **메모리 기반 벡터 저장소**: JSON 파일로 벡터 저장 및 로드
- **코사인 유사도 검색**: 쿼리 벡터와 가장 유사한 문서 검색
- **메타데이터 필터링**: 폴더, 파일명 등으로 검색 범위 제한
- **점수 부스팅**: 시나리오/용도 일치 시 점수 가중치 적용
- **안전한 오류 처리**: 손상된 JSON 파일 자동 복구

#### 클래스: `Retriever`

```python
Retriever(
    vector_store_path: str = "vector_store",  # 벡터 저장소 경로
    top_k: int = 5,                          # 반환할 문서 개수
    similarity_threshold: float = 0.1,        # 유사도 임계값
    similarity_weight: float = 1.0,           # 유사도 가중치
    recency_weight: float = 0.0,              # 최신성 가중치
    source_weight: float = 0.0                # 출처 가중치
)
```

#### 주요 메서드

- `add_document(embedding, content, metadata)`
  - 문서를 벡터 저장소에 추가
  - 자동으로 JSON 파일에 저장

- `retrieve(query_embedding, folder_filter, filename_filter, top_k, similarity_threshold)`
  - 쿼리와 유사한 문서 검색
  - `folder_filter`: 특정 폴더의 문서만 검색
  - `filename_filter`: 특정 파일명 패턴만 검색 (예: `["4.", "5-1.", "5-2."]`)
  - 점수 부스팅:
    - 시나리오 일치: +0.1
    - 용도 일치: +0.05

- `remove_document(doc_id)`
  - 특정 문서 ID의 모든 청크 제거

- `_load_vector_store()`
  - 벡터 저장소 로드
  - JSON 파싱 오류 시 자동 백업 및 복구

- `_save_vector_store()`
  - 벡터 저장소를 JSON 파일로 저장

#### 벡터 저장소 구조

```json
{
  "vectors": [[0.1, 0.2, ...], ...],      // 임베딩 벡터 리스트
  "contents": ["청크 내용1", ...],        // 청크 텍스트 리스트
  "metadatas": [                          // 메타데이터 리스트
    {
      "source": "doc_id",
      "filename": "5-2.법령별.doc",
      "folder": "신축_일반개인_다중주택",
      "scenario": "신축_일반개인_다중주택",
      "law_group": "건축법",
      "item_name": "건축물의 높이 제한",
      "article_ids": ["제60조", "제61조"],
      ...
    },
    ...
  ]
}
```

#### 사용 예시

```python
from rag.retrieval.retriever import Retriever
from rag.embedding.embedder import Embedder

retriever = Retriever(vector_store_path="./vector_store")
embedder = Embedder(api_key="your-api-key")

# 문서 추가
embedding = await embedder.embed_text("문서 내용")
await retriever.add_document(
    embedding=embedding,
    content="문서 내용",
    metadata={"filename": "test.txt", "folder": "folder1"}
)

# 검색
query_embedding = await embedder.embed_query("검색 질문")
results = await retriever.retrieve(
    query_embedding=query_embedding,
    folder_filter="신축_일반개인_다중주택",
    filename_filter=["5-2."],
    top_k=5
)
```

---

### 4. `llm/llm_client.py` - LLM 답변 생성

검색된 문서 컨텍스트를 기반으로 LLM을 통해 답변을 생성하는 모듈입니다.

#### 주요 기능
- **OpenAI Chat API 사용**: `gpt-4o-mini` 모델 사용
- **구조화된 컨텍스트 지원**: 메타데이터가 포함된 청크를 포맷팅
- **프롬프트 템플릿**: `prompts.py`의 템플릿 사용
- **컨텍스트 길이 제한**: 12000자 초과 시 자동 축약
- **재시도 로직**: API 오류 시 자동 재시도

#### 클래스: `LLMClient`

```python
LLMClient(
    api_key: str,                    # OpenAI API 키
    model: str = "gpt-4o-mini"        # LLM 모델
)
```

#### 주요 메서드

- `generate_answer(query, context, chunks, scenario) -> str`
  - 컨텍스트를 기반으로 답변 생성
  - `chunks`가 제공되면 구조화된 포맷팅 사용
  - `context`가 제공되면 일반 텍스트 컨텍스트 사용
  - `scenario`: 시나리오 정보 (프롬프트에 포함)

#### 파라미터
- `max_tokens`: 3000 (긴 답변 생성)
- `temperature`: 0.3 (일관된 답변)

#### 사용 예시

```python
from rag.llm.llm_client import LLMClient

llm_client = LLMClient(api_key="your-api-key")

# 구조화된 청크 사용
answer = await llm_client.generate_answer(
    query="건축허가에 필요한 서류는?",
    chunks=[
        {
            "scenario": "신축_일반개인_다중주택",
            "law_group": "건축법",
            "item_name": "건축허가 신청",
            "review_text": "검토내용...",
            "law_text": "법령내용...",
            ...
        }
    ],
    scenario="신축_일반개인_다중주택"
)

# 일반 컨텍스트 사용
answer = await llm_client.generate_answer(
    query="질문",
    context="참고 문서 내용..."
)
```

---

### 5. `llm/prompts.py` - 프롬프트 템플릿

LLM에 전달할 프롬프트를 생성하는 모듈입니다.

#### 주요 구성 요소

- **`SYSTEM_PROMPT`**: 시스템 역할 정의
  - 건축 인허가 실무를 돕는 AI 어시스턴트
  - 컨텍스트 기반 답변, 추측 금지

- **`USER_PROMPT_TEMPLATE`**: 사용자 프롬프트 템플릿
  - 시나리오 정보 포함
  - 검토내용과 법령내용 구분
  - 마크다운 형식 답변 요구

- **`get_rag_prompt(query, context, scenario) -> str`**
  - RAG 프롬프트 생성 함수
  - 쿼리, 컨텍스트, 시나리오를 조합

- **`format_context_chunks(chunks) -> str`**
  - 구조화된 청크 리스트를 프롬프트용 텍스트로 변환
  - 각 청크의 메타데이터(시나리오, 법령 묶음, 항목, 조문, 검토내용, 법령내용) 포함

#### 프롬프트 구조

```
[시스템 프롬프트]
당신은 건축 인허가 실무를 돕는 AI 어시스턴트입니다.
주어진 참고 자료를 기반으로만 답변하세요.
...

[사용자 프롬프트]
안녕하세요! 저는 건축 인허가 실무를 돕는 AI입니다.
아래는 "{scenario}" 시나리오에 대한 법령 조문과 검토내용입니다.

[참고 자료]
[참고 자료 1]
시나리오: 신축_일반개인_다중주택
법령 묶음: 건축법
항목: 건축물의 높이 제한
조문: 제60조, 제61조
검토내용: ...
법령내용: ...

사용자 질문: {query}

위 자료를 우선적으로 사용해서 한국어로 구조화된 형식으로 답변하세요.
```

#### 사용 예시

```python
from rag.llm.prompts import get_rag_prompt, format_context_chunks

# 구조화된 청크 포맷팅
context = format_context_chunks(chunks)

# 프롬프트 생성
prompt = get_rag_prompt(
    query="건축허가에 필요한 서류는?",
    context=context,
    scenario="신축_일반개인_다중주택"
)
```

---

### 6. `parsers/file_parser.py` - 범용 파일 파서

다양한 파일 형식을 텍스트로 변환하는 모듈입니다.

#### 지원 파일 형식
- **Excel** (`.xlsx`, `.xls`): pandas로 모든 시트 읽기
- **CSV** (`.csv`): pandas로 읽기
- **Word** (`.docx`): python-docx로 읽기
- **Word (구버전)** (`.doc`): HTML 형식으로 저장된 경우 BeautifulSoup으로 파싱
- **텍스트** (`.txt`, `.md`): UTF-8 디코딩
- **HTML**: 텍스트 추출

#### 클래스: `FileParser`

#### 주요 메서드

- `parse_file(filename: str, file_content: bytes) -> str`
  - 파일 확장자에 따라 적절한 파서 호출
  - 반환: 텍스트 문자열

- `_parse_excel(file_content: bytes) -> str`
  - Excel 파일 파싱
  - 모든 시트를 읽어 텍스트로 변환

- `_parse_csv(file_content: bytes, filename: str) -> str`
  - CSV 파일 파싱
  - 인코딩 자동 감지 (UTF-8, CP949, EUC-KR)

- `_parse_docx(file_content: bytes) -> str`
  - Word 문서(.docx) 파싱
  - 단락과 표 추출

- `_parse_doc(file_content: bytes, filename: str) -> str`
  - Word 문서(.doc) 파싱
  - HTML 형식으로 저장된 경우 BeautifulSoup 사용

- `_extract_text_from_html(html_content: str) -> str`
  - HTML에서 텍스트 추출
  - 스크립트, 스타일 태그 제거

- `parse_law_table_file(filename: str, file_content: bytes) -> List[Dict]`
  - `5-2.법령별` 문서 전용 파서
  - `LawTableParser` 사용

#### 사용 예시

```python
from rag.parsers.file_parser import FileParser

with open("document.xlsx", "rb") as f:
    content = f.read()

text = FileParser.parse_file("document.xlsx", content)
```

---

### 7. `parsers/law_table_parser.py` - 법령 테이블 파서

`5-2.법령별` 문서를 행 단위로 구조화하여 파싱하는 전용 파서입니다.

#### 주요 기능
- **HTML 테이블 파싱**: BeautifulSoup으로 HTML 테이블 추출
- **행 단위 구조화**: 각 테이블 행을 하나의 청크로 처리
- **메타데이터 추출**: 법령 묶음, 항목명, 조문 번호, 검토내용, 법령내용 등
- **임베딩 텍스트 생성**: 구조화된 데이터를 임베딩용 텍스트로 변환

#### 클래스: `LawTableParser`

#### 주요 메서드

- `parse_law_table(html_content: str, scenario: str, filename: str) -> List[Dict]`
  - HTML 테이블을 파싱하여 구조화된 청크 리스트 반환
  - 각 행은 하나의 딕셔너리로 변환

- `_parse_row(cells, scenario, law_group, filename) -> Dict`
  - 테이블 행을 파싱하여 구조화된 청크 메타데이터 생성

- `_extract_law_content(cell) -> tuple[str, List[str]]`
  - 법령내용 셀에서 법령 텍스트와 조문 번호 추출
  - `jonote` 클래스에서 조문 제목 추출
  - `tag1`, `tag2`, `tag3`, `tag4` 클래스에서 조문 내용 추출

- `_extract_review_content(cell) -> tuple[str, Dict]`
  - 검토내용 셀에서 검토 텍스트와 메타데이터 추출
  - `note1` 클래스에서 메타데이터 추출 (건축종류, 건축물용도, 건축주, 주요구조부, 건물특성)
  - `note2` 클래스에서 검토내용 추출

- `create_embedding_text(chunk: Dict) -> str`
  - 구조화된 청크를 임베딩용 텍스트로 변환
  - 시나리오, 법령 묶음, 조문, 항목, 검토내용, 법령내용, 용도, 건축종류 포함

#### 반환 데이터 구조

```python
{
    "id": "scenario|filename|law_group|no",
    "scenario": "신축_일반개인_다중주택",
    "law_group": "건축법",
    "article_ids": ["제60조", "제61조"],
    "item_name": "건축물의 높이 제한",
    "law_text": "법령 조문 원문...",
    "review_text": "검토내용 요약...",
    "no": 1,
    "filename": "5-2.법령별.doc",
    "building_type": "신축",
    "usage": "공동주택",
    "owner_type": "일반개인",
    "main_structure": "철근콘크리트",
    "building_characteristics": ["특성1", "특성2"]
}
```

#### 사용 예시

```python
from rag.parsers.law_table_parser import LawTableParser

with open("5-2.법령별.doc", "rb") as f:
    html_content = f.read().decode('utf-8')

chunks = LawTableParser.parse_law_table(
    html_content=html_content,
    scenario="신축_일반개인_다중주택",
    filename="5-2.법령별.doc"
)

# 임베딩용 텍스트 생성
for chunk in chunks:
    embed_text = LawTableParser.create_embedding_text(chunk)
```

---

### 8. `utils/retry.py` - 재시도 유틸리티

API 호출 실패 시 자동으로 재시도하는 데코레이터입니다.

#### 주요 기능
- **지수 백오프**: 재시도 간격이 지수적으로 증가
- **최대 재시도 횟수 설정**: 기본 3회
- **예외 타입 지정**: 특정 예외만 재시도
- **최대 지연 시간 제한**: 지연 시간이 너무 길어지지 않도록 제한

#### 함수: `retry_with_backoff`

```python
@retry_with_backoff(
    max_retries: int = 3,              # 최대 재시도 횟수
    initial_delay: float = 1.0,        # 초기 지연 시간 (초)
    max_delay: float = 10.0,           # 최대 지연 시간 (초)
    exponential_base: float = 2.0,     # 지수 증가 기준
    exceptions: tuple = (Exception,)    # 재시도할 예외 타입
)
```

#### 재시도 로직
1. 첫 번째 실패: `initial_delay` 초 대기
2. 두 번째 실패: `initial_delay * exponential_base` 초 대기
3. 세 번째 실패: `initial_delay * exponential_base^2` 초 대기
4. 최대 지연 시간은 `max_delay`로 제한

#### 사용 예시

```python
from rag.utils.retry import retry_with_backoff
from openai import APIError, RateLimitError

@retry_with_backoff(
    max_retries=3,
    initial_delay=1.0,
    max_delay=10.0,
    exceptions=(APIError, RateLimitError)
)
async def call_api():
    # API 호출 코드
    pass
```

---

## 🔧 설정 및 사용법

### 환경 변수

```bash
OPENAI_API_KEY=your_api_key_here
OPENAI_MODEL=gpt-4o-mini
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
CHUNK_SIZE=1000
CHUNK_OVERLAP=200
TOP_K_DOCUMENTS=5
SIMILARITY_THRESHOLD=0.3
```

### 전체 파이프라인 사용 예시

```python
from rag.chunking.chunker import Chunker
from rag.embedding.embedder import Embedder
from rag.retrieval.retriever import Retriever
from rag.llm.llm_client import LLMClient
from rag.parsers.file_parser import FileParser

# 1. 문서 파싱
with open("document.docx", "rb") as f:
    content = FileParser.parse_file("document.docx", f.read())

# 2. 텍스트 청킹
chunker = Chunker(chunk_size=1000, chunk_overlap=200)
chunks = chunker.chunk_text(content)

# 3. 임베딩 생성 및 저장
embedder = Embedder(api_key="your-api-key")
retriever = Retriever(vector_store_path="./vector_store")

for chunk in chunks:
    embedding = await embedder.embed_text(chunk)
    await retriever.add_document(
        embedding=embedding,
        content=chunk,
        metadata={"filename": "document.docx"}
    )

# 4. 질문 검색 및 답변 생성
query = "건축허가에 필요한 서류는?"
query_embedding = await embedder.embed_query(query)

results = await retriever.retrieve(
    query_embedding=query_embedding,
    folder_filter="신축_일반개인_다중주택",
    top_k=5
)

llm_client = LLMClient(api_key="your-api-key")
answer = await llm_client.generate_answer(
    query=query,
    chunks=results,
    scenario="신축_일반개인_다중주택"
)
```

## 📝 주요 특징

1. **구조화된 청킹**: 법령 테이블 문서는 행 단위로 구조화하여 파싱
2. **메타데이터 기반 필터링**: 폴더, 파일명, 시나리오 등으로 검색 범위 제한
3. **점수 부스팅**: 관련성 높은 문서에 가중치 적용
4. **안전한 오류 처리**: API 오류, 파일 손상 등에 대한 자동 복구
5. **비동기 처리**: 모든 API 호출은 비동기로 처리하여 성능 최적화
6. **재시도 로직**: 네트워크 오류 시 자동 재시도

## 🚀 성능 최적화

- **배치 임베딩**: 여러 텍스트를 한 번에 임베딩하여 API 호출 횟수 감소
- **메모리 기반 저장소**: 빠른 검색을 위한 인메모리 벡터 저장
- **비동기 처리**: I/O 작업의 병렬 처리
- **컨텍스트 길이 제한**: LLM 토큰 제한을 고려한 자동 축약

## 🔍 디버깅

각 모듈은 로깅을 지원합니다. 로그 레벨을 설정하여 디버깅 정보를 확인할 수 있습니다.

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 📚 참고 자료

- OpenAI Embedding API: https://platform.openai.com/docs/guides/embeddings
- OpenAI Chat API: https://platform.openai.com/docs/guides/text-generation
- FastAPI: https://fastapi.tiangolo.com/

