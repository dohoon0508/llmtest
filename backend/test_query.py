"""
테스트 스크립트: 소방 스프링클러 설치기준 질문 테스트
"""
import asyncio
import sys
import os

# 프로젝트 루트를 경로에 추가
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.rag_service import RAGService
from app.models.rag_models import QueryRequest

async def test_query():
    """테스트 쿼리 실행"""
    print("=" * 50)
    print("RAG 시스템 테스트 시작")
    print("=" * 50)
    
    rag_service = RAGService()
    
    query = "소방 스프링클러 설치기준 연면적 혹은 건물용도는?"
    
    print(f"\n질문: {query}\n")
    
    try:
        request = QueryRequest(query=query)
        response = await rag_service.query(request)
        
        print("=" * 50)
        print("응답:")
        print("=" * 50)
        print(response.answer)
        print("\n" + "=" * 50)
        print(f"참고 문서: {len(response.chunks)}개")
        print("=" * 50)
        
        for i, chunk in enumerate(response.chunks, 1):
            print(f"\n[{i}] {chunk.metadata.get('filename', 'unknown')}")
            print(f"    유사도: {chunk.score * 100:.2f}%")
            print(f"    내용: {chunk.content[:100]}...")
        
        print("\n" + "=" * 50)
        print("테스트 성공!")
        print("=" * 50)
        
    except Exception as e:
        print(f"\n❌ 오류 발생: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    result = asyncio.run(test_query())
    sys.exit(0 if result else 1)

