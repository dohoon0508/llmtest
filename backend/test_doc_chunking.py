"""
.doc 파일 청킹 테스트 스크립트
"""
import sys
import os
from pathlib import Path

# 프로젝트 루트를 경로에 추가
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.config import settings
from rag.parsers.file_parser import FileParser
from rag.chunking.chunker import Chunker

def test_doc_chunking():
    """doc 파일 청킹 테스트"""
    print("=" * 60)
    print(".doc 파일 청킹 테스트")
    print("=" * 60)
    
    documents_dir = Path(settings.DOCUMENTS_DIR)
    documents_dir.mkdir(exist_ok=True, parents=True)
    
    # .doc 파일 찾기
    doc_files = list(documents_dir.glob("*.doc"))
    
    if not doc_files:
        print("❌ documents 폴더에 .doc 파일이 없습니다.")
        print(f"   폴더 경로: {documents_dir.absolute()}")
        return False
    
    print(f"\n✅ {len(doc_files)}개의 .doc 파일을 찾았습니다:")
    for f in doc_files:
        print(f"   - {f.name}")
    
    # 첫 번째 .doc 파일 테스트
    test_file = doc_files[0]
    print(f"\n📄 테스트 파일: {test_file.name}")
    print(f"   파일 크기: {test_file.stat().st_size / 1024:.2f} KB")
    
    try:
        # 1. 파일 파싱 테스트
        print("\n" + "=" * 60)
        print("1단계: 파일 파싱")
        print("=" * 60)
        
        with open(test_file, "rb") as f:
            content_bytes = f.read()
        
        try:
            parsed_text = FileParser.parse_file(test_file.name, content_bytes)
            print(f"✅ 파싱 성공!")
            print(f"   파싱된 텍스트 길이: {len(parsed_text)} 문자")
            print(f"   첫 500자 미리보기:")
            print("-" * 60)
            print(parsed_text[:500])
            print("-" * 60)
        except Exception as e:
            print(f"❌ 파싱 실패: {str(e)}")
            print("\n💡 .doc 파일은 바이너리 형식이라 텍스트로 직접 파싱할 수 없습니다.")
            print("   python-docx2txt 또는 textract 라이브러리가 필요합니다.")
            return False
        
        # 2. 청킹 테스트
        print("\n" + "=" * 60)
        print("2단계: 청킹 테스트")
        print("=" * 60)
        
        chunker = Chunker(
            chunk_size=settings.CHUNK_SIZE,
            chunk_overlap=settings.CHUNK_OVERLAP,
            chunk_by_row=False
        )
        
        chunks = chunker.chunk_text(parsed_text)
        print(f"✅ 청킹 완료!")
        print(f"   청크 개수: {len(chunks)}")
        for i, chunk in enumerate(chunks[:3], 1):
            print(f"\n   청크 {i} ({len(chunk)} 문자):")
            print(f"   {chunk[:200]}...")
        
        print("\n" + "=" * 60)
        print("✅ 모든 테스트 통과!")
        print("=" * 60)
        return True
        
    except Exception as e:
        print(f"\n❌ 오류 발생: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    result = test_doc_chunking()
    sys.exit(0 if result else 1)

