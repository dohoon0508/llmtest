# RAG 실습 프로젝트

React, FastAPI, OpenAI API를 사용한 RAG(Retrieval-Augmented Generation) 실습 프로젝트입니다.

## 프로젝트 구조

```
Rag_test/
├── frontend/              # React 프론트엔드
│   ├── src/
│   │   ├── components/    # React 컴포넌트
│   │   ├── App.jsx
│   │   └── main.jsx
│   └── package.json
│
├── backend/               # FastAPI 백엔드
│   ├── app/
│   │   ├── api/          # API 라우터 (Controller 계층)
│   │   ├── core/         # 설정 및 공통 기능
│   │   ├── models/       # 데이터 모델 (DTO)
│   │   ├── services/     # 비즈니스 로직 (Service 계층)
│   │   └── main.py
│   │
│   └── rag/              # RAG 독립 모듈
│       ├── chunking/     # 문서 청킹
│       ├── embedding/    # 임베딩 생성
│       ├── retrieval/    # 문서 검색
│       ├── llm/          # LLM 클라이언트
│       └── parsers/      # 파일 파서 (CSV, Excel 등)
│
└── documents/             # 문서 저장소
```

## 백엔드 아키텍처

**레이어드 아키텍처 (Layered Architecture)** 패턴을 사용했습니다.

### 계층 구조:
1. **API Layer (Controller)**: `app/api/` - HTTP 요청/응답 처리
2. **Service Layer**: `app/services/` - 비즈니스 로직 처리
3. **Model Layer (DTO)**: `app/models/` - 데이터 전송 객체
4. **RAG Module**: `rag/` - RAG 관련 독립 모듈

### 장점:
- 관심사의 분리 (Separation of Concerns)
- 유지보수성 향상
- 테스트 용이성
- 프론트엔드/백엔드와 RAG 모듈의 독립성 보장

## 주요 기능

1. **문서 관리**
   - 문서 업로드 및 저장 (텍스트, CSV, Excel 지원)
   - 문서 목록 조회
   - 문서 삭제
   - 지원 형식: `.txt`, `.md`, `.csv`, `.xlsx`, `.xls`

2. **RAG 쿼리**
   - 질문에 대한 답변 생성
   - 관련 문서 검색 및 표시
   - 청킹 단위 실시간 수정
   - 유사도 임계값 조정

3. **설정 관리**
   - 청킹 설정 (크기, 오버랩)
   - 유사도 설정 (임계값, 상위 K개)

4. **정확도 평가**
   - 문서 매칭 정확도 확인
   - Precision, Recall, F1 점수 계산

## 설치 및 실행

### 백엔드 설정

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

`.env` 파일 생성:
```bash
cp .env.example .env
# .env 파일에 OPENAI_API_KEY 입력
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

## 환경 변수

`.env` 파일에 다음 변수들을 설정하세요:

- `OPENAI_API_KEY`: OpenAI API 키
- `OPENAI_MODEL`: 사용할 LLM 모델 (기본값: gpt-4o-mini)
- `OPENAI_EMBEDDING_MODEL`: 사용할 임베딩 모델 (기본값: text-embedding-3-small)
- `CHUNK_SIZE`: 기본 청크 크기 (기본값: 1000)
- `CHUNK_OVERLAP`: 기본 청크 오버랩 (기본값: 200)
- `TOP_K_DOCUMENTS`: 기본 반환 문서 개수 (기본값: 5)
- `SIMILARITY_THRESHOLD`: 기본 유사도 임계값 (기본값: 0.7)

## 파일 형식 지원

### 텍스트 파일
- `.txt`, `.md`: 직접 텍스트로 처리

### CSV 파일
- 자동 인코딩 감지 (UTF-8, CP949, EUC-KR 등)
- 자동 구분자 감지 (쉼표, 세미콜론, 탭 등)
- 컬럼명과 각 행의 데이터를 구조화된 텍스트로 변환

### Excel 파일
- `.xlsx`, `.xls` 지원
- 모든 시트 자동 처리
- 각 시트별로 구조화된 텍스트로 변환
- 컬럼명과 행 데이터를 RAG에 적합한 형식으로 변환

## 실습 항목

1. **청킹 단위 수정**: 설정 탭에서 청크 크기와 오버랩 조정
2. **문서 의존도 수정**: 유사도 임계값과 상위 K개 문서 수 조정
3. **문서 매칭 정확도 확인**: 정확도 평가 탭에서 Precision, Recall, F1 점수 확인
4. **저장된 문서 응답**: 문서 업로드 후 질문하기 탭에서 질문하여 저장된 문서 기반 답변 확인
5. **다양한 파일 형식 실습**: CSV, Excel 파일을 업로드하여 구조화된 데이터를 RAG로 검색

