from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    # OpenAI 설정
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o-mini"
    OPENAI_EMBEDDING_MODEL: str = "text-embedding-3-small"
    
    # RAG 설정
    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 200
    TOP_K_DOCUMENTS: int = 5
    SIMILARITY_THRESHOLD: float = 0.3  # 더 많은 문서를 검색하기 위해 낮춤
    
    # 문서 저장 경로
    DOCUMENTS_DIR: str = "documents"
    VECTOR_STORE_PATH: str = "vector_store"
    
    # CORS 설정
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:3001", "http://localhost:3002", "http://localhost:5173"]
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()

