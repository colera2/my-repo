import React, { useState } from 'react';
import './FileUploader.css';

const FileUploader = () => {
  const [selectedFile, setSelectedFile] = useState(null);

  const handleFileChange = (e) => {
    if (e.target.files.length > 0) {
      setSelectedFile(e.target.files[0]);
    }
  };

  return (
    <div className="page-container">
      {/* 1. 헤더 섹션 */}
      <header className="header-section">
        <h1 className="main-title">마케팅 보고서 업로드</h1>
      </header>

      {/* 2. 메인 업로드 카드 */}
      <main className="upload-card">
        <div className="upload-header">
          <span className="upload-icon">📥</span>
          <h2 className="upload-title">파일 업로드</h2>
        </div>
        
        <p className="drag-guide">파일을 여기에 드래그하거나 클릭하세요</p>

        <div className="file-select-area">
          <label htmlFor="file-input" className="file-label">파일 선택</label>
          <input 
            type="file" 
            id="file-input" 
            onChange={handleFileChange} 
            className="hidden-input"
          />
          <span className="file-name">
            {selectedFile ? selectedFile.name : "선택된 파일 없음"}
          </span>
        </div>

        <button 
          className={`upload-button ${selectedFile ? 'active' : ''}`}
          disabled={!selectedFile}
        >
          업로드
        </button>
      </main>

      {/* 3. 하단 지원 파일 가이드 */}
      <footer className="guide-footer">
        <div className="guide-box">
          <span className="guide-tag">지원 파일</span>
          <p className="guide-text">
            네이버 : 검색광고, 검색채널, 사용자 정의 채널, 키워드 보고서<br/>
            쿠팡 : 키워드 보고서
          </p>
        </div>
      </footer>
    </div>
  );
};

export default FileUploader;
