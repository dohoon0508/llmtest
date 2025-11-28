import React, { useState, useRef, useEffect } from 'react'

function Sidebar({ selectedFolder, onSelectFolder, selectedRegion, onSelectRegion }) {
  const [isOpen, setIsOpen] = useState(false)
  const [isRegionOpen, setIsRegionOpen] = useState(false)
  const dropdownRef = useRef(null)
  const regionDropdownRef = useRef(null)

  // 실제 documents 폴더 구조에 맞춘 건물 유형 옵션
  const folderOptions = [
    // 공동주택
    { 
      value: '공동주택(기숙사)', 
      label: '공동주택(기숙사)',
      fullName: '공동주택(기숙사)'
    },
    { 
      value: '공동주택(다세대주택)', 
      label: '공동주택(다세대주택)',
      fullName: '공동주택(다세대주택)'
    },
    { 
      value: '공동주택(아파트)', 
      label: '공동주택(아파트)',
      fullName: '공동주택(아파트)'
    },
    { 
      value: '공동주택(연립주택)', 
      label: '공동주택(연립주택)',
      fullName: '공동주택(연립주택)'
    },
    // 주택
    { 
      value: '다가구주택', 
      label: '다가구주택',
      fullName: '다가구주택'
    },
    { 
      value: '다중주택', 
      label: '다중주택',
      fullName: '다중주택'
    },
    { 
      value: '단독주택', 
      label: '단독주택',
      fullName: '단독주택'
    },
    // 숙박시설
    { 
      value: '숙박시설(관광숙박시설)', 
      label: '숙박시설(관광숙박시설)',
      fullName: '숙박시설(관광숙박시설)'
    },
    { 
      value: '숙박시설(다중생활시설)', 
      label: '숙박시설(다중생활시설)',
      fullName: '숙박시설(다중생활시설)'
    },
    { 
      value: '숙박시설(생활숙박시설)', 
      label: '숙박시설(생활숙박시설)',
      fullName: '숙박시설(생활숙박시설)'
    },
    { 
      value: '숙박시설(일반숙박시설)', 
      label: '숙박시설(일반숙박시설)',
      fullName: '숙박시설(일반숙박시설)'
    },
    // 판매시설
    { 
      value: '판매시설(도매시장)', 
      label: '판매시설(도매시장)',
      fullName: '판매시설(도매시장)'
    },
    { 
      value: '판매시설(상점)', 
      label: '판매시설(상점)',
      fullName: '판매시설(상점)'
    },
    { 
      value: '판매시설(소매시장)', 
      label: '판매시설(소매시장)',
      fullName: '판매시설(소매시장)'
    },
    // 업무시설
    { 
      value: '업무시설(공공업무시설)', 
      label: '업무시설(공공업무시설)',
      fullName: '업무시설(공공업무시설)'
    },
    { 
      value: '업무시설(일반업무시설)', 
      label: '업무시설(일반업무시설)',
      fullName: '업무시설(일반업무시설)'
    },
    // 창고시설
    { 
      value: '창고시설(공장)', 
      label: '창고시설(공장)',
      fullName: '창고시설(공장)'
    },
    { 
      value: '창고시설(집배송시설)', 
      label: '창고시설(집배송시설)',
      fullName: '창고시설(집배송시설)'
    },
    { 
      value: '창고시설(하역장)', 
      label: '창고시설(하역장)',
      fullName: '창고시설(하역장)'
    },
    // 기타
    { 
      value: '공장', 
      label: '공장',
      fullName: '공장'
    },
    { 
      value: '관광휴계시설(휴게소)', 
      label: '관광휴계시설(휴게소)',
      fullName: '관광휴계시설(휴게소)'
    }
  ]

  // 지역 옵션 (향후 확장 가능)
  const regionOptions = [
    { 
      value: '전주시', 
      label: '전주시',
      fullName: '전주시'
    }
    // 향후 다른 지역 추가 가능
    // { value: '서울시', label: '서울시', fullName: '서울시' },
    // { value: '부산시', label: '부산시', fullName: '부산시' },
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
      if (regionDropdownRef.current && !regionDropdownRef.current.contains(event.target)) {
        setIsRegionOpen(false)
      }
    }

    if (isOpen || isRegionOpen) {
      document.addEventListener('mousedown', handleClickOutside)
    }

    return () => {
      document.removeEventListener('mousedown', handleClickOutside)
    }
  }, [isOpen, isRegionOpen])

  const handleSelect = (folderName) => {
    onSelectFolder(folderName)
    setIsOpen(false)
  }

  const handleRegionSelect = (regionName) => {
    onSelectRegion(regionName)
    setIsRegionOpen(false)
  }

  const getSelectedRegionLabel = () => {
    if (!selectedRegion) return '지역 선택 (선택사항)'
    const option = regionOptions.find(opt => opt.fullName === selectedRegion)
    return option ? option.label : selectedRegion
  }

  // 초기 선택 설정
  useEffect(() => {
    if (!selectedFolder && folderOptions.length > 0) {
      onSelectFolder(folderOptions[0].fullName)
    }
    // 지역은 선택사항이므로 기본값 없음
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

        <div className="nav-section">
          <div className="nav-section-title">지역 선택 (선택사항)</div>
          <div className="dropdown-container" ref={regionDropdownRef}>
            <button
              className="dropdown-button"
              onClick={() => setIsRegionOpen(!isRegionOpen)}
              type="button"
            >
              <span className="dropdown-icon">📍</span>
              <span className="dropdown-text">{getSelectedRegionLabel()}</span>
              <span className={`dropdown-arrow ${isRegionOpen ? 'open' : ''}`}>▼</span>
            </button>
            
            {isRegionOpen && (
              <div className="dropdown-menu">
                <div
                  className={`dropdown-item ${!selectedRegion ? 'selected' : ''}`}
                  onClick={() => handleRegionSelect(null)}
                >
                  <span className="dropdown-item-icon">📍</span>
                  <span>지역 선택 안함</span>
                  {!selectedRegion && <span className="dropdown-check">✓</span>}
                </div>
                {regionOptions.map(option => {
                  const isSelected = selectedRegion === option.fullName
                  return (
                    <div
                      key={option.fullName}
                      className={`dropdown-item ${isSelected ? 'selected' : ''}`}
                      onClick={() => handleRegionSelect(option.fullName)}
                    >
                      <span className="dropdown-item-icon">📍</span>
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

      {(selectedFolder || selectedRegion) && (
        <div className="sidebar-footer">
          {selectedFolder && (
            <div className="selected-folder-info">
              <span className="folder-label">건축 양식:</span>
              <span className="folder-name">{getFolderLabel(selectedFolder)}</span>
            </div>
          )}
          {selectedRegion && (
            <div className="selected-folder-info">
              <span className="folder-label">지역:</span>
              <span className="folder-name">{getSelectedRegionLabel()}</span>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

export default Sidebar

