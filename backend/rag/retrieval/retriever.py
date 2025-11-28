from typing import List, Dict, Any, Optional
import json
import numpy as np
from datetime import datetime
from pathlib import Path

class Retriever:
    def __init__(
        self, 
        vector_store_path: str = "vector_store", 
        top_k: int = 5, 
        similarity_threshold: float = 0.1,  # 기본값을 낮춰서 더 많은 문서 검색
        similarity_weight: float = 1.0,
        recency_weight: float = 0.0,
        source_weight: float = 0.0
    ):
        self.top_k = top_k
        self.similarity_threshold = similarity_threshold
        self.similarity_weight = similarity_weight
        self.recency_weight = recency_weight
        self.source_weight = source_weight
        self.vector_store_path = Path(vector_store_path)
        self.vector_store_path.mkdir(exist_ok=True, parents=True)
        
        # 메모리 기반 벡터 저장소
        self.vectors: List[List[float]] = []
        self.contents: List[str] = []
        self.metadatas: List[Dict[str, Any]] = []
        
        # 저장소 로드
        self._load_vector_store()
    
    def _load_vector_store(self):
        """벡터 저장소 로드 (안전한 오류 처리)"""
        import logging
        logger = logging.getLogger(__name__)
        
        vector_file = self.vector_store_path / "vectors.json"
        if vector_file.exists():
            try:
                with open(vector_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.vectors = data.get("vectors", [])
                    self.contents = data.get("contents", [])
                    self.metadatas = data.get("metadatas", [])
                    logger.info(f"벡터 저장소 로드 완료: {len(self.vectors)}개 벡터")
            except json.JSONDecodeError as e:
                logger.error(f"벡터 저장소 JSON 파싱 오류: {str(e)}. 손상된 파일을 백업하고 새로 시작합니다.")
                # 손상된 파일 백업
                backup_file = self.vector_store_path / f"vectors.json.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                try:
                    import shutil
                    shutil.copy2(vector_file, backup_file)
                    logger.info(f"손상된 파일 백업 완료: {backup_file}")
                except Exception as backup_error:
                    logger.warning(f"백업 실패: {str(backup_error)}")
                
                # 빈 저장소로 초기화
                self.vectors = []
                self.contents = []
                self.metadatas = []
                # 손상된 파일 삭제
                try:
                    vector_file.unlink()
                    logger.info("손상된 벡터 저장소 파일 삭제 완료. 새로 시작합니다.")
                except Exception as del_error:
                    logger.warning(f"파일 삭제 실패: {str(del_error)}")
            except Exception as e:
                logger.error(f"벡터 저장소 로드 중 예상치 못한 오류: {str(e)}. 빈 저장소로 시작합니다.")
                self.vectors = []
                self.contents = []
                self.metadatas = []
        else:
            logger.info("벡터 저장소 파일이 없습니다. 새로 시작합니다.")
            self.vectors = []
            self.contents = []
            self.metadatas = []
    
    def _save_vector_store(self):
        """벡터 저장소 저장"""
        vector_file = self.vector_store_path / "vectors.json"
        data = {
            "vectors": self.vectors,
            "contents": self.contents,
            "metadatas": self.metadatas
        }
        with open(vector_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    async def add_document(
        self,
        embedding: List[float],
        content: str,
        metadata: Dict[str, Any]
    ):
        """문서를 벡터 저장소에 추가"""
        self.vectors.append(embedding)
        self.contents.append(content)
        self.metadatas.append(metadata)
        self._save_vector_store()
    
    def remove_document(self, doc_id: str):
        """문서를 벡터 저장소에서 제거"""
        indices_to_remove = [
            i for i, meta in enumerate(self.metadatas)
            if meta.get("source") == doc_id
        ]
        
        for idx in reversed(indices_to_remove):
            self.vectors.pop(idx)
            self.contents.pop(idx)
            self.metadatas.pop(idx)
        
        self._save_vector_store()
    
    async def retrieve(
        self,
        query_embedding: List[float],
        top_k: Optional[int] = None,
        similarity_threshold: Optional[float] = None,
        preferred_sources: Optional[List[str]] = None,
        folder_filter: Optional[str] = None,
        filename_filter: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """유사한 문서 검색 (가중치 적용, 폴더/파일 필터링)"""
        top_k = top_k or self.top_k
        similarity_threshold = similarity_threshold or self.similarity_threshold
        preferred_sources = preferred_sources or []
        
        if not self.vectors:
            return []
        
        query_vec = np.array(query_embedding)
        weighted_scores = []
        current_time = datetime.now()
        
        # 디버깅 정보
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"검색 시작: 쿼리 벡터 차원={len(query_embedding)}, 벡터 저장소 크기={len(self.vectors)}")
        
        filtered_count = 0
        similarity_failed_count = 0
        passed_count = 0
        
        # 성능 최적화: 먼저 필터링 인덱스 생성 (한 번만)
        import unicodedata
        valid_indices = []
        
        # 1단계: 폴더 및 파일명 필터링으로 유효한 인덱스만 추출
        for idx in range(len(self.vectors)):
            try:
                metadata = self.metadatas[idx] if idx < len(self.metadatas) else {}
                
                # 폴더 필터링
                if folder_filter:
                    metadata_folder = metadata.get("folder", "")
                    if not metadata_folder:
                        continue
                    metadata_folder_clean = unicodedata.normalize('NFC', str(metadata_folder).strip())
                    folder_filter_clean = unicodedata.normalize('NFC', str(folder_filter).strip())
                    if metadata_folder_clean != folder_filter_clean:
                        continue
                
                # 파일명 필터링
                if filename_filter:
                    filename = metadata.get("filename", "")
                    if not filename:
                        continue
                    matches = any(filename.startswith(fn) for fn in filename_filter)
                    if not matches:
                        filtered_count += 1
                        continue
                
                valid_indices.append(idx)
            except Exception as e:
                filtered_count += 1
                continue
        
        if not valid_indices:
            logger.warning(f"필터링 후 유효한 벡터가 없습니다. (폴더: {folder_filter}, 파일: {filename_filter})")
            return []
        
        logger.info(f"필터링 완료: {len(valid_indices)}/{len(self.vectors)}개 벡터가 검색 대상")
        
        # 2단계: 벡터화된 유사도 계산 (전체 행렬 연산으로 최적화)
        try:
            # 유효한 벡터만 추출
            valid_vectors = np.array([self.vectors[idx] for idx in valid_indices])
            
            # 정규화된 벡터 계산
            query_norm = np.linalg.norm(query_vec)
            if query_norm == 0:
                return []
            
            # 모든 문서 벡터 정규화
            doc_norms = np.linalg.norm(valid_vectors, axis=1)
            valid_doc_mask = doc_norms > 0
            
            if not np.any(valid_doc_mask):
                return []
            
            # 유사도 계산 (벡터화)
            similarities = np.dot(valid_vectors[valid_doc_mask], query_vec) / (query_norm * doc_norms[valid_doc_mask])
            
            # 유효한 인덱스 재매핑
            valid_indices_filtered = [valid_indices[i] for i in range(len(valid_indices)) if valid_doc_mask[i]]
            
            # 임계값 필터링
            threshold_mask = (similarities >= similarity_threshold) & np.isfinite(similarities)
            passed_indices = [valid_indices_filtered[i] for i in range(len(valid_indices_filtered)) if threshold_mask[i]]
            passed_similarities = similarities[threshold_mask]
            
            if not passed_indices:
                logger.info("유사도 임계값을 통과한 벡터가 없습니다.")
                return []
            
            # 점수 계산을 위한 루프 (최적화: 필요한 경우만)
            weighted_scores = []
            passed_count = len(passed_indices)
            
            for idx, base_similarity in zip(passed_indices, passed_similarities):
                try:
                    metadata = self.metadatas[idx] if idx < len(self.metadatas) else {}
                    base_similarity = float(base_similarity)
                    
                    # 시나리오 일치 보정 (scenario 필드 확인)
                    bonus = 0.0
                    scenario = metadata.get("scenario") or metadata.get("folder")
                    if folder_filter and scenario:
                        scenario_clean = unicodedata.normalize('NFC', str(scenario).strip())
                        folder_filter_clean = unicodedata.normalize('NFC', str(folder_filter).strip())
                        if scenario_clean == folder_filter_clean:
                            bonus += 0.1  # 시나리오 일치 시 +0.1 가산점
                    
                    # 용도 일치 보정
                    usage = metadata.get("usage")
                    if usage and folder_filter:
                        if "판매시설" in folder_filter and "판매시설" in str(usage):
                            bonus += 0.05
                        elif "숙박시설" in folder_filter and "숙박시설" in str(usage):
                            bonus += 0.05
                        elif "다중주택" in folder_filter and "다중주택" in str(usage):
                            bonus += 0.05
                        elif "단독주택" in folder_filter and "단독주택" in str(usage):
                            bonus += 0.05
                    
                    # 최종 점수 (유사도 + 보정)
                    similarity = base_similarity + bonus
                    
                    # 가중치 적용
                    weighted_score = similarity * self.similarity_weight
                    
                    # 최신성 가중치
                    if self.recency_weight > 0:
                        created_at_str = metadata.get("created_at", "")
                        if created_at_str:
                            try:
                                created_at = datetime.fromisoformat(created_at_str.replace('Z', '+00:00'))
                                days_old = (current_time - created_at.replace(tzinfo=None)).days
                                recency_score = max(0, 1 - (days_old / 365))
                                weighted_score += recency_score * self.recency_weight
                            except:
                                pass
                    
                    # 출처 가중치
                    if self.source_weight > 0 and preferred_sources:
                        source = metadata.get("source", "")
                        if source in preferred_sources:
                            weighted_score += self.source_weight
                    
                    weighted_scores.append({
                        "idx": idx,
                        "similarity": similarity,
                        "weighted_score": weighted_score
                    })
                except Exception as e:
                    logger.warning(f"Error calculating similarity for vector {idx}: {str(e)}")
                    continue
        except Exception as e:
            logger.error(f"벡터화된 유사도 계산 실패: {str(e)}", exc_info=True)
            return []
        
        # 디버깅: 검색 통계 로깅
        logger.info(f"검색 통계: 필터링됨={filtered_count}, 유사도 실패={similarity_failed_count}, 통과={passed_count}, 최종 점수={len(weighted_scores)}")
        
        # 가중치 점수로 정렬
        weighted_scores.sort(key=lambda x: x["weighted_score"], reverse=True)
        
        # 디버깅: 검색 결과 로깅
        logger.info(f"검색 완료: 총 {len(weighted_scores)}개 항목, 상위 {top_k}개 반환 예정")
        if weighted_scores:
            logger.info(f"최고 점수: {weighted_scores[0]['similarity']:.4f} (가중치 점수: {weighted_scores[0]['weighted_score']:.4f})")
            logger.info(f"최저 점수: {weighted_scores[-1]['similarity']:.4f} (가중치 점수: {weighted_scores[-1]['weighted_score']:.4f})")
        else:
            logger.warning(f"⚠️ 검색 결과가 없습니다! (유사도 임계값: {similarity_threshold}, 필터링: {filtered_count}개, 유사도 실패: {similarity_failed_count}개)")
        
        # 상위 K개 선택
        results = []
        for item in weighted_scores[:top_k]:
            idx = item["idx"]
            results.append({
                "content": self.contents[idx],
                "metadata": self.metadatas[idx],
                "score": item["similarity"],
                "weighted_score": item["weighted_score"]
            })
        
        return results
    
    def update_config(
        self, 
        similarity_threshold: Optional[float] = None, 
        top_k: Optional[int] = None,
        similarity_weight: Optional[float] = None,
        recency_weight: Optional[float] = None,
        source_weight: Optional[float] = None
    ):
        """검색 설정 업데이트"""
        if similarity_threshold is not None:
            self.similarity_threshold = similarity_threshold
        if top_k is not None:
            self.top_k = top_k
        if similarity_weight is not None:
            self.similarity_weight = similarity_weight
        if recency_weight is not None:
            self.recency_weight = recency_weight
        if source_weight is not None:
            self.source_weight = source_weight

