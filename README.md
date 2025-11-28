# 건축허가 자동화 시스템 - RAG 기반

React, FastAPI, OpenAI API를 사용한 RAG(Retrieval-Augmented Generation) 기반 건축허가 자동화 시스템입니다.

## 🎯 시스템 개요

이 시스템은 **JSON 기반 키워드 검색**과 **LLM 답변 생성**을 결합한 RAG 시스템입니다. 건축 양식별 법령 Q&A JSON 파일과 지역별 조례 JSON 파일을 활용하여 빠르고 정확한 답변을 제공합니다.

### 주요 특징
- ⚡ **빠른 응답**: JSON 키워드 검색으로 임베딩 없이 즉시 검색
- 🎯 **정확한 필터링**: 건물 타입 + 지역 조합 검색
- 📚 **구조화된 데이터**: JSON 형식의 Q&A 데이터 활용
- 🔍 **스마트 검색**: 키워드 매칭, 질문 매칭, 정확한 매칭 우선순위

## 🏗️ RAG 아키텍처

### 시스템 구조

```
┌─────────────────────────────────────────────────────────┐
│                    Frontend (React)                      │
│  - 건축 양식 선택 (드롭다운)                              │
│  - 지역 선택 (드롭다운, 선택사항)                          │
│  - 질문 입력 및 답변 표시                                 │
└──────────────────────┬──────────────────────────────────┘
                       │ HTTP Request
                       ▼
┌─────────────────────────────────────────────────────────┐
│              Backend API (FastAPI)                       │
│  ┌──────────────────────────────────────────────────┐   │
│  │  RAG Router (/api/rag/query)                     │   │
│  └──────────────┬───────────────────────────────────┘   │
│                 │                                         │
│  ┌──────────────▼───────────────────────────────────┐   │
│  │  RAG Service                                      │   │
│  │  1. JSON 인덱스 검색 (키워드 기반)                 │   │
│  │  2. 검색 결과를 LLM에 전달                         │   │
│  │  3. 답변 생성 및 반환                              │   │
│  └──────────────┬───────────────────────────────────┘   │
└─────────────────┼───────────────────────────────────────┘
                  │
        ┌─────────┴─────────┐
        │                   │
        ▼                   ▼
┌──────────────┐    ┌──────────────┐
│ JSON Index   │    │ LLM Client   │
│ (키워드 검색) │    │ (답변 생성)   │
└──────────────┘    └──────────────┘
```

### RAG 파이프라인 흐름

```
1. 사용자 질문 입력
   ↓
2. 건축 양식 선택 (필수) + 지역 선택 (선택)
   ↓
3. JSON 인덱스에서 키워드 검색
   - 건물 타입 폴더의 Construction_law_qa.json 검색
   - 지역 폴더의 조례 JSON 검색 (지역 선택 시)
   - 키워드 매칭 점수 계산
   - 질문 매칭 점수 계산
   - 정확한 질문 매칭 우선순위
   ↓
4. 상위 K개 결과 선택 (점수 정규화: 0.0~1.0)
   ↓
5. 검색 결과를 LLM 컨텍스트로 전달
   ↓
6. LLM이 컨텍스트 기반 답변 생성
   ↓
7. 답변 + 참고 문서 반환
```

## 📁 프로젝트 구조

