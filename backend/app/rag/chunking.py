"""
Intelligent text chunking for RAG
Implements semantic chunking with sentence boundaries and overlap
"""

import re
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class ChunkingStrategy:
    """
    Advanced text chunking with multiple strategies
    """
    
    def __init__(
        self,
        chunk_size: int = 1000,
        overlap: int = 200,
        respect_sentences: bool = True,
        min_chunk_size: int = 100
    ):
        """
        Initialize chunking strategy
        
        Args:
            chunk_size: Target characters per chunk
            overlap: Characters to overlap between chunks
            respect_sentences: Try to break on sentence boundaries
            min_chunk_size: Minimum chunk size before forcing split
        """
        self.chunk_size = chunk_size
        self.overlap = overlap
        self.respect_sentences = respect_sentences
        self.min_chunk_size = min_chunk_size
        
        # Sentence boundary patterns (Spanish + English)
        self.sentence_endings = re.compile(
            r'(?<=[.!?…])\s+(?=[A-ZÁÉÍÓÚÑ])',  # Spanish uppercase
            re.MULTILINE
        )
        
        # Paragraph boundaries
        self.paragraph_sep = re.compile(r'\n\s*\n')
    
    def split_into_sentences(self, text: str) -> List[str]:
        """
        Split text into sentences respecting Spanish and English punctuation
        
        Args:
            text: Input text
            
        Returns:
            List of sentences
        """
        # First try paragraph-level split
        paragraphs = self.paragraph_sep.split(text)
        
        sentences = []
        for para in paragraphs:
            if not para.strip():
                continue
            
            # Split by sentence boundaries
            para_sentences = self.sentence_endings.split(para)
            
            # Clean and filter
            for sent in para_sentences:
                sent = sent.strip()
                if sent and len(sent) > 10:  # Filter very short fragments
                    sentences.append(sent)
        
        return sentences
    
    def chunk_by_sentences(self, text: str) -> List[str]:
        """
        Create chunks respecting sentence boundaries
        
        Args:
            text: Input text
            
        Returns:
            List of text chunks
        """
        sentences = self.split_into_sentences(text)
        
        if not sentences:
            return []
        
        chunks = []
        current_chunk = []
        current_length = 0
        
        for i, sentence in enumerate(sentences):
            sentence_length = len(sentence)
            
            # If adding this sentence exceeds chunk size
            if current_length + sentence_length > self.chunk_size and current_chunk:
                # Save current chunk
                chunk_text = ' '.join(current_chunk)
                chunks.append(chunk_text)
                
                # Start new chunk with overlap
                # Include last few sentences for context
                overlap_sentences = []
                overlap_length = 0
                
                for prev_sent in reversed(current_chunk):
                    if overlap_length + len(prev_sent) <= self.overlap:
                        overlap_sentences.insert(0, prev_sent)
                        overlap_length += len(prev_sent)
                    else:
                        break
                
                current_chunk = overlap_sentences
                current_length = overlap_length
            
            # Add sentence to current chunk
            current_chunk.append(sentence)
            current_length += sentence_length
        
        # Add final chunk
        if current_chunk:
            chunk_text = ' '.join(current_chunk)
            chunks.append(chunk_text)
        
        return chunks
    
    def chunk_by_characters(self, text: str) -> List[str]:
        """
        Simple character-based chunking with overlap (fallback)
        
        Args:
            text: Input text
            
        Returns:
            List of text chunks
        """
        if not text:
            return []
        
        chunks = []
        start = 0
        length = len(text)
        
        while start < length:
            end = min(start + self.chunk_size, length)
            
            # Try to find a word boundary near the end
            if end < length and self.respect_sentences:
                # Look back for space
                boundary_search = text[max(start, end - 100):end]
                last_space = boundary_search.rfind(' ')
                
                if last_space > 0:
                    end = max(start, end - 100) + last_space
            
            chunk = text[start:end].strip()
            
            if chunk and len(chunk) >= self.min_chunk_size:
                chunks.append(chunk)
            
            # Move start position with overlap
            start = end - self.overlap if end < length else end
            
            # Prevent infinite loop
            if start <= 0:
                start = end
        
        return chunks
    
    def chunk_by_paragraphs(self, text: str) -> List[str]:
        """
        Chunk by paragraphs, combining small paragraphs
        
        Args:
            text: Input text
            
        Returns:
            List of text chunks
        """
        paragraphs = self.paragraph_sep.split(text)
        
        chunks = []
        current_chunk = []
        current_length = 0
        
        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
            
            para_length = len(para)
            
            # If paragraph alone exceeds chunk size, split it
            if para_length > self.chunk_size * 1.5:
                # Save current chunk if any
                if current_chunk:
                    chunks.append('\n\n'.join(current_chunk))
                    current_chunk = []
                    current_length = 0
                
                # Split large paragraph by sentences
                para_chunks = self.chunk_by_sentences(para)
                chunks.extend(para_chunks)
                continue
            
            # If adding this paragraph exceeds chunk size
            if current_length + para_length > self.chunk_size and current_chunk:
                chunks.append('\n\n'.join(current_chunk))
                
                # Start new chunk with last paragraph as overlap
                if len(current_chunk) > 0 and len(current_chunk[-1]) <= self.overlap:
                    current_chunk = [current_chunk[-1]]
                    current_length = len(current_chunk[-1])
                else:
                    current_chunk = []
                    current_length = 0
            
            current_chunk.append(para)
            current_length += para_length
        
        # Add final chunk
        if current_chunk:
            chunks.append('\n\n'.join(current_chunk))
        
        return chunks
    
    def chunk(self, text: str, strategy: str = 'auto') -> List[Dict[str, Any]]:
        """
        Chunk text using specified strategy
        
        Args:
            text: Input text
            strategy: 'auto', 'sentences', 'paragraphs', 'characters'
            
        Returns:
            List of chunk dicts with text and metadata
        """
        if not text or not text.strip():
            return []
        
        # Normalize whitespace
        text = re.sub(r'\r\n', '\n', text)
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        # Choose strategy
        if strategy == 'auto':
            # Auto-detect best strategy
            has_paragraphs = bool(self.paragraph_sep.search(text))
            has_sentences = bool(self.sentence_endings.search(text))
            
            if has_paragraphs and len(text) > self.chunk_size:
                strategy = 'paragraphs'
            elif has_sentences:
                strategy = 'sentences'
            else:
                strategy = 'characters'
        
        # Execute chunking
        if strategy == 'sentences':
            chunks = self.chunk_by_sentences(text)
        elif strategy == 'paragraphs':
            chunks = self.chunk_by_paragraphs(text)
        else:  # characters
            chunks = self.chunk_by_characters(text)
        
        # Add metadata
        result = []
        for i, chunk_text in enumerate(chunks):
            result.append({
                'text': chunk_text,
                'index': i,
                'length': len(chunk_text),
                'strategy': strategy
            })
        
        logger.info(f"Created {len(result)} chunks using '{strategy}' strategy")
        return result


# Singleton instance
_chunking_strategy_instance: Optional[ChunkingStrategy] = None

def get_chunking_strategy(
    chunk_size: int = 1000,
    overlap: int = 200
) -> ChunkingStrategy:
    """
    Get or create chunking strategy singleton
    
    Args:
        chunk_size: Target characters per chunk
        overlap: Characters to overlap
        
    Returns:
        ChunkingStrategy instance
    """
    global _chunking_strategy_instance
    
    if _chunking_strategy_instance is None:
        _chunking_strategy_instance = ChunkingStrategy(
            chunk_size=chunk_size,
            overlap=overlap
        )
    
    return _chunking_strategy_instance
