import json
import hashlib
from datetime import datetime
from typing import List, Dict, Any
from pathlib import Path
from app.core.config import settings
from app.models.rag_models import DocumentInfo

class DocumentService:
    def __init__(self):
        self.documents_dir = Path(settings.DOCUMENTS_DIR)
        self.documents_dir.mkdir(exist_ok=True, parents=True)
    
    async def upload_document(
        self,
        filename: str,
        content: str,
        metadata: Dict[str, Any] = None,
        file_path: str = None
    ) -> DocumentInfo:
        """문서 업로드 (JSON만 사용, 벡터화 없음)"""
        import logging
        logger = logging.getLogger(__name__)
        
        # 폴더 정보 추출
        folder_name = None
        if metadata and "folder" in metadata:
            folder_name = metadata.get("folder")
        
        # JSON 파일만 처리
        if not filename.lower().endswith('.json'):
            logger.warning(f"JSON 파일만 지원합니다: {filename}")
            raise ValueError("JSON 파일만 업로드할 수 있습니다.")
        
        # 중복 체크: 메타데이터 파일에서 확인
        import unicodedata
        existing_doc_id = None
        folder_name_nfc = unicodedata.normalize('NFC', str(folder_name).strip()) if folder_name else ""
        
        for meta_file in self.documents_dir.glob("*.meta.json"):
            try:
                with open(meta_file, "r", encoding="utf-8") as f:
                    meta = json.load(f)
                    meta_folder = meta.get("metadata", {}).get("folder", "")
                    meta_filename = meta.get("filename", "")
                    meta_folder_nfc = unicodedata.normalize('NFC', str(meta_folder).strip()) if meta_folder else ""
                    
                    if meta_folder_nfc == folder_name_nfc and meta_filename == filename:
                        existing_doc_id = meta.get("id")
                        break
            except:
                continue
        
        # 이미 존재하는 문서가 있으면 기존 정보 반환
        if existing_doc_id:
            logger.info(f"문서가 이미 존재합니다: {folder_name}/{filename} (doc_id: {existing_doc_id})")
            meta_file = self.documents_dir / f"{existing_doc_id}.meta.json"
            if meta_file.exists():
                with open(meta_file, "r", encoding="utf-8") as f:
                    existing_meta = json.load(f)
                    return DocumentInfo(
                        id=existing_doc_id,
                        filename=filename,
                        chunk_count=0,  # JSON은 청크 개념 없음
                        created_at=existing_meta.get("created_at", datetime.now().isoformat())
                    )
        
        # doc_id 생성
        folder_str = folder_name or ""
        id_string = f"{folder_str}|{filename}"
        doc_id = hashlib.md5(id_string.encode('utf-8')).hexdigest()
        
        # 메타데이터 저장
        metadata_path = self.documents_dir / f"{doc_id}.meta.json"
        doc_metadata = {
            "id": doc_id,
            "filename": filename,
            "created_at": datetime.now().isoformat(),
            "metadata": metadata or {}
        }
        
        with open(metadata_path, "w", encoding="utf-8") as f:
            json.dump(doc_metadata, f, ensure_ascii=False, indent=2)
        
        logger.info(f"JSON 파일 메타데이터 저장 완료: {filename}")
        
        # JSON 파일은 RAGService의 JSON 인덱스에서 자동으로 로드되므로
        # 여기서는 메타데이터만 저장하고 완료
        return DocumentInfo(
            id=doc_id,
            filename=filename,
            chunk_count=0,  # JSON은 청크 개념 없음
            created_at=doc_metadata["created_at"]
        )
    
    def list_documents(self) -> List[DocumentInfo]:
        """저장된 문서 목록 조회"""
        documents = []
        for meta_file in self.documents_dir.glob("*.meta.json"):
            with open(meta_file, "r", encoding="utf-8") as f:
                meta = json.load(f)
                documents.append(DocumentInfo(**meta))
        return documents
    
    def get_document(self, doc_id: str) -> str:
        """문서 내용 조회"""
        # 먼저 메타데이터에서 원본 파일명 확인
        meta_path = self.documents_dir / f"{doc_id}.meta.json"
        if meta_path.exists():
            with open(meta_path, "r", encoding="utf-8") as f:
                meta = json.load(f)
                original_filename = meta.get("filename")
                
                # 원본 파일이 있으면 원본 파일 사용
                original_file_path = self.documents_dir / original_filename
                if original_file_path.exists():
                    if original_filename.lower().endswith(('.txt', '.md')):
                        with open(original_file_path, "r", encoding="utf-8") as f:
                            return f.read()
                    else:
                        # 바이너리 파일인 경우 파싱
                        with open(original_file_path, "rb") as f:
                            content_bytes = f.read()
                        from rag.parsers.file_parser import FileParser
                        return FileParser.parse_file(original_filename, content_bytes)
        
        # 메타데이터가 없거나 원본 파일이 없는 경우 txt 파일 확인
        doc_path = self.documents_dir / f"{doc_id}.txt"
        if doc_path.exists():
            with open(doc_path, "r", encoding="utf-8") as f:
                return f.read()
        
        raise FileNotFoundError(f"Document {doc_id} not found")
    
    def delete_document(self, doc_id: str) -> bool:
        """문서 삭제"""
        doc_path = self.documents_dir / f"{doc_id}.txt"
        meta_path = self.documents_dir / f"{doc_id}.meta.json"
        
        if doc_path.exists():
            doc_path.unlink()
        if meta_path.exists():
            meta_path.unlink()
        
        # JSON 파일은 RAGService의 JSON 인덱스에서 자동으로 관리되므로
        # 여기서는 메타데이터 파일만 삭제
        
        return True
    
    async def load_existing_documents(self):
        """documents 폴더에 있는 기존 JSON 파일들을 자동으로 로드 (JSON만 사용)"""
        import logging
        logger = logging.getLogger(__name__)
        
        logger.info("기존 JSON 문서 자동 로드 시작... (JSON만 처리)")
        
        # JSON만 사용하므로 벡터화 불필요
        # JSON 파일은 RAGService의 JSON 인덱스에서 자동으로 로드됨
        logger.info("JSON 파일은 RAGService 초기화 시 자동으로 로드됩니다. 별도 처리 불필요.")
        
        loaded_count = 0
        skipped_count = 0
        
        # JSON 파일은 RAGService의 JSON 인덱스에서 자동으로 로드되므로
        # 여기서는 벡터화 작업을 하지 않습니다.
        logger.info("JSON 파일은 RAGService 초기화 시 JSON 인덱스에 자동 로드됩니다.")
        
        logger.info(f"기존 문서 자동 로드 완료: {loaded_count}개 로드, {skipped_count}개 스킵")
        return loaded_count