```
Rag_test/
├── frontend/              # React 프론트엔드
│   ├── src/
│   │   ├── components/
│   │   │   ├── ChatSection.jsx    # 채팅 인터페이스
│   │   │   ├── Sidebar.jsx        # 건축 양식/지역 선택
│   │   │   └── ...
│   │   ├── App.jsx
│   │   └── main.jsx
│   └── package.json
│
├── backend/               # FastAPI 백엔드
│   ├── app/
│   │   ├── api/          # API 라우터
│   │   │   ├── rag_router.py      # RAG 쿼리 엔드포인트
│   │   │   └── document_router.py # 문서 관리 엔드포인트
│   │   ├── core/         # 설정
│   │   │   └── config.py
│   │   ├── models/       # 데이터 모델
│   │   │   └── rag_models.py
│   │   ├── services/     # 비즈니스 로직
│   │   │   ├── rag_service.py     # RAG 파이프라인 오케스트레이션
│   │   │   └── document_service.py # 문서 관리
│   │   └── main.py
│   │
│   └── rag/              # RAG 독립 모듈
│       ├── retrieval/
│       │   ├── json_index.py      # JSON 키워드 인덱스 (핵심)
│       │   └── retriever.py       # 벡터 검색 (현재 미사용)
│       ├── llm/
│       │   ├── llm_client.py      # OpenAI LLM 클라이언트
│       │   └── prompts.py         # 프롬프트 템플릿
│       ├── parsers/
│       │   └── file_parser.py     # JSON 파일 파서
│       └── README.md              # RAG 모듈 상세 문서
│
└── documents/             # 문서 저장소
    ├── {건축양식}/        # 건축 양식별 폴더
    │   └── Construction_law_qa.json  # 법령 Q&A JSON
    └── region/            # 지역별 조례
        └── Jeonju_Construction_Ordinance.json
```

## 🔑 핵심 RAG 모듈

### 1. JSON 인덱스 (`rag/retrieval/json_index.py`)

JSON 파일을 키워드 기반으로 빠르게 검색하는 인덱스입니다.

#### 주요 기능
- **키워드 인덱싱**: JSON 항목의 `keywords` 필드를 인덱싱
- **질문 인덱싱**: `question` 필드의 주요 단어 추출 및 인덱싱
- **카테고리 인덱싱**: `category` 필드로 분류 검색
- **빠른 검색**: 키워드 매칭으로 즉시 검색 (임베딩 불필요)
- **점수 정규화**: 검색 점수를 0.0~1.0 범위로 정규화

#### 검색 우선순위
1. **정확한 질문 매칭** (점수 +5.0): 질문이 정확히 일치
2. **질문 키워드 매칭** (점수 +2.0): 질문의 주요 단어 매칭
3. **키워드 매칭** (점수 +1.0): 일반 키워드 매칭

#### 사용 예시

```python
from rag.retrieval.json_index import JSONIndex

# 인덱스 초기화
json_index = JSONIndex()

# JSON 파일 로드
json_index.load_json_file(
    file_path=Path("documents/다중주택/Construction_law_qa.json"),
    folder="다중주택"
)

# 검색
results = json_index.search(
    query="건축허가에 필요한 서류는?",
    folder_filter="다중주택",
    region_filter="전주시",  # 선택사항
    top_k=5
)
```

### 2. RAG 서비스 (`app/services/rag_service.py`)

RAG 파이프라인을 오케스트레이션하는 서비스입니다.

#### 주요 기능
- **JSON 인덱스 초기화**: 서버 시작 시 모든 JSON 파일 자동 로드
- **검색 실행**: JSON 인덱스에서 키워드 검색
- **LLM 답변 생성**: 검색 결과를 LLM에 전달하여 답변 생성
- **에러 처리**: 안전한 오류 처리 및 사용자 친화적 메시지

#### 파이프라인

```python
class RAGService:
    def __init__(self):
        # JSON 인덱스 초기화
        self.json_index = JSONIndex()
        self._load_json_index()  # 모든 JSON 파일 로드
        
        # LLM 클라이언트 초기화
        self.llm_client = LLMClient(...)
    
    async def query(self, request: QueryRequest):
        # 1. JSON 인덱스 검색
        json_results = self.json_index.search(
            query=request.query,
            folder_filter=request.folder,
            region_filter=request.region,
            top_k=5
        )
        
        # 2. LLM 답변 생성
        answer = await self.llm_client.generate_answer(
            query=request.query,
            context=format_context(json_results),
            scenario=request.folder,
            region=request.region
        )
        
        return answer
```

