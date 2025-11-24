import React, { useState, useRef, useEffect } from 'react'

function Sidebar({ selectedFolder, onSelectFolder }) {
  const [isOpen, setIsOpen] = useState(false)
  const dropdownRef = useRef(null)

  // 미리 정의된 건물 유형 옵션
  const folderOptions = [
    { 
      value: '다중주택', 
      label: '다중주택',
      fullName: '신축_일반개인_다중주택'
    },
    { 
      value: '단독주택', 
      label: '단독주택',
      fullName: '신축_일반개인_단독주택'
    },
    { 
      value: '숙박시설(생활숙박시설)', 
      label: '숙박시설',
      fullName: '신축_일반개인_숙박시설(생활숙박시설)'
    },
    { 
      value: '판매시설(도매시장)', 
      label: '판매시설',
      fullName: '신축_일반개인_판매시설(도매시장)'
    }
  ]

  // 실제 폴더명과 옵션 매칭
  const getMatchingOption = (folderName) => {
    if (!folderName) return null
    return folderOptions.find(opt => opt.fullName === folderName)
  }

  const getSelectedLabel = () => {
    if (!selectedFolder) return '건축 양식 선택'
    const option = getMatchingOption(selectedFolder)
    return option ? option.label : selectedFolder
  }

  const getFolderLabel = (folderName) => {
    if (!folderName) return ''
    const option = getMatchingOption(folderName)
    return option ? option.label : folderName
  }

  // 외부 클릭 시 드롭다운 닫기
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setIsOpen(false)
      }
    }

    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside)
    }

    return () => {
      document.removeEventListener('mousedown', handleClickOutside)
    }
  }, [isOpen])

  const handleSelect = (folderName) => {
    onSelectFolder(folderName)
    setIsOpen(false)
  }

  // 초기 선택 설정
  useEffect(() => {
    if (!selectedFolder && folderOptions.length > 0) {
      onSelectFolder(folderOptions[0].fullName)
    }
  }, [])

  return (
    <div className="sidebar">
      <div className="sidebar-header">
        <h1 className="sidebar-title">건축허가</h1>
        <p className="sidebar-subtitle">자동화 시스템</p>
        <button className="sidebar-menu-btn">☰</button>
      </div>

      <nav className="sidebar-nav">
        <div className="nav-item active">
          <span className="nav-icon">📄</span>
          <span>서류 작성 AI</span>
        </div>

        <div className="nav-section">
          <div className="nav-section-title">건축 양식 선택</div>
          <div className="dropdown-container" ref={dropdownRef}>
            <button
              className="dropdown-button"
              onClick={() => setIsOpen(!isOpen)}
              type="button"
            >
              <span className="dropdown-icon">🏢</span>
              <span className="dropdown-text">{getSelectedLabel()}</span>
              <span className={`dropdown-arrow ${isOpen ? 'open' : ''}`}>▼</span>
            </button>
            
            {isOpen && (
              <div className="dropdown-menu">
                {folderOptions.map(option => {
                  const isSelected = selectedFolder === option.fullName
                  return (
                    <div
                      key={option.fullName}
                      className={`dropdown-item ${isSelected ? 'selected' : ''}`}
                      onClick={() => handleSelect(option.fullName)}
                    >
                      <span className="dropdown-item-icon">🏢</span>
                      <span>{option.label}</span>
                      {isSelected && <span className="dropdown-check">✓</span>}
                    </div>
                  )
                })}
              </div>
            )}
          </div>
        </div>
      </nav>

      {selectedFolder && (
        <div className="sidebar-footer">
          <div className="selected-folder-info">
            <span className="folder-label">선택된 폴더:</span>
            <span className="folder-name">{getFolderLabel(selectedFolder)}</span>
          </div>
        </div>
      )}
    </div>
  )
}

export default Sidebar

