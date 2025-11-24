"""
설정 확인 스크립트
"""
import sys
import os
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.config import settings

print("=" * 60)
print("설정 확인")
print("=" * 60)

print(f"\n📁 문서 폴더: {Path(settings.DOCUMENTS_DIR).absolute()}")
print(f"📁 벡터 저장소: {Path(settings.VECTOR_STORE_PATH).absolute()}")

print(f"\n🔑 OpenAI API 키: ", end="")
if settings.OPENAI_API_KEY and settings.OPENAI_API_KEY != "":
    print(f"✅ 설정됨 ({settings.OPENAI_API_KEY[:10]}...)")
else:
    print("❌ 미설정")

print(f"\n🤖 LLM 모델: {settings.OPENAI_MODEL}")
print(f"📊 임베딩 모델: {settings.OPENAI_EMBEDDING_MODEL}")

print(f"\n⚙️  RAG 설정:")
print(f"   - 청크 크기: {settings.CHUNK_SIZE}")
print(f"   - 청크 오버랩: {settings.CHUNK_OVERLAP}")
print(f"   - 상위 K개: {settings.TOP_K_DOCUMENTS}")
print(f"   - 유사도 임계값: {settings.SIMILARITY_THRESHOLD}")

# 문서 확인
documents_dir = Path(settings.DOCUMENTS_DIR)
if documents_dir.exists():
    files = list(documents_dir.glob("*"))
    files = [f for f in files if not f.name.endswith('.meta.json')]
    print(f"\n📄 documents 폴더 파일: {len(files)}개")
    for f in files[:5]:
        print(f"   - {f.name}")
    if len(files) > 5:
        print(f"   ... 외 {len(files) - 5}개")
else:
    print(f"\n📄 documents 폴더 없음")

# 벡터 저장소 확인
vector_store = Path(settings.VECTOR_STORE_PATH) / "vectors.json"
if vector_store.exists():
    import json
    with open(vector_store, "r", encoding="utf-8") as f:
        data = json.load(f)
        vector_count = len(data.get("vectors", []))
    print(f"\n🔍 벡터 저장소: {vector_count}개 벡터")
else:
    print(f"\n🔍 벡터 저장소: 비어있음")

print("\n" + "=" * 60)

