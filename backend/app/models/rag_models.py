from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class QueryRequest(BaseModel):
    query: str = Field(..., description="사용자 질문")
    top_k: Optional[int] = Field(None, description="반환할 문서 개수")
    similarity_threshold: Optional[float] = Field(None, description="유사도 임계값")
    folder: Optional[str] = Field(None, description="검색할 폴더명 (건물 타입, 예: 다중주택)")
    region: Optional[str] = Field(None, description="검색할 지역명 (예: 전주시)")

class DocumentChunk(BaseModel):
    content: str
    metadata: Dict[str, Any]
    score: Optional[float] = None

class QueryResponse(BaseModel):
    answer: str
    chunks: List[DocumentChunk]
    sources: List[str]

class ChunkConfig(BaseModel):
    chunk_size: int = Field(..., ge=100, le=5000, description="청크 크기")
    chunk_overlap: int = Field(..., ge=0, le=1000, description="청크 오버랩")
    chunk_by_row: bool = Field(False, description="Row 단위 청킹 (CSV/Excel용)")

class SimilarityConfig(BaseModel):
    similarity_threshold: float = Field(..., ge=0.0, le=1.0, description="유사도 임계값")
    top_k: int = Field(..., ge=1, le=20, description="상위 K개 문서")

class RAGWeightConfig(BaseModel):
    similarity_weight: float = Field(1.0, ge=0.0, le=2.0, description="유사도 가중치")
    recency_weight: float = Field(0.0, ge=0.0, le=1.0, description="최신성 가중치")
    source_weight: float = Field(0.0, ge=0.0, le=1.0, description="출처 가중치")

class DocumentUpload(BaseModel):
    filename: str
    content: str
    metadata: Optional[Dict[str, Any]] = None

class DocumentInfo(BaseModel):
    id: str
    filename: str
    chunk_count: int
    created_at: str

