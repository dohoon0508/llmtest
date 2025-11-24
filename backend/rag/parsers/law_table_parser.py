"""5-2.법령별 문서 전용 파서 - 행 단위 구조화 파싱"""
from typing import List, Dict, Any, Optional
import re
from bs4 import BeautifulSoup


class LawTableParser:
    """5-2.법령별 문서를 행 단위로 파싱하여 구조화된 메타데이터 추출"""
    
    @staticmethod
    def parse_law_table(html_content: str, scenario: str, filename: str) -> List[Dict[str, Any]]:
        """HTML 테이블을 파싱하여 행 단위 청크 리스트 반환"""
        soup = BeautifulSoup(html_content, 'html.parser')
        
        chunks = []
        current_law_group = None  # 현재 법령 묶음 (예: "건축법", "건축법 시행령")
        
        # ruleCheckTable 찾기
        table = soup.find('table', class_='ruleCheckTable')
        if not table:
            return chunks
        
        rows = table.find_all('tr')
        
        for row in rows:
            cells = row.find_all('td')
            if len(cells) < 2:
                continue
            
            # 법령 묶음 헤더 확인 (colspan이 4인 경우)
            if len(cells) == 1 and cells[0].get('colspan') == '4':
                law_group_text = cells[0].get_text(strip=True)
                # "■ 1. 건축법" 형식에서 "건축법" 추출
                match = re.search(r'■\s*\d+\.\s*(.+)', law_group_text)
                if match:
                    current_law_group = match.group(1).strip()
                continue
            
            # 헤더 행 스킵 (No, 항목, 법령내용, 검토내용)
            if len(cells) >= 4:
                header_text = ' '.join([cell.get_text(strip=True) for cell in cells[:4]])
                if 'No' in header_text and '항목' in header_text and '법령내용' in header_text:
                    continue
            
            # 데이터 행 처리 (4개 컬럼: No, 항목, 법령내용, 검토내용)
            if len(cells) >= 4:
                chunk = LawTableParser._parse_row(
                    cells, 
                    scenario=scenario,
                    law_group=current_law_group,
                    filename=filename
                )
                if chunk:
                    chunks.append(chunk)
        
        return chunks
    
    @staticmethod
    def _parse_row(cells: List, scenario: str, law_group: Optional[str], filename: str) -> Optional[Dict[str, Any]]:
        """테이블 행을 파싱하여 구조화된 청크 메타데이터 생성"""
        try:
            # No (첫 번째 셀)
            no_text = cells[0].get_text(strip=True)
            if not no_text or not no_text.isdigit():
                return None
            no = int(no_text)
            
            # 항목 (두 번째 셀)
            item_name = cells[1].get_text(strip=True)
            if not item_name:
                return None
            
            # 법령내용 (세 번째 셀)
            law_content_cell = cells[2]
            law_text, article_ids = LawTableParser._extract_law_content(law_content_cell)
            
            # 검토내용 (네 번째 셀)
            review_content_cell = cells[3]
            review_text, metadata = LawTableParser._extract_review_content(review_content_cell)
            
            # 청크 ID 생성
            chunk_id = f"{scenario}|{filename}|{law_group}|{no}" if law_group else f"{scenario}|{filename}|{no}"
            
            # 구조화된 청크 메타데이터
            chunk = {
                "id": chunk_id,
                "scenario": scenario,
                "law_group": law_group or "기타",
                "article_ids": article_ids,
                "item_name": item_name,
                "law_text": law_text,
                "review_text": review_text,
                "no": no,
                "filename": filename,
                **metadata  # 건축종류, 건축물용도, 주요구조부 등 추가 메타데이터
            }
            
            return chunk
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"행 파싱 오류: {str(e)}")
            return None
    
    @staticmethod
    def _extract_law_content(cell) -> tuple[str, List[str]]:
        """법령내용 셀에서 법령 텍스트와 조문 번호 추출"""
        law_text_parts = []
        article_ids = []
        
        # jonote 클래스 (조문 제목: "제60조(...)")
        for jonote in cell.find_all(class_='jonote'):
            text = jonote.get_text(strip=True)
            law_text_parts.append(text)
            
            # 조문 번호 추출 ("제60조", "제61조" 등)
            article_match = re.search(r'제(\d+)조', text)
            if article_match:
                article_ids.append(f"제{article_match.group(1)}조")
        
        # tag1, tag2, tag3 (조문 내용)
        for tag in cell.find_all(['div', 'span']):
            classes = tag.get('class', [])
            if any(c in ['tag1', 'tag2', 'tag3', 'tag4'] for c in classes):
                text = tag.get_text(strip=True)
                if text:
                    law_text_parts.append(text)
        
        law_text = "\n".join(law_text_parts)
        
        return law_text, article_ids
    
    @staticmethod
    def _extract_review_content(cell) -> tuple[str, Dict[str, Any]]:
        """검토내용 셀에서 검토 텍스트와 메타데이터 추출"""
        review_parts = []
        metadata = {
            "building_type": None,  # 건축종류
            "usage": None,  # 건축물용도
            "owner_type": None,  # 건축주 유형
            "main_structure": None,  # 주요구조부
            "building_characteristics": []  # 건물특성
        }
        
        # note1 클래스 (메타데이터: "• 건축종류 : 신축")
        for note1 in cell.find_all(class_='note1'):
            text = note1.get_text(strip=True)
            if text.startswith('•'):
                # 메타데이터 파싱
                if '건축종류' in text:
                    match = re.search(r'건축종류\s*:\s*(.+)', text)
                    if match:
                        metadata["building_type"] = match.group(1).strip()
                elif '건축물용도' in text:
                    match = re.search(r'건축물용도\s*:\s*(.+)', text)
                    if match:
                        metadata["usage"] = match.group(1).strip()
                elif '건축주' in text:
                    match = re.search(r'건축주\s*:\s*(.+)', text)
                    if match:
                        metadata["owner_type"] = match.group(1).strip()
                elif '주요구조부' in text:
                    match = re.search(r'주요구조부\s*:\s*(.+)', text)
                    if match:
                        metadata["main_structure"] = match.group(1).strip()
                elif '건물특성' in text:
                    match = re.search(r'건물특성\s*:\s*(.+)', text)
                    if match:
                        metadata["building_characteristics"].append(match.group(1).strip())
        
        # note2 클래스 (검토내용: "01.전용주거지역...")
        for note2 in cell.find_all(class_='note2'):
            text = note2.get_text(strip=True)
            if text:
                review_parts.append(text)
        
        review_text = "\n".join(review_parts)
        
        return review_text, metadata
    
    @staticmethod
    def create_embedding_text(chunk: Dict[str, Any]) -> str:
        """청크 메타데이터를 기반으로 임베딩용 텍스트 생성"""
        embed_parts = []
        
        embed_parts.append(f"[시나리오] {chunk.get('scenario', '')}")
        embed_parts.append(f"[법령 묶음] {chunk.get('law_group', '')}")
        
        # 조문 번호
        article_ids = chunk.get('article_ids', [])
        if article_ids:
            embed_parts.append(f"[조문] {', '.join(article_ids)}")
        
        embed_parts.append(f"[항목] {chunk.get('item_name', '')}")
        
        # 검토내용 (우선)
        review_text = chunk.get('review_text', '')
        if review_text:
            embed_parts.append(f"[검토내용] {review_text}")
        
        # 법령내용
        law_text = chunk.get('law_text', '')
        if law_text:
            # 너무 길면 일부만 포함
            if len(law_text) > 2000:
                law_text = law_text[:2000] + "..."
            embed_parts.append(f"[법령내용] {law_text}")
        
        # 추가 메타데이터
        usage = chunk.get('usage')
        if usage:
            embed_parts.append(f"[용도] {usage}")
        
        building_type = chunk.get('building_type')
        if building_type:
            embed_parts.append(f"[건축종류] {building_type}")
        
        return "\n".join(embed_parts)

