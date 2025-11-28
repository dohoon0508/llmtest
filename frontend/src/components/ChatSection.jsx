import React, { useState, useRef, useEffect } from 'react'
import axios from 'axios'
import ReactMarkdown from 'react-markdown'

function ChatSection({ selectedFolder, selectedRegion }) {
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const messagesEndRef = useRef(null)

  const quickQuestions = [
    "준주거지역 건축허가에 필요한 서류는?",
    "에너지절약계획서 작성 방법",
    "주차장 설치 기준 법령",
    "내진설계 의무 대상"
  ]

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  useEffect(() => {
    // 폴더나 지역이 변경되면 메시지 초기화
    setMessages([])
  }, [selectedFolder, selectedRegion])

  const handleSend = async (e) => {
    e.preventDefault()
    if (!input.trim() || loading || !selectedFolder) return

    const userMessage = input.trim()
    setInput('')
    setError(null)

    const newMessages = [...messages, { role: 'user', content: userMessage }]
    setMessages(newMessages)
    setLoading(true)

    try {
      const response = await axios.post('/api/rag/query', {
        query: userMessage,
        folder: selectedFolder,  // 선택된 폴더 전달
        region: selectedRegion   // 선택된 지역 전달 (선택사항)
      }, {
        timeout: 90000  // 90초 타임아웃
      })

      setMessages([
        ...newMessages,
        {
          role: 'assistant',
          content: response.data.answer,
          chunks: response.data.chunks,
          sources: response.data.sources
        }
      ])
    } catch (err) {
      console.error('Query error:', err)
      
      if (err.response?.data?.answer) {
        setMessages([...newMessages, {
          role: 'assistant',
          content: err.response.data.answer,
          error: true
        }])
        setError(null)
      } else {
        const errorMsg = err.response?.data?.detail || err.message || '알 수 없는 오류가 발생했습니다.'
        setError(errorMsg)
        setMessages([...newMessages, {
          role: 'assistant',
          content: `죄송합니다. 오류가 발생했습니다: ${errorMsg}`,
          error: true
        }])
      }
    } finally {
      setLoading(false)
    }
  }

  const handleQuickQuestion = (question) => {
    setInput(question)
  }

  const getFolderName = (folder) => {
    if (!folder) return ''
    const parts = folder.split('_')
    return parts[parts.length - 1]
  }

  return (
    <div className="chat-page">
      <div className="chat-page-header">
        <h1>서류 작성 AI</h1>
        <p className="chat-page-subtitle">법령, 조례, 서류 양식에 대해 무엇이든 물어보세요</p>
      </div>

      {selectedFolder && (
        <div className="project-card">
          <div className="project-icon">🏢</div>
          <div className="project-info">
            <h3>현재 프로젝트</h3>
            <p className="project-subtitle">전주 덕진구 건축</p>
            <div className="project-details">
              <div className="project-detail-item">
                <span className="detail-label">건축 양식:</span>
                <span className="detail-value">{getFolderName(selectedFolder)}</span>
              </div>
            </div>
          </div>
        </div>
      )}

      <div className="quick-questions-card">
        <div className="quick-questions-header">
          <span className="quick-questions-icon">✨</span>
          <h3>빠른 질문</h3>
        </div>
        <div className="quick-questions-list">
          {quickQuestions.map((question, idx) => (
            <button
              key={idx}
              className="quick-question-btn"
              onClick={() => handleQuickQuestion(question)}
              disabled={loading || !selectedFolder}
            >
              {question}
            </button>
          ))}
        </div>
      </div>

      <div className="chat-container">
        <div className="chat-messages">
          {messages.length === 0 && (
            <div className="welcome-message">
              <h3>안녕하세요! 👋</h3>
              <p>건축허가 관련 문서에 대해 질문해보세요. RAG 시스템이 도와드립니다.</p>
              {!selectedFolder && (
                <p className="warning-message">⚠️ 왼쪽 사이드바에서 건축 양식을 선택해주세요.</p>
              )}
            </div>
          )}
          
          {messages.map((msg, idx) => (
            <div key={idx} className={`message ${msg.role}`}>
              <div className="message-content markdown-content">
                <ReactMarkdown>{msg.content}</ReactMarkdown>
              </div>
              {msg.role === 'assistant' && msg.chunks && (
                <div className="message-sources">
                  <details>
                    <summary>참고 문서 ({msg.chunks.length}개)</summary>
                    {msg.chunks.map((chunk, i) => (
                      <div key={i} className="source-item">
                        <div className="source-header">
                          <span>{chunk.metadata?.filename || 'unknown'}</span>
                          <span className="score">{(chunk.score * 100).toFixed(1)}%</span>
                        </div>
                        <div className="source-content">{chunk.content}</div>
                      </div>
                    ))}
                  </details>
                </div>
              )}
            </div>
          ))}
          
          {loading && (
            <div className="message assistant">
              <div className="message-content">
                <span className="typing-indicator">●</span>
                <span className="typing-indicator">●</span>
                <span className="typing-indicator">●</span>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {error && (
          <div className="error-banner">
            {error}
          </div>
        )}

        <form className="chat-input-form" onSubmit={handleSend}>
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder={selectedFolder ? "메시지를 입력하세요..." : "건축 양식을 먼저 선택해주세요"}
            disabled={loading || !selectedFolder}
            className="chat-input"
          />
          <button type="submit" disabled={loading || !input.trim() || !selectedFolder} className="send-btn">
            전송
          </button>
        </form>
      </div>
    </div>
  )
}

export default ChatSection