### 3. LLM 클라이언트 (`rag/llm/llm_client.py`)

OpenAI LLM을 사용하여 답변을 생성합니다.

#### 주요 기능
- **컨텍스트 기반 답변**: 검색된 JSON 결과를 컨텍스트로 사용
- **프롬프트 템플릿**: 구조화된 프롬프트로 일관된 답변 생성
- **타임아웃 처리**: 20초 타임아웃으로 빠른 실패
- **에러 처리**: API 오류 시 사용자 친화적 메시지 반환

### 4. 프롬프트 템플릿 (`rag/llm/prompts.py`)

LLM에 전달할 프롬프트를 생성합니다.

#### 프롬프트 구조
- **시스템 프롬프트**: AI 역할 정의 (건축 인허가 실무 도우미)
- **사용자 프롬프트**: 시나리오, 컨텍스트, 질문 포함
- **지역 정보**: 지역 선택 시 프롬프트에 포함

## 📊 JSON 데이터 구조

### 건축 양식별 Q&A JSON (`Construction_law_qa.json`)

```json
[
  {
    "id": "qa_001",
    "category": "건축허가",
    "question": "건축허가에 필요한 서류는?",
    "keywords": ["건축허가", "서류", "신청"],
    "answer": "건축허가 신청 시 필요한 서류는...",
    "legal_basis": ["건축법 제11조", "건축법 제23조"],
    "reference_document": "건축허가 신청서",
    "application_scope": "신축 건축물"
  }
]
```

### 지역별 조례 JSON (`Jeonju_Construction_Ordinance.json`)

```json
[
  {
    "id": "ordinance_001",
    "title": "전주시 건축 조례",
    "question": "전주시 건축물 높이 제한은?",
    "keywords": ["높이", "제한", "전주시"],
    "answer": "전주시 건축물 높이 제한은...",
    "category": "건축물 높이",
    "jurisdiction": "전주시",
    "regulation_type": "조례"
  }
]
```

## 🚀 설치 및 실행

### 백엔드 설정

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

`.env` 파일 생성:
```bash
OPENAI_API_KEY=your_api_key_here
OPENAI_MODEL=gpt-4o-mini
OPENAI_EMBEDDING_MODEL=text-embedding-3-small  # 현재 미사용
DOCUMENTS_DIR=documents
CORS_ORIGINS=["http://localhost:5173"]
```

백엔드 실행:
```bash
uvicorn app.main:app --reload --port 8000
```

### 프론트엔드 설정

```bash
cd frontend
npm install
npm run dev
```

## 📝 사용 방법

### 1. 건축 양식 선택
- 왼쪽 사이드바에서 건축 양식을 선택합니다 (예: "다중주택", "단독주택")
- 각 건축 양식은 `documents/{건축양식}/Construction_law_qa.json` 파일과 매핑됩니다

### 2. 지역 선택 (선택사항)
- 왼쪽 사이드바에서 지역을 선택합니다 (예: "전주시")
- 지역 선택 시 해당 지역의 조례 JSON도 함께 검색됩니다
- 현재 지원 지역: 전주시

### 3. 질문 입력
- 채팅창에 질문을 입력합니다
- 예: "건축허가에 필요한 서류는?", "주차장 설치 기준은?"

### 4. 답변 확인
- LLM이 검색된 JSON 데이터를 기반으로 답변을 생성합니다
- 참고 문서 섹션에서 검색된 문서와 점수를 확인할 수 있습니다

## 🔍 검색 동작 원리

### JSON 인덱스 검색 과정

1. **키워드 추출**: 질문에서 주요 키워드 추출 (한글, 영문, 숫자)
2. **인덱스 조회**: 키워드 인덱스에서 매칭되는 항목 찾기
3. **점수 계산**:
   - 키워드 매칭: +1.0
   - 질문 키워드 매칭: +2.0
   - 정확한 질문 매칭: +5.0
