"""
JSON 파일을 위한 빠른 키워드 검색 인덱스
"""
import json
from typing import List, Dict, Any, Optional
from pathlib import Path
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)


class JSONIndex:
    """JSON 파일을 키워드 기반으로 빠르게 검색하는 인덱스"""
    
    def __init__(self):
        # 폴더별 JSON 데이터 저장
        # {folder_name: {filename: [items]}}
        self.json_data: Dict[str, Dict[str, List[Dict[str, Any]]]] = defaultdict(dict)
        
        # 키워드 인덱스: {keyword: [(folder, filename, item_index, score)]}
        self.keyword_index: Dict[str, List[tuple]] = defaultdict(list)
        
        # 카테고리 인덱스: {category: [(folder, filename, item_index)]}
        self.category_index: Dict[str, List[tuple]] = defaultdict(list)
        
        # 질문 인덱스: {question_keyword: [(folder, filename, item_index)]}
        self.question_index: Dict[str, List[tuple]] = defaultdict(list)
    
    def load_json_file(self, file_path: Path, folder: str = ""):
        """JSON 파일을 로드하고 인덱싱"""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            if not isinstance(data, list):
                data = [data]
            
            filename = file_path.name
            
            # JSON 데이터 저장
            if folder not in self.json_data:
                self.json_data[folder] = {}
            self.json_data[folder][filename] = data
            
            # 인덱싱
            for idx, item in enumerate(data):
                if not isinstance(item, dict):
                    continue
                
                # 키워드 인덱싱
                keywords = item.get("keywords", [])
                if isinstance(keywords, list):
                    for keyword in keywords:
                        if keyword:
                            self.keyword_index[keyword.lower()].append((folder, filename, idx, 1.0))
                
                # 카테고리 인덱싱
                category = item.get("category", "")
                if category:
                    self.category_index[category.lower()].append((folder, filename, idx))
                
                # 질문 인덱싱 (질문의 주요 단어 추출)
                question = item.get("question", "")
                if question:
                    # 간단한 키워드 추출 (실제로는 더 정교한 토크나이징 필요)
                    question_words = self._extract_keywords(question)
                    for word in question_words:
                        if len(word) > 1:  # 1글자 단어 제외
                            self.question_index[word.lower()].append((folder, filename, idx))
                
                # 답변 내용도 인덱싱
                answer = item.get("answer", "")
                if answer:
                    answer_words = self._extract_keywords(answer)
                    for word in answer_words:
                        if len(word) > 1:
                            self.keyword_index[word.lower()].append((folder, filename, idx, 0.5))  # 낮은 점수
            
            logger.info(f"JSON 파일 인덱싱 완료: {folder}/{filename} ({len(data)}개 항목)")
            return True
        except Exception as e:
            logger.error(f"JSON 파일 로드 실패: {file_path}, {str(e)}")
            return False
    
    def _extract_keywords(self, text: str) -> List[str]:
        """텍스트에서 키워드 추출 (간단한 버전)"""
        # 한글, 영문, 숫자만 추출
        import re
        # 단어 단위로 분리
        words = re.findall(r'[가-힣a-zA-Z0-9]+', text)
        return words
    
    def search(
        self, 
        query: str, 
        folder_filter: Optional[str] = None,
        region_filter: Optional[str] = None,
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """키워드 기반 빠른 검색 (지역 + 건물 타입 조합 지원)"""
        query_lower = query.lower()
        query_words = self._extract_keywords(query)
        
        # 점수 계산: {item_key: score}
        item_scores: Dict[tuple, float] = defaultdict(float)
        
        # 검색할 폴더 목록 결정
        # region이 있으면: region 폴더 + folder 폴더 모두 검색
        # region이 없으면: folder 폴더만 검색
        search_folders = []
        if folder_filter:
            search_folders.append(folder_filter)
        if region_filter:
            search_folders.append(region_filter)  # region 폴더도 검색 대상에 추가
        
        # 키워드 매칭 (최적화: 상위 결과가 충분하면 조기 종료)
        for word in query_words:
            if word in self.keyword_index:
                for folder, filename, idx, score in self.keyword_index[word]:
                    if search_folders and folder not in search_folders:
                        continue
                    item_scores[(folder, filename, idx)] += score
                    # 충분한 결과가 있으면 조기 종료
                    if len(item_scores) >= top_k * 3:
                        break
                if len(item_scores) >= top_k * 3:
                    break
        
        # 질문 매칭 (더 높은 가중치, 최적화)
        for word in query_words:
            if word in self.question_index:
                for folder, filename, idx in self.question_index[word]:
                    if search_folders and folder not in search_folders:
                        continue
                    item_scores[(folder, filename, idx)] += 2.0
                    if len(item_scores) >= top_k * 3:
                        break
                if len(item_scores) >= top_k * 3:
                    break
        
        # 정확한 질문 매칭 (최적화: 매칭되면 즉시 반환)
        exact_match_found = False
        for folder, file_data in self.json_data.items():
            if search_folders and folder not in search_folders:
                continue
            for filename, items in file_data.items():
                for idx, item in enumerate(items):
                    question = item.get("question", "").lower()
                    if query_lower in question or question in query_lower:
                        item_scores[(folder, filename, idx)] += 5.0  # 매우 높은 점수
                        exact_match_found = True
                        # 정확한 매칭이 있으면 즉시 상위 결과 반환 (성능 최적화)
                        if len(item_scores) >= top_k:
                            break
                if exact_match_found and len(item_scores) >= top_k:
                    break
            if exact_match_found and len(item_scores) >= top_k:
                break
        
        # 점수 순으로 정렬
        sorted_items = sorted(item_scores.items(), key=lambda x: x[1], reverse=True)
        
        # 최고 점수 계산 (정규화용)
        max_score = sorted_items[0][1] if sorted_items else 1.0
        
        # 상위 K개 반환
        results = []
        seen = set()
        for (folder, filename, idx), raw_score in sorted_items[:top_k * 2]:  # 중복 제거를 위해 더 많이 가져옴
            item_key = (folder, filename, idx)
            if item_key in seen:
                continue
            seen.add(item_key)
            
            if folder in self.json_data and filename in self.json_data[folder]:
                item = self.json_data[folder][filename][idx]
                
                # 점수 정규화 (0.0 ~ 1.0 범위로 변환)
                # 최고 점수를 1.0으로 하고 나머지를 상대적으로 변환
                normalized_score = min(1.0, raw_score / max_score) if max_score > 0 else 0.0
                
                # 구조화된 형식으로 반환
                result = {
                    "content": self._format_item(item),
                    "metadata": {
                        "folder": folder,
                        "filename": filename,
                        "id": item.get("id", ""),
                        "category": item.get("category", ""),
                        "json_type": "qa" if "question" in item else "ordinance" if "title" in item else "general",
                        "score": normalized_score,
                        "source": f"{folder}/{filename}" if folder else filename
                    },
                    "score": normalized_score
                }
                results.append(result)
                if len(results) >= top_k:
                    break
        
        return results
    
    def _format_item(self, item: Dict[str, Any]) -> str:
        """JSON 항목을 텍스트로 포맷팅"""
        parts = []
        
        if "question" in item and "answer" in item:
            parts.append(f"질문: {item.get('question', '')}")
            parts.append(f"답변: {item.get('answer', '')}")
            if item.get('category'):
                parts.append(f"카테고리: {item.get('category')}")
            if item.get('keywords'):
                keywords = item.get('keywords', [])
                if isinstance(keywords, list):
                    parts.append(f"키워드: {', '.join(keywords)}")
        elif "title" in item and "answer" in item:
            parts.append(f"제목: {item.get('title', '')}")
            if item.get('question'):
                parts.append(f"질문: {item.get('question')}")
            parts.append(f"답변: {item.get('answer', '')}")
            if item.get('category'):
                parts.append(f"카테고리: {item.get('category')}")
        
        return "\n".join(parts)
    
    def get_by_category(self, category: str, folder_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        """카테고리로 검색"""
        results = []
        category_lower = category.lower()
        
        if category_lower in self.category_index:
            for folder, filename, idx in self.category_index[category_lower]:
                if folder_filter and folder != folder_filter:
                    continue
                if folder in self.json_data and filename in self.json_data[folder]:
                    item = self.json_data[folder][filename][idx]
                    results.append({
                        "content": self._format_item(item),
                        "metadata": {
                            "folder": folder,
                            "filename": filename,
                            "id": item.get("id", ""),
                            "category": item.get("category", "")
                        }
                    })
        
        return results

