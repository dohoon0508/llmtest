import React, { useState, useEffect } from 'react'
import ChatSection from './components/ChatSection'
import Sidebar from './components/Sidebar'
import './App.css'

function App() {
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

  const [selectedFolder, setSelectedFolder] = useState(
    folderOptions.length > 0 ? folderOptions[0].fullName : null
  )

  useEffect(() => {
    // 기본 폴더 선택
    if (folderOptions.length > 0 && !selectedFolder) {
      setSelectedFolder(folderOptions[0].fullName)
    }
  }, [])

  return (
    <div className="app">
      <Sidebar 
        selectedFolder={selectedFolder}
        onSelectFolder={setSelectedFolder}
      />
      <main className="app-main">
        <ChatSection selectedFolder={selectedFolder} />
      </main>
    </div>
  )
}

export default App
