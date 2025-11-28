#!/bin/bash
# 이전 벡터화 파일들 삭제 스크립트

echo "🧹 이전 벡터화 파일들 삭제 시작..."

# documents 폴더의 .meta.json 파일 삭제
echo "📄 .meta.json 파일 삭제 중..."
find documents -maxdepth 1 -name "*.meta.json" -type f -delete
echo "✅ .meta.json 파일 삭제 완료"

# documents 폴더의 해시 .txt 파일 삭제 (32자 해시 파일명)
echo "📄 해시 .txt 파일 삭제 중..."
find documents -maxdepth 1 -name "????????????????????????????????.txt" -type f -delete
echo "✅ 해시 .txt 파일 삭제 완료"

# vector_store 폴더의 벡터 파일 삭제
echo "🗄️ 벡터 저장소 파일 삭제 중..."
rm -f vector_store/vectors.json
rm -f vector_store/vectors.json.backup.*
echo "✅ 벡터 저장소 파일 삭제 완료"

echo "✨ 정리 완료!"
