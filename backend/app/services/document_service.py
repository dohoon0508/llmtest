import json
import hashlib
from datetime import datetime
from typing import List, Dict, Any
from pathlib import Path
from app.core.config import settings
from app.models.rag_models import DocumentInfo
from rag.chunking.chunker import Chunker
from rag.embedding.embedder import Embedder
from rag.retrieval.retriever import Retriever

class DocumentService:
    def __init__(self):
        self.documents_dir = Path(settings.DOCUMENTS_DIR)
        self.documents_dir.mkdir(exist_ok=True, parents=True)
        
        self.chunker = Chunker(
            chunk_size=settings.CHUNK_SIZE,
            chunk_overlap=settings.CHUNK_OVERLAP
        )
        self.embedder = Embedder(
            api_key=settings.OPENAI_API_KEY,
            model=settings.OPENAI_EMBEDDING_MODEL
        )
        self.retriever = Retriever(
            vector_store_path=settings.VECTOR_STORE_PATH,
            top_k=settings.TOP_K_DOCUMENTS,
            similarity_threshold=settings.SIMILARITY_THRESHOLD
        )
    
    async def upload_document(
        self,
        filename: str,
        content: str,
        metadata: Dict[str, Any] = None,
        file_path: str = None
    ) -> DocumentInfo:
        """문서 업로드 및 벡터화"""
        # 폴더 정보 추출
        folder_name = None
        if metadata and "folder" in metadata:
            folder_name = metadata.get("folder")
        
        # 중복 체크: 벡터 저장소에서 같은 폴더+파일명의 문서가 이미 있는지 확인
        existing_doc_id = None
        for meta in self.retriever.metadatas:
            meta_folder = meta.get("folder", "")
            meta_filename = meta.get("filename", "")
            
            # 유니코드 정규화하여 비교
            import unicodedata
            if folder_name and meta_folder:
                meta_folder_nfc = unicodedata.normalize('NFC', str(meta_folder).strip())
                folder_name_nfc = unicodedata.normalize('NFC', str(folder_name).strip())
                if meta_folder_nfc == folder_name_nfc and meta_filename == filename:
                    existing_doc_id = meta.get("source")
                    break
        
        # 이미 존재하는 문서가 있으면 기존 정보 반환 (새 파일 생성 안 함)
        if existing_doc_id:
            import logging
            logger = logging.getLogger(__name__)
            logger.info(f"문서가 이미 존재합니다: {folder_name}/{filename} (doc_id: {existing_doc_id})")
            
            # 기존 메타데이터 파일 찾기
            for meta_file in self.documents_dir.glob(f"{existing_doc_id}.meta.json"):
                with open(meta_file, "r", encoding="utf-8") as f:
                    existing_meta = json.load(f)
                    return DocumentInfo(
                        id=existing_doc_id,
                        filename=filename,
                        chunk_count=len([m for m in self.retriever.metadatas if m.get("source") == existing_doc_id]),
                        created_at=existing_meta.get("created_at", datetime.now().isoformat())
                    )
        
        # 한국어 파일명을 포함한 안전한 doc_id 생성 (타임스탬프 제거, 파일명+폴더 해시 사용)
        # 같은 파일은 항상 같은 ID를 가지도록 함
        folder_str = folder_name or ""
        id_string = f"{folder_str}|{filename}"
        doc_id = hashlib.md5(id_string.encode('utf-8')).hexdigest()
        
        # 원본 파일이 이미 documents 폴더에 있으면 txt 파일 저장 생략
        # 원본 파일만 유지하고, 파싱된 내용은 벡터 저장소에만 저장
        original_file_path = self.documents_dir / filename
        save_txt_file = not original_file_path.exists()
        
        if save_txt_file:
            # 원본 파일이 없는 경우에만 txt 파일 저장 (텍스트 파일인 경우)
            doc_path = self.documents_dir / f"{doc_id}.txt"
            with open(doc_path, "w", encoding="utf-8") as f:
                f.write(content)
        
        # 메타데이터는 최소한만 저장 (벡터 저장소에 이미 있음)
        # 원본 파일명만 추적하기 위한 최소 메타데이터
        metadata_path = self.documents_dir / f"{doc_id}.meta.json"
        doc_metadata = {
            "id": doc_id,
            "filename": filename,
            "created_at": datetime.now().isoformat(),
            "metadata": metadata or {}
        }
        
        with open(metadata_path, "w", encoding="utf-8") as f:
            json.dump(doc_metadata, f, ensure_ascii=False, indent=2)
        
        # 폴더 정보 추출 (시나리오 키)
        folder_name = None
        if metadata and "folder" in metadata:
            folder_name = metadata.get("folder")
        elif "/" in filename or "\\" in filename:
            path_parts = filename.replace("\\", "/").split("/")
            if len(path_parts) > 1:
                folder_name = "/".join(path_parts[:-1])
        
        # 5-2.법령별 문서는 구조화된 파서 사용
        if filename.startswith("5-2.") and filename.lower().endswith(('.doc', '.docx')):
            try:
                from rag.parsers.file_parser import FileParser
                from rag.parsers.law_table_parser import LawTableParser
                
                # 파일 내용 다시 읽기 (바이너리)
                import logging
                logger = logging.getLogger(__name__)
                
                # 원본 파일 경로 찾기 (file_path가 제공되면 사용, 아니면 폴더 내에서 찾기)
                if file_path:
                    from pathlib import Path
                    original_file = Path(file_path)
                else:
                    original_file = self.documents_dir / folder_name / filename if folder_name else self.documents_dir / filename
                
                if original_file.exists():
                    with open(original_file, "rb") as f:
                        file_content_bytes = f.read()
                    
                    # HTML로 디코딩
                    html_content = file_content_bytes.decode('utf-8')
                    if '<html' not in html_content.lower():
                        for encoding in ['cp949', 'euc-kr']:
                            try:
                                html_content = file_content_bytes.decode(encoding)
                                if '<html' in html_content.lower() or '<table' in html_content.lower():
                                    break
                            except:
                                continue
                    
                    # 구조화된 파싱
                    structured_chunks = LawTableParser.parse_law_table(
                        html_content=html_content,
                        scenario=folder_name or "",
                        filename=filename
                    )
                    
                    if structured_chunks:
                        logger.info(f"구조화된 파싱 성공: {len(structured_chunks)}개 청크 생성")
                        
                        # 구조화된 청크를 벡터 저장소에 추가
                        for structured_chunk in structured_chunks:
                            # 구조화된 임베딩 텍스트 생성
                            embed_text = LawTableParser.create_embedding_text(structured_chunk)
                            embedding = await self.embedder.embed_text(embed_text)
                            
                            # 메타데이터 구성 (구조화된 필드 포함)
                            chunk_metadata = {
                                "source": doc_id,
                                "filename": filename,
                                "folder": folder_name,
                                "created_at": datetime.now().isoformat(),
                                **structured_chunk  # scenario, law_group, item_name, article_ids, law_text, review_text 등
                            }
                            
                            await self.retriever.add_document(
                                embedding=embedding,
                                content=structured_chunk.get("review_text", "") + "\n\n" + structured_chunk.get("law_text", ""),
                                metadata=chunk_metadata
                            )
                        
                        return DocumentInfo(
                            id=doc_id,
                            filename=filename,
                            chunk_count=len(structured_chunks),
                            created_at=doc_metadata["created_at"]
                        )
                    else:
                        logger.warning(f"구조화된 파싱 결과가 비어있습니다. 기본 청킹 사용: {filename}")
                else:
                    logger.warning(f"원본 파일을 찾을 수 없습니다. 기본 청킹 사용: {filename}")
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f"구조화된 파싱 실패, 기본 청킹 사용: {filename}, 오류: {str(e)}")
        
        # 기본 청킹 (5-2.법령별이 아니거나 구조화된 파싱 실패 시)
        is_structured = filename.lower().endswith(('.csv', '.xlsx', '.xls', '.doc', '.docx'))
        self.chunker.update_config(chunk_by_row=True)
        chunk_metadata_for_chunking = {"is_structured_data": is_structured} if is_structured else None
        chunks = self.chunker.chunk_text(content, chunk_metadata_for_chunking)
        
        # 임베딩 및 벡터 저장소에 추가
        filename_prefix = f"[파일: {filename}]\n"
        
        for i, chunk in enumerate(chunks):
            chunk_with_filename = filename_prefix + chunk
            embedding = await self.embedder.embed_text(chunk_with_filename)
            
            chunk_metadata = {
                "source": doc_id,
                "filename": filename,
                "folder": folder_name,
                "chunk_index": i,
                "created_at": datetime.now().isoformat(),
                **(metadata or {})
            }
            await self.retriever.add_document(
                embedding=embedding,
                content=chunk,
                metadata=chunk_metadata
            )
        
        return DocumentInfo(
            id=doc_id,
            filename=filename,
            chunk_count=len(chunks),
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
        
        # 벡터 저장소에서도 제거
        self.retriever.remove_document(doc_id)
        
        return True
    
    async def load_existing_documents(self):
        """documents 폴더에 있는 기존 문서들을 자동으로 로드 (폴더별 처리)"""
        import logging
        logger = logging.getLogger(__name__)
        
        logger.info("기존 문서 자동 로드 시작...")
        
        # 처리된 문서 확인용 (벡터 저장소에서 확인 - 더 정확함)
        processed_docs = set()
        
        # 벡터 저장소의 메타데이터에서 확인
        import unicodedata
        for meta in self.retriever.metadatas:
            folder = meta.get("folder", "")
            filename = meta.get("filename", "")
            if folder and filename:
                # 유니코드 정규화하여 키 생성
                folder_nfc = unicodedata.normalize('NFC', str(folder).strip())
                processed_docs.add(f"{folder_nfc}/{filename}")
        
        # 메타데이터 파일에서도 확인 (벡터 저장소에 없는 경우 대비)
        for meta_file in self.documents_dir.glob("*.meta.json"):
            try:
                with open(meta_file, "r", encoding="utf-8") as f:
                    meta = json.load(f)
                    folder = meta.get("metadata", {}).get("folder", "")
                    filename = meta.get("filename", "")
                    if folder and filename:
                        folder_nfc = unicodedata.normalize('NFC', str(folder).strip())
                        processed_docs.add(f"{folder_nfc}/{filename}")
            except Exception as e:
                logger.warning(f"메타데이터 파일 읽기 실패: {meta_file}, {str(e)}")
        
        loaded_count = 0
        skipped_count = 0
        
        # 지원하는 파일 확장자
        supported_extensions = ['.txt', '.md', '.csv', '.xlsx', '.xls', '.doc', '.docx']
        # 허용할 파일명 (4, 5-1, 5-2만)
        allowed_files = ["4.", "5-1.", "5-2."]
        
        # 폴더별로 처리
        for folder_path in self.documents_dir.iterdir():
            if not folder_path.is_dir() or folder_path.name.startswith('.'):
                continue
            
            folder_name = folder_path.name
            logger.info(f"폴더 처리 중: {folder_name}")
            
            # 폴더 내의 파일들 처리
            for file_path in folder_path.iterdir():
                if file_path.is_dir() or file_path.name.startswith('~$'):  # 임시 파일 스킵
                    continue
                
                filename = file_path.name
                
                # 허용된 파일만 처리 (4, 5-1, 5-2)
                if not any(filename.startswith(prefix) for prefix in allowed_files):
                    continue
                
                # 지원하는 확장자인지 확인
                if not any(filename.lower().endswith(ext) for ext in supported_extensions):
                    continue
                
                # 이미 처리된 문서인지 확인 (유니코드 정규화하여 비교)
                import unicodedata
                folder_name_nfc = unicodedata.normalize('NFC', str(folder_name).strip())
                doc_key = f"{folder_name_nfc}/{filename}"
                if doc_key in processed_docs:
                    skipped_count += 1
                    logger.debug(f"문서 스킵 (이미 처리됨): {doc_key}")
                    continue
                
                try:
                    # 5-2.법령별 문서는 구조화된 파서 사용 (로우 단위 청킹)
                    if filename.startswith("5-2.") and filename.lower().endswith(('.doc', '.docx')):
                        # 구조화된 파서를 사용하므로 원본 파일 경로를 전달
                        # 파일을 텍스트로 변환 (구조화된 파서는 upload_document 내부에서 처리)
                        with open(file_path, "rb") as f:
                            content_bytes = f.read()
                        from rag.parsers.file_parser import FileParser
                        content = FileParser.parse_file(filename, content_bytes)
                        
                        # upload_document에 원본 파일 경로 전달 (구조화된 파서가 사용할 수 있도록)
                        await self.upload_document(
                            filename=filename,
                            content=content,
                            metadata={"auto_loaded": True, "folder": folder_name},
                            file_path=str(file_path)  # 원본 파일 경로 전달
                        )
                        loaded_count += 1
                        logger.info(f"문서 자동 로드 완료 (구조화된 파싱, 로우 단위): {folder_name}/{filename}")
                    else:
                        # 다른 파일은 기본 방식
                        if filename.lower().endswith(('.csv', '.xlsx', '.xls', '.doc', '.docx')):
                            with open(file_path, "rb") as f:
                                content_bytes = f.read()
                            from rag.parsers.file_parser import FileParser
                            content = FileParser.parse_file(filename, content_bytes)
                        else:
                            with open(file_path, "r", encoding="utf-8") as f:
                                content = f.read()
                        
                        # 문서 업로드 (벡터화) - 폴더 정보 포함
                        await self.upload_document(
                            filename=filename,
                            content=content,
                            metadata={"auto_loaded": True, "folder": folder_name}
                        )
                        loaded_count += 1
                        logger.info(f"문서 자동 로드 완료: {folder_name}/{filename}")
                    
                except Exception as e:
                    logger.error(f"문서 자동 로드 실패: {folder_name}/{filename}, 오류: {str(e)}")
        
        logger.info(f"기존 문서 자동 로드 완료: {loaded_count}개 로드, {skipped_count}개 스킵")
        return loaded_count