4. **폴더 필터링**: 선택한 건축 양식 폴더의 JSON만 검색
5. **지역 필터링**: 지역 선택 시 해당 지역 JSON도 검색
6. **점수 정규화**: 최고 점수를 1.0으로 하고 나머지를 상대적으로 변환
7. **상위 K개 선택**: 정규화된 점수 순으로 정렬하여 상위 K개 반환

### 검색 예시

```
질문: "건축허가에 필요한 서류는?"
건축 양식: "다중주택"
지역: "전주시"

검색 과정:
1. 키워드 추출: ["건축허가", "필요", "서류"]
2. "다중주택" 폴더의 Construction_law_qa.json 검색
3. "전주시" 폴더의 Jeonju_Construction_Ordinance.json 검색
4. 키워드 매칭 항목 찾기
5. 점수 계산 및 정규화
6. 상위 5개 결과 반환
```

## 🎯 주요 기능

### 1. 빠른 검색
- JSON 키워드 인덱스로 즉시 검색 (임베딩 불필요)
- 평균 응답 시간: 1~3초

### 2. 정확한 필터링
- 건물 타입별 필터링 (23개 건축 양식)
- 지역별 필터링 (현재 전주시 지원)
- 건물 타입 + 지역 조합 검색

### 3. 스마트 매칭
- 정확한 질문 매칭 우선
- 키워드 매칭으로 관련 문서 검색
- 점수 기반 정렬

### 4. 구조화된 답변
- 마크다운 형식 답변
- 법령 근거 명시
- 참고 문서 표시

## 📚 API 엔드포인트

### RAG 쿼리

```http
POST /api/rag/query
Content-Type: application/json

{
  "query": "건축허가에 필요한 서류는?",
  "folder": "다중주택",
  "region": "전주시",
  "top_k": 5
}
```

**응답:**
```json
{
  "answer": "건축허가 신청 시 필요한 서류는...",
  "chunks": [
    {
      "content": "질문: 건축허가에 필요한 서류는?\n답변: ...",
      "metadata": {
        "folder": "다중주택",
        "filename": "Construction_law_qa.json",
        "category": "건축허가",
        "score": 1.0
      },
      "score": 1.0
    }
  ],
  "sources": ["다중주택/Construction_law_qa.json"]
}
```

## 🔧 설정

### 환경 변수 (`.env`)

```bash
# OpenAI 설정
OPENAI_API_KEY=your_api_key_here
OPENAI_MODEL=gpt-4o-mini

# 문서 경로
DOCUMENTS_DIR=documents

# CORS 설정
CORS_ORIGINS=["http://localhost:5173"]
```

## 📈 성능 최적화

### 현재 구현된 최적화
- ✅ JSON 키워드 검색 (임베딩 불필요)
- ✅ 점수 정규화 (0.0~1.0 범위)
- ✅ 조기 종료 (충분한 결과 발견 시)
- ✅ LLM 타임아웃 (20초)
- ✅ 컨텍스트 길이 제한 (12000자)

### 성능 지표
- **검색 시간**: 평균 0.01~0.1초 (JSON 인덱스)
- **LLM 응답 시간**: 평균 2~5초
- **전체 응답 시간**: 평균 3~6초

## 🛠️ 개발 가이드

### JSON 파일 추가 방법

1. **건축 양식별 Q&A 추가**
   - `documents/{건축양식}/Construction_law_qa.json` 파일에 항목 추가
   - 서버 재시작 시 자동으로 인덱싱됨

2. **지역별 조례 추가**
   - `documents/region/{지역명}_Construction_Ordinance.json` 파일 추가
   - `rag_service.py`의 `region_file_mapping`에 지역명 매핑 추가

### RAG 모듈 확장

자세한 내용은 `backend/rag/README.md`를 참고하세요.

## 📄 라이선스

이 프로젝트는 실습 목적으로 제작되었습니다.
