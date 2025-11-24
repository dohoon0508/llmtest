from fastapi import APIRouter, HTTPException, UploadFile, File
from app.models.rag_models import DocumentUpload, DocumentInfo
from app.services.document_service import DocumentService
from rag.parsers.file_parser import FileParser
import traceback
import logging

logger = logging.getLogger(__name__)

router = APIRouter()
document_service = DocumentService()

@router.post("/upload", response_model=DocumentInfo)
async def upload_document(
    file: UploadFile = File(...),
    metadata: str = None
):
    """문서 업로드 (텍스트, CSV, Excel 지원)"""
    try:
        content = await file.read()
        
        # 파일 파서를 사용하여 텍스트로 변환
        content_str = FileParser.parse_file(file.filename or "unknown", content)
        
        import json
        doc_metadata = json.loads(metadata) if metadata else None
        
        result = await document_service.upload_document(
            filename=file.filename,
            content=content_str,
            metadata=doc_metadata
        )
        return result
    except ValueError as e:
        logger.error(f"ValueError in upload_document: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error in upload_document: {str(e)}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"파일 업로드 오류: {str(e)}")

@router.post("/upload-text", response_model=DocumentInfo)
async def upload_text_document(doc: DocumentUpload):
    """텍스트로 문서 업로드"""
    try:
        result = await document_service.upload_document(
            filename=doc.filename,
            content=doc.content,
            metadata=doc.metadata
        )
        return result
    except Exception as e:
        logger.error(f"Error in upload_text_document: {str(e)}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"문서 업로드 오류: {str(e)}")

@router.get("/list", response_model=list[DocumentInfo])
async def list_documents():
    """문서 목록 조회"""
    try:
        return document_service.list_documents()
    except Exception as e:
        logger.error(f"Error in list_documents: {str(e)}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"문서 목록 조회 오류: {str(e)}")

@router.get("/folders")
async def list_folders():
    """documents 폴더 내의 폴더 목록 조회"""
    try:
        from pathlib import Path
        from app.core.config import settings
        
        documents_dir = Path(settings.DOCUMENTS_DIR)
        folders = []
        
        # documents 폴더 내의 모든 디렉토리 찾기
        for item in documents_dir.iterdir():
            if item.is_dir() and not item.name.startswith('.'):
                folders.append(item.name)
        
        folders.sort()
        return {"folders": folders}
    except Exception as e:
        logger.error(f"Error in list_folders: {str(e)}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"폴더 목록 조회 오류: {str(e)}")

@router.post("/reload")
async def reload_documents():
    """documents 폴더의 기존 문서들을 다시 로드 (벡터화)"""
    try:
        loaded_count = await document_service.load_existing_documents()
        return {
            "message": f"문서 재로드 완료",
            "loaded_count": loaded_count
        }
    except Exception as e:
        logger.error(f"Error in reload_documents: {str(e)}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"문서 재로드 오류: {str(e)}")

@router.get("/{doc_id}")
async def get_document(doc_id: str):
    """문서 내용 조회"""
    try:
        content = document_service.get_document(doc_id)
        return {"id": doc_id, "content": content}
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error in get_document: {str(e)}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"문서 조회 오류: {str(e)}")

@router.delete("/{doc_id}")
async def delete_document(doc_id: str):
    """문서 삭제"""
    try:
        document_service.delete_document(doc_id)
        return {"message": f"Document {doc_id} deleted"}
    except Exception as e:
        logger.error(f"Error in delete_document: {str(e)}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"문서 삭제 오류: {str(e)}")

