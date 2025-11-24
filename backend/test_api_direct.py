"""
직접 API 테스트 스크립트
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.rag_service import RAGService
from app.models.rag_models import QueryRequest

async def test_direct():
    """직접 RAG 서비스 테스트"""
    print("=" * 60)
    print("직접 RAG 서비스 테스트")
    print("=" * 60)
    
    try:
        rag_service = RAGService()
        
        query = "개인이 신축 건물을 지을 때 건축허가에 필요한 서류나 참고할 만한 법령을 알려줘"
        print(f"\n질문: {query}\n")
        
        request = QueryRequest(query=query)
        response = await rag_service.query(request)
        
        print("=" * 60)
        print("응답:")
        print("=" * 60)
        print(response.answer)
        print(f"\n참고 문서: {len(response.chunks)}개")
        print(f"출처: {response.sources}")
        
        return True
    except Exception as e:
        print(f"\n❌ 오류 발생: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    result = asyncio.run(test_direct())
    sys.exit(0 if result else 1)

