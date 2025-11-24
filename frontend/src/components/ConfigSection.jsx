import React, { useState } from 'react'
import axios from 'axios'

function ConfigSection() {
  const [chunkConfig, setChunkConfig] = useState({ chunk_size: 1000, chunk_overlap: 200, chunk_by_row: false })
  const [similarityConfig, setSimilarityConfig] = useState({ similarity_threshold: 0.7, top_k: 5 })
  const [weightConfig, setWeightConfig] = useState({ similarity_weight: 1.0, recency_weight: 0.0, source_weight: 0.0 })
  const [message, setMessage] = useState(null)
  const [error, setError] = useState(null)

  const handleChunkConfigUpdate = async (e) => {
    e.preventDefault()
    setError(null)
    setMessage(null)

    try {
      await axios.put('/api/rag/chunk-config', chunkConfig)
      setMessage('청킹 설정이 업데이트되었습니다.')
    } catch (err) {
      setError(err.response?.data?.detail || err.message)
    }
  }

  const handleSimilarityConfigUpdate = async (e) => {
    e.preventDefault()
    setError(null)
    setMessage(null)

    try {
      await axios.put('/api/rag/similarity-config', similarityConfig)
      setMessage('유사도 설정이 업데이트되었습니다.')
    } catch (err) {
      setError(err.response?.data?.detail || err.message)
    }
  }

  const handleWeightConfigUpdate = async (e) => {
    e.preventDefault()
    setError(null)
    setMessage(null)

    try {
      await axios.put('/api/rag/weight-config', weightConfig)
      setMessage('가중치 설정이 업데이트되었습니다.')
    } catch (err) {
      setError(err.response?.data?.detail || err.message)
    }
  }

  return (
    <div>
      <div className="card">
        <h2>청킹 설정</h2>
        <p style={{ marginBottom: '1rem', color: '#666' }}>
          문서를 분할할 때 사용하는 청크 크기와 오버랩을 설정합니다.
        </p>
        
        <form onSubmit={handleChunkConfigUpdate}>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginBottom: '1.5rem' }}>
            <div className="form-group">
              <label>청크 크기</label>
              <input
                type="number"
                value={chunkConfig.chunk_size}
                onChange={(e) => setChunkConfig({ ...chunkConfig, chunk_size: parseInt(e.target.value) })}
                min="100"
                max="5000"
                required
              />
            </div>
            <div className="form-group">
              <label>청크 오버랩</label>
              <input
                type="number"
                value={chunkConfig.chunk_overlap}
                onChange={(e) => setChunkConfig({ ...chunkConfig, chunk_overlap: parseInt(e.target.value) })}
                min="0"
                max="1000"
                required
              />
            </div>
            <div className="form-group">
              <label>
                <input
                  type="checkbox"
                  checked={chunkConfig.chunk_by_row}
                  onChange={(e) => setChunkConfig({ ...chunkConfig, chunk_by_row: e.target.checked })}
                  style={{ marginRight: '0.5rem' }}
                />
                Row 단위 청킹 (CSV/Excel용)
              </label>
            </div>
          </div>

          <button type="submit" className="btn btn-primary">
            청킹 설정 업데이트
          </button>
        </form>
      </div>

      <div className="card">
        <h2>유사도 설정</h2>
        <p style={{ marginBottom: '1rem', color: '#666' }}>
          문서 검색 시 사용하는 유사도 임계값과 반환할 문서 개수를 설정합니다.
        </p>
        
        <form onSubmit={handleSimilarityConfigUpdate}>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginBottom: '1.5rem' }}>
            <div className="form-group">
              <label>유사도 임계값</label>
              <input
                type="number"
                step="0.1"
                value={similarityConfig.similarity_threshold}
                onChange={(e) => setSimilarityConfig({ ...similarityConfig, similarity_threshold: parseFloat(e.target.value) })}
                min="0"
                max="1"
                required
              />
            </div>
            <div className="form-group">
              <label>상위 K개 문서</label>
              <input
                type="number"
                value={similarityConfig.top_k}
                onChange={(e) => setSimilarityConfig({ ...similarityConfig, top_k: parseInt(e.target.value) })}
                min="1"
                max="20"
                required
              />
            </div>
          </div>

          <button type="submit" className="btn btn-primary">
            유사도 설정 업데이트
          </button>
        </form>
      </div>

      <div className="card">
        <h2>RAG 가중치 설정</h2>
        <p style={{ marginBottom: '1rem', color: '#666' }}>
          검색 결과에 적용할 가중치를 설정합니다. 유사도 외에 최신성, 출처 등을 고려할 수 있습니다.
        </p>
        
        <form onSubmit={handleWeightConfigUpdate}>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '1rem', marginBottom: '1.5rem' }}>
            <div className="form-group">
              <label>유사도 가중치</label>
              <input
                type="number"
                step="0.1"
                value={weightConfig.similarity_weight}
                onChange={(e) => setWeightConfig({ ...weightConfig, similarity_weight: parseFloat(e.target.value) })}
                min="0"
                max="2"
                required
              />
            </div>
            <div className="form-group">
              <label>최신성 가중치</label>
              <input
                type="number"
                step="0.1"
                value={weightConfig.recency_weight}
                onChange={(e) => setWeightConfig({ ...weightConfig, recency_weight: parseFloat(e.target.value) })}
                min="0"
                max="1"
                required
              />
            </div>
            <div className="form-group">
              <label>출처 가중치</label>
              <input
                type="number"
                step="0.1"
                value={weightConfig.source_weight}
                onChange={(e) => setWeightConfig({ ...weightConfig, source_weight: parseFloat(e.target.value) })}
                min="0"
                max="1"
                required
              />
            </div>
          </div>

          <button type="submit" className="btn btn-primary">
            가중치 설정 업데이트
          </button>
        </form>
      </div>

      {message && <div className="success">{message}</div>}
      {error && <div className="error">{error}</div>}
    </div>
  )
}

export default ConfigSection

