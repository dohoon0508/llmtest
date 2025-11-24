from typing import List, Dict, Any, Optional
import re

class Chunker:
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200, chunk_by_row: bool = False):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.chunk_by_row = chunk_by_row
    
    def chunk_text(self, text: str, metadata: Optional[Dict[str, Any]] = None) -> List[str]:
        """텍스트를 청크로 분할"""
        # Row 단위 청킹 (CSV/Excel 파일의 경우)
        if self.chunk_by_row and metadata and metadata.get("is_structured_data", False):
            return self._chunk_by_row(text)
        
        # 문장 단위로 분할 시도
        sentences = re.split(r'(?<=[.!?])\s+', text)
        
        # 문장 구분자가 없거나 너무 적으면 줄바꿈 단위로 분할
        if len(sentences) == 1 or (len(sentences) == 1 and len(text) > self.chunk_size):
            sentences = text.split('\n')
        
        chunks = []
        current_chunk = []
        current_length = 0
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
                
            sentence_length = len(sentence)
            
            # 문장이 청크 크기보다 크면 강제로 분할
            if sentence_length > self.chunk_size:
                # 큰 문장을 여러 청크로 분할
                words = sentence.split()
                temp_chunk = []
                temp_length = 0
                
                for word in words:
                    word_length = len(word) + 1  # 공백 포함
                    if temp_length + word_length > self.chunk_size and temp_chunk:
                        chunks.append(" ".join(temp_chunk))
                        # 오버랩 처리
                        if self.chunk_overlap > 0:
                            overlap_words = temp_chunk[-self.chunk_overlap//10:] if len(temp_chunk) > self.chunk_overlap//10 else temp_chunk
                            temp_chunk = overlap_words
                            temp_length = sum(len(w) + 1 for w in temp_chunk)
                        else:
                            temp_chunk = []
                            temp_length = 0
                    temp_chunk.append(word)
                    temp_length += word_length
                
                if temp_chunk:
                    current_chunk.extend(temp_chunk)
                    current_length += temp_length
                continue
            
            if current_length + sentence_length > self.chunk_size and current_chunk:
                # 현재 청크 저장
                chunks.append(" ".join(current_chunk))
                
                # 오버랩 처리
                if self.chunk_overlap > 0:
                    overlap_text = " ".join(current_chunk)
                    overlap_sentences = re.split(r'(?<=[.!?])\s+', overlap_text)
                    if len(overlap_sentences) == 1:
                        overlap_sentences = overlap_text.split('\n')
                    overlap_length = 0
                    overlap_chunk = []
                    
                    for sent in reversed(overlap_sentences):
                        sent = sent.strip()
                        if not sent:
                            continue
                        if overlap_length + len(sent) <= self.chunk_overlap:
                            overlap_chunk.insert(0, sent)
                            overlap_length += len(sent) + 1
                        else:
                            break
                    
                    current_chunk = overlap_chunk
                    current_length = overlap_length
                else:
                    current_chunk = []
                    current_length = 0
            
            current_chunk.append(sentence)
            current_length += sentence_length + 1  # 공백 포함
        
        # 마지막 청크 추가
        if current_chunk:
            chunks.append(" ".join(current_chunk))
        
        return chunks if chunks else [text]
    
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

