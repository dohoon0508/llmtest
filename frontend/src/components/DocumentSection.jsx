import React, { useState, useEffect } from 'react'
import axios from 'axios'

function DocumentSection() {
  const [documents, setDocuments] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [success, setSuccess] = useState(null)
  const [filename, setFilename] = useState('')
  const [content, setContent] = useState('')
  const [uploadMethod, setUploadMethod] = useState('text') // 'text' or 'file'
  const [selectedFile, setSelectedFile] = useState(null)

  useEffect(() => {
    loadDocuments()
  }, [])

  const loadDocuments = async () => {
    try {
      const response = await axios.get('/api/documents/list')
      setDocuments(response.data)
    } catch (err) {
      setError(err.response?.data?.detail || err.message)
    }
  }

  const handleFileSelect = (e) => {
    const file = e.target.files[0]
    if (file) {
      setSelectedFile(file)
      setFilename(file.name)
    }
  }

  const handleUpload = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError(null)
    setSuccess(null)

    try {
      if (uploadMethod === 'file' && selectedFile) {
        // 파일 업로드
        const formData = new FormData()
        formData.append('file', selectedFile)
        
        await axios.post('/api/documents/upload', formData, {
          headers: {
            'Content-Type': 'multipart/form-data'
          }
        })
        setSuccess('파일이 성공적으로 업로드되었습니다.')
        setSelectedFile(null)
        setFilename('')
      } else {
        // 텍스트 업로드
        await axios.post('/api/documents/upload-text', {
          filename: filename,
          content: content
        })
        setSuccess('문서가 성공적으로 업로드되었습니다.')
        setFilename('')
        setContent('')
      }
      loadDocuments()
    } catch (err) {
      setError(err.response?.data?.detail || err.message)
    } finally {
      setLoading(false)
    }
  }

  const handleDelete = async (docId) => {
    if (!confirm('정말 삭제하시겠습니까?')) return

    try {
      await axios.delete(`/api/documents/${docId}`)
      setSuccess('문서가 삭제되었습니다.')
      loadDocuments()
    } catch (err) {
      setError(err.response?.data?.detail || err.message)
    }
  }

  return (
    <div>
      <div className="card">
        <h2>문서 업로드</h2>
        
        <div style={{ marginBottom: '1.5rem' }}>
          <label style={{ marginRight: '1rem' }}>
            <input
              type="radio"
              value="text"
              checked={uploadMethod === 'text'}
              onChange={(e) => setUploadMethod(e.target.value)}
              style={{ marginRight: '0.5rem' }}
            />
            텍스트 입력
          </label>
          <label>
            <input
              type="radio"
              value="file"
              checked={uploadMethod === 'file'}
              onChange={(e) => setUploadMethod(e.target.value)}
              style={{ marginRight: '0.5rem' }}
            />
            파일 업로드 (txt, csv, xlsx 지원)
          </label>
        </div>
        
        <form onSubmit={handleUpload}>
          {uploadMethod === 'file' ? (
            <div className="form-group">
              <label>파일 선택</label>
              <input
                type="file"
                onChange={handleFileSelect}
                accept=".txt,.csv,.xlsx,.xls,.md"
                required={uploadMethod === 'file'}
              />
              {selectedFile && (
                <div style={{ marginTop: '0.5rem', fontSize: '0.9rem', color: '#666' }}>
                  선택된 파일: {selectedFile.name} ({(selectedFile.size / 1024).toFixed(2)} KB)
                </div>
              )}
            </div>
          ) : (
            <>
              <div className="form-group">
                <label>파일명</label>
                <input
                  type="text"
                  value={filename}
                  onChange={(e) => setFilename(e.target.value)}
                  placeholder="예: 문서1.txt"
                  required
                />
              </div>

              <div className="form-group">
                <label>내용</label>
                <textarea
                  value={content}
                  onChange={(e) => setContent(e.target.value)}
                  placeholder="문서 내용을 입력하세요..."
                  required
                  style={{ minHeight: '200px' }}
                />
              </div>
            </>
          )}

          <button type="submit" className="btn btn-primary" disabled={loading}>
            {loading ? '업로드 중...' : '업로드'}
          </button>
        </form>

        {error && <div className="error">{error}</div>}
        {success && <div className="success">{success}</div>}
      </div>

      <div className="card">
        <h2>저장된 문서 목록</h2>
        
        {documents.length === 0 ? (
          <p>저장된 문서가 없습니다.</p>
        ) : (
          <div style={{ display: 'grid', gap: '1rem' }}>
            {documents.map((doc) => (
              <div key={doc.id} style={{ padding: '1rem', background: '#f9f9f9', borderRadius: '8px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div>
                  <div style={{ fontWeight: 'bold', marginBottom: '0.5rem' }}>{doc.filename}</div>
                  <div style={{ fontSize: '0.9rem', color: '#666' }}>
                    ID: {doc.id} | 청크 수: {doc.chunk_count} | 생성일: {new Date(doc.created_at).toLocaleString('ko-KR')}
                  </div>
                </div>
                <button
                  className="btn btn-secondary"
                  onClick={() => handleDelete(doc.id)}
                  style={{ padding: '0.5rem 1rem' }}
                >
                  삭제
                </button>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

export default DocumentSection

