"""
xlsx 파일 청킹 테스트 스크립트
"""
import asyncio
import sys
import os
from pathlib import Path

# 프로젝트 루트를 경로에 추가
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from rag.parsers.file_parser import FileParser
from rag.chunking.chunker import Chunker
from app.core.config import settings

async def test_xlsx_chunking():
    """xlsx 파일 청킹 테스트"""
    print("=" * 60)
    print("xlsx 파일 청킹 테스트")
    print("=" * 60)
    
    documents_dir = Path(settings.DOCUMENTS_DIR)
    documents_dir.mkdir(exist_ok=True, parents=True)
    
    # xlsx 파일 찾기
    xlsx_files = list(documents_dir.glob("*.xlsx")) + list(documents_dir.glob("*.xls"))
    
    if not xlsx_files:
        print("❌ documents 폴더에 xlsx 파일이 없습니다.")
        print(f"   폴더 경로: {documents_dir.absolute()}")
        print(f"   폴더 내용: {list(documents_dir.iterdir())}")
        return False
    
    print(f"\n✅ {len(xlsx_files)}개의 Excel 파일을 찾았습니다:")
    for f in xlsx_files:
        print(f"   - {f.name}")
    
    # 첫 번째 xlsx 파일 테스트
    test_file = xlsx_files[0]
    print(f"\n📄 테스트 파일: {test_file.name}")
    print(f"   파일 크기: {test_file.stat().st_size / 1024:.2f} KB")
    
    try:
        # 1. 파일 파싱 테스트
        print("\n" + "=" * 60)
        print("1단계: 파일 파싱")
        print("=" * 60)
        
        with open(test_file, "rb") as f:
            content_bytes = f.read()
        
        parsed_text = FileParser.parse_file(test_file.name, content_bytes)
        print(f"✅ 파싱 성공!")
        print(f"   파싱된 텍스트 길이: {len(parsed_text)} 문자")
        print(f"   첫 500자 미리보기:")
        print("-" * 60)
        print(parsed_text[:500])
        print("-" * 60)
        
        # 2. 청킹 테스트 (일반 청킹)
        print("\n" + "=" * 60)
        print("2단계: 일반 청킹 테스트")
        print("=" * 60)
        
        chunker = Chunker(
            chunk_size=settings.CHUNK_SIZE,
            chunk_overlap=settings.CHUNK_OVERLAP,
            chunk_by_row=False
        )
        
        chunks_normal = chunker.chunk_text(parsed_text)
        print(f"✅ 일반 청킹 완료!")
        print(f"   청크 개수: {len(chunks_normal)}")
        for i, chunk in enumerate(chunks_normal[:3], 1):
            print(f"\n   청크 {i} ({len(chunk)} 문자):")
            print(f"   {chunk[:200]}...")
        
        # 3. Row 단위 청킹 테스트
        print("\n" + "=" * 60)
        print("3단계: Row 단위 청킹 테스트")
        print("=" * 60)
        
        chunker_row = Chunker(
            chunk_size=settings.CHUNK_SIZE,
            chunk_overlap=settings.CHUNK_OVERLAP,
            chunk_by_row=True
        )
        
        # Row 단위 청킹을 위한 메타데이터
        metadata = {"is_structured_data": True}
        chunks_row = chunker_row.chunk_text(parsed_text, metadata)
        print(f"✅ Row 단위 청킹 완료!")
        print(f"   청크 개수: {len(chunks_row)}")
        for i, chunk in enumerate(chunks_row[:3], 1):
            print(f"\n   청크 {i} ({len(chunk)} 문자):")
            print(f"   {chunk[:200]}...")
        
        # 4. 비교
        print("\n" + "=" * 60)
        print("4단계: 청킹 방식 비교")
        print("=" * 60)
        print(f"   일반 청킹: {len(chunks_normal)}개 청크")
        print(f"   Row 단위 청킹: {len(chunks_row)}개 청크")
        print(f"   차이: {abs(len(chunks_normal) - len(chunks_row))}개")
        
        if len(chunks_row) > len(chunks_normal):
            print("   ✅ Row 단위 청킹이 더 세밀하게 분할했습니다.")
        elif len(chunks_row) < len(chunks_normal):
            print("   ✅ 일반 청킹이 더 세밀하게 분할했습니다.")
        else:
            print("   ℹ️  두 방식의 청크 개수가 동일합니다.")
        
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
    result = asyncio.run(test_xlsx_chunking())
    sys.exit(0 if result else 1)

