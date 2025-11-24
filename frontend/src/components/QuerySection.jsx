import React, { useState } from 'react'
import axios from 'axios'

function QuerySection() {
  const [query, setQuery] = useState('')
  const [loading, setLoading] = useState(false)
  const [response, setResponse] = useState(null)
  const [error, setError] = useState(null)
  const [chunkSize, setChunkSize] = useState('')
  const [chunkOverlap, setChunkOverlap] = useState('')
  const [similarityThreshold, setSimilarityThreshold] = useState('')
  const [topK, setTopK] = useState('')

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError(null)
    setResponse(null)

    try {
      const params = {}
      if (chunkSize) params.chunk_size = parseInt(chunkSize)
      if (chunkOverlap) params.chunk_overlap = parseInt(chunkOverlap)
      if (similarityThreshold) params.similarity_threshold = parseFloat(similarityThreshold)
      if (topK) params.top_k = parseInt(topK)

      const response = await axios.post('/api/rag/query', {
        query: query
      }, { params })

      setResponse(response.data)
    } catch (err) {
      setError(err.response?.data?.detail || err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="card">
      <h2>질문하기</h2>
      
      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label>질문</label>
          <textarea
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="질문을 입력하세요..."
            required
          />
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginBottom: '1.5rem' }}>
          <div className="form-group">
            <label>청크 크기 (선택)</label>
            <input
              type="number"
              value={chunkSize}
              onChange={(e) => setChunkSize(e.target.value)}
              placeholder="기본값 사용"
              min="100"
              max="5000"
            />
          </div>
          <div className="form-group">
            <label>청크 오버랩 (선택)</label>
            <input
              type="number"
              value={chunkOverlap}
              onChange={(e) => setChunkOverlap(e.target.value)}
              placeholder="기본값 사용"
              min="0"
              max="1000"
            />
          </div>
          <div className="form-group">
            <label>유사도 임계값 (선택)</label>
            <input
              type="number"
              step="0.1"
              value={similarityThreshold}
              onChange={(e) => setSimilarityThreshold(e.target.value)}
              placeholder="기본값 사용"
              min="0"
              max="1"
            />
          </div>
          <div className="form-group">
            <label>상위 K개 문서 (선택)</label>
            <input
              type="number"
              value={topK}
              onChange={(e) => setTopK(e.target.value)}
              placeholder="기본값 사용"
              min="1"
              max="20"
            />
          </div>
        </div>

        <button type="submit" className="btn btn-primary" disabled={loading}>
          {loading ? '처리 중...' : '질문하기'}
        </button>
      </form>

      {error && <div className="error">{error}</div>}

      {response && (
        <div style={{ marginTop: '2rem' }}>
          <h3>답변</h3>
          <div style={{ background: '#f9f9f9', padding: '1rem', borderRadius: '8px', marginBottom: '1rem' }}>
            {response.answer}
          </div>

          <h3>참고 문서 ({response.chunks.length}개)</h3>
          {response.chunks.map((chunk, idx) => (
            <div key={idx} style={{ marginBottom: '1rem', padding: '1rem', background: '#f9f9f9', borderRadius: '8px' }}>
              <div style={{ fontSize: '0.9rem', color: '#666', marginBottom: '0.5rem' }}>
                출처: {chunk.metadata?.filename || 'unknown'} | 
                유사도: {chunk.score ? (chunk.score * 100).toFixed(2) + '%' : 'N/A'}
              </div>
              <div>{chunk.content}</div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

export default QuerySection

