from typing import List, Dict, Any, Optional
import re

class Chunker:
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200, chunk_by_row: bool = False):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.chunk_by_row = chunk_by_row
        # 단락 구분자 패턴 (줄바꿈 2개 이상, #, @, 특수 마커)
        self.paragraph_separators = [
            r'\n\s*\n+',  # 빈 줄 (줄바꿈 2개 이상)
            r'\n(?=#)',   # 마크다운 헤더 앞 줄바꿈
            r'\n(?=@)',   # @ 마커 앞 줄바꿈
            r'\n(?=\d+\.)',  # 번호 목록 앞 줄바꿈
        ]
    
    def chunk_text(self, text: str, metadata: Optional[Dict[str, Any]] = None) -> List[str]:
        """텍스트를 단락 단위로 청크로 분할"""
        # Row 단위 청킹 (CSV/Excel 파일의 경우)
        if self.chunk_by_row and metadata and metadata.get("is_structured_data", False):
            return self._chunk_by_row(text)
        
        # 단락 단위로 분할
        paragraphs = self._split_into_paragraphs(text)
        
        chunks = []
        current_chunk = []
        current_length = 0
        
        for paragraph in paragraphs:
            paragraph = paragraph.strip()
            if not paragraph:
                continue
            
            paragraph_length = len(paragraph)
            
            # 단락이 청크 크기보다 크면 문장 단위로 분할
            if paragraph_length > self.chunk_size:
                # 현재 청크가 있으면 먼저 저장
                if current_chunk:
                    chunks.append("\n\n".join(current_chunk))
                    # 오버랩 처리
                    if self.chunk_overlap > 0:
                        current_chunk = self._get_overlap_chunk(current_chunk)
                        current_length = sum(len(p) + 2 for p in current_chunk)  # \n\n 포함
                    else:
                        current_chunk = []
                        current_length = 0
                
                # 큰 단락을 문장 단위로 분할
                sentence_chunks = self._split_large_paragraph(paragraph)
                chunks.extend(sentence_chunks)
                continue
            
            # 현재 청크에 추가했을 때 크기 초과 여부 확인
            if current_length + paragraph_length + 2 > self.chunk_size and current_chunk:  # +2는 \n\n
                # 현재 청크 저장
                chunks.append("\n\n".join(current_chunk))
                
                # 오버랩 처리
                if self.chunk_overlap > 0:
                    current_chunk = self._get_overlap_chunk(current_chunk)
                    current_length = sum(len(p) + 2 for p in current_chunk)
                else:
                    current_chunk = []
                    current_length = 0
            
            # 단락 추가
            current_chunk.append(paragraph)
            current_length += paragraph_length + 2  # \n\n 포함
        
        # 마지막 청크 추가
        if current_chunk:
            chunks.append("\n\n".join(current_chunk))
        
        return chunks if chunks else [text]
    
    def _split_into_paragraphs(self, text: str) -> List[str]:
        """텍스트를 단락으로 분할"""
        # 먼저 빈 줄로 분할 시도
        paragraphs = re.split(r'\n\s*\n+', text)
        
        # 단락이 너무 적거나 모든 단락이 너무 크면 다른 구분자 시도
        if len(paragraphs) == 1 or all(len(p) > self.chunk_size * 2 for p in paragraphs if p.strip()):
            # 마크다운 헤더(#) 기준으로 분할
            paragraphs = re.split(r'\n(?=#)', text)
        
        # 여전히 단일 단락이면 @ 마커나 번호 목록 기준으로 분할
        if len(paragraphs) == 1:
            paragraphs = re.split(r'\n(?=@|\d+\.)', text)
        
        # 최종적으로 줄바꿈 단위로 분할 (단락이 없을 경우)
        if len(paragraphs) == 1:
            paragraphs = [p for p in text.split('\n') if p.strip()]
        
        return [p.strip() for p in paragraphs if p.strip()]
    
    def _split_large_paragraph(self, paragraph: str) -> List[str]:
        """큰 단락을 문장 단위로 분할"""
        # 문장 단위로 분할
        sentences = re.split(r'(?<=[.!?])\s+', paragraph)
        
        # 문장 구분자가 없으면 줄바꿈 단위로 분할
        if len(sentences) == 1:
            sentences = [s for s in paragraph.split('\n') if s.strip()]
        
        chunks = []
        current_chunk = []
        current_length = 0
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            
            sentence_length = len(sentence)
            
            # 문장이 청크 크기보다 크면 단어 단위로 강제 분할
            if sentence_length > self.chunk_size:
                if current_chunk:
                    chunks.append(" ".join(current_chunk))
                    current_chunk = []
                    current_length = 0
                
                # 단어 단위로 분할
                words = sentence.split()
                temp_chunk = []
                temp_length = 0
                
                for word in words:
                    word_length = len(word) + 1
                    if temp_length + word_length > self.chunk_size and temp_chunk:
                        chunks.append(" ".join(temp_chunk))
                        temp_chunk = [word]
                        temp_length = word_length
                    else:
                        temp_chunk.append(word)
                        temp_length += word_length
                
                if temp_chunk:
                    current_chunk = temp_chunk
                    current_length = temp_length
                continue
            
            # 현재 청크에 추가했을 때 크기 초과 여부 확인
            if current_length + sentence_length + 1 > self.chunk_size and current_chunk:
                chunks.append(" ".join(current_chunk))
                # 오버랩 처리
                if self.chunk_overlap > 0:
                    overlap_sentences = current_chunk[-self.chunk_overlap//50:] if len(current_chunk) > self.chunk_overlap//50 else current_chunk
                    current_chunk = overlap_sentences
                    current_length = sum(len(s) + 1 for s in current_chunk)
                else:
                    current_chunk = []
                    current_length = 0
            
            current_chunk.append(sentence)
            current_length += sentence_length + 1
        
        if current_chunk:
            chunks.append(" ".join(current_chunk))
        
        return chunks if chunks else [paragraph]
    
    def _get_overlap_chunk(self, chunks: List[str]) -> List[str]:
        """오버랩을 위한 마지막 단락들 추출"""
        if not chunks or self.chunk_overlap == 0:
            return []
        
        overlap_chunks = []
        overlap_length = 0
        
        # 뒤에서부터 단락을 추가하여 오버랩 크기 내로 유지
        for chunk in reversed(chunks):
            chunk_length = len(chunk) + 2  # \n\n 포함
            if overlap_length + chunk_length <= self.chunk_overlap:
                overlap_chunks.insert(0, chunk)
                overlap_length += chunk_length
            else:
                break
        
        return overlap_chunks
    
    def _chunk_by_row(self, text: str) -> List[str]:
        """Row 단위로 청킹 (CSV/Excel 데이터용)"""
        lines = text.split('\n')
        chunks = []
        current_chunk = []
        current_length = 0
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            line_length = len(line)
            
            # 행 단위로 청크 생성
            if line.startswith('행 '):
                if current_chunk:
                    chunks.append('\n'.join(current_chunk))
                current_chunk = [line]
                current_length = line_length
            else:
                if current_length + line_length > self.chunk_size and current_chunk:
                    chunks.append('\n'.join(current_chunk))
                    current_chunk = [line]
                    current_length = line_length
                else:
                    current_chunk.append(line)
                    current_length += line_length
        
        if current_chunk:
            chunks.append('\n'.join(current_chunk))
        
        return chunks if chunks else [text]
    
    def update_config(self, chunk_size: int = None, chunk_overlap: int = None, chunk_by_row: bool = None):
        """청킹 설정 업데이트"""
        if chunk_size is not None:
            self.chunk_size = chunk_size
        if chunk_overlap is not None:
            self.chunk_overlap = chunk_overlap
        if chunk_by_row is not None:
            self.chunk_by_row = chunk_by_row

