import React, { useState } from 'react'
import axios from 'axios'

function EvaluationSection() {
  const [query, setQuery] = useState('')
  const [expectedDocs, setExpectedDocs] = useState('')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)

  const handleEvaluate = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError(null)
    setResult(null)

    try {
      const expectedDocsList = expectedDocs.split(',').map(doc => doc.trim()).filter(doc => doc)
      const response = await axios.post('/api/rag/evaluate', null, {
        params: {
          query: query,
          expected_documents: expectedDocsList
        }
      })
      setResult(response.data)
    } catch (err) {
      setError(err.response?.data?.detail || err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="card">
      <h2>문서 매칭 정확도 평가</h2>
      <p style={{ marginBottom: '1.5rem', color: '#666' }}>
        질문에 대해 예상되는 문서를 입력하고, 실제 검색된 문서와의 정확도를 확인합니다.
      </p>
      
      <form onSubmit={handleEvaluate}>
        <div className="form-group">
          <label>질문</label>
          <textarea
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="평가할 질문을 입력하세요..."
            required
          />
        </div>

        <div className="form-group">
          <label>예상 문서 ID (쉼표로 구분)</label>
          <input
            type="text"
            value={expectedDocs}
            onChange={(e) => setExpectedDocs(e.target.value)}
            placeholder="예: doc1, doc2, doc3"
            required
          />
        </div>

        <button type="submit" className="btn btn-primary" disabled={loading}>
          {loading ? '평가 중...' : '정확도 평가'}
        </button>
      </form>

      {error && <div className="error">{error}</div>}

      {result && (
        <div style={{ marginTop: '2rem' }}>
          <h3>평가 결과</h3>
          
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '1rem', marginBottom: '1.5rem' }}>
            <div style={{ padding: '1rem', background: '#f0f8ff', borderRadius: '8px', textAlign: 'center' }}>
              <div style={{ fontSize: '0.9rem', color: '#666', marginBottom: '0.5rem' }}>정밀도 (Precision)</div>
              <div style={{ fontSize: '2rem', fontWeight: 'bold', color: '#667eea' }}>
                {(result.precision * 100).toFixed(2)}%
              </div>
            </div>
            <div style={{ padding: '1rem', background: '#f0fff0', borderRadius: '8px', textAlign: 'center' }}>
              <div style={{ fontSize: '0.9rem', color: '#666', marginBottom: '0.5rem' }}>재현율 (Recall)</div>
              <div style={{ fontSize: '2rem', fontWeight: 'bold', color: '#4caf50' }}>
                {(result.recall * 100).toFixed(2)}%
              </div>
            </div>
            <div style={{ padding: '1rem', background: '#fff8f0', borderRadius: '8px', textAlign: 'center' }}>
              <div style={{ fontSize: '0.9rem', color: '#666', marginBottom: '0.5rem' }}>F1 점수</div>
              <div style={{ fontSize: '2rem', fontWeight: 'bold', color: '#ff9800' }}>
                {(result.f1_score * 100).toFixed(2)}%
              </div>
            </div>
          </div>

          <div style={{ marginBottom: '1rem' }}>
            <strong>예상 문서:</strong> {result.expected_documents.join(', ')}
          </div>
          <div style={{ marginBottom: '1rem' }}>
            <strong>검색된 문서:</strong> {result.retrieved_documents.join(', ')}
          </div>
          <div>
            <strong>매칭된 문서 수:</strong> {result.matched_count} / {result.expected_documents.length}
          </div>
        </div>
      )}
    </div>
  )
}

export default EvaluationSection

