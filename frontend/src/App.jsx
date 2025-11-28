import React, { useState, useEffect } from 'react'
import ChatSection from './components/ChatSection'
import Sidebar from './components/Sidebar'
import './App.css'

function App() {
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

  const [selectedFolder, setSelectedFolder] = useState(
    folderOptions.length > 0 ? folderOptions[0].fullName : null
  )
  const [selectedRegion, setSelectedRegion] = useState(null)

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
        selectedRegion={selectedRegion}
        onSelectRegion={setSelectedRegion}
      />
      <main className="app-main">
        <ChatSection selectedFolder={selectedFolder} selectedRegion={selectedRegion} />
      </main>
    </div>
  )
}

export default App
