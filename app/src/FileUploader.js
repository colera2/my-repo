import React, { useState, useRef } from 'react';
import './FileUploader.css';

export default function FileUploader() {
  const [file, setFile]         = useState(null);
  const [dragging, setDragging] = useState(false);
  const [loading, setLoading]   = useState(false);
  const [message, setMessage]   = useState(null); // { type: 'success'|'error', text }
  const inputRef = useRef(null);

  // 파일 선택 처리
  const handleFile = (selected) => {
    if (!selected) return;
    setFile(selected);
    setMessage(null);
  };

  // 드래그 이벤트
  const handleDragOver  = (e) => { e.preventDefault(); setDragging(true); };
  const handleDragLeave = ()  => setDragging(false);
  const handleDrop      = (e) => {
    e.preventDefault();
    setDragging(false);
    handleFile(e.dataTransfer.files?.[0]);
  };

  // 업로드
  const handleUpload = async () => {
    if (!file) return;
    setLoading(true);
    setMessage(null);

    const url = `/api/upload?filename=${encodeURIComponent(file.name)}`;
    try {
      const resp = await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/octet-stream' },
        body: file,
      });
      if (resp.ok) {
        setMessage({ type: 'success', text: '✅ 업로드가 완료되었습니다!' });
        setFile(null);
      } else {
        const text = await resp.text();
        setMessage({ type: 'error', text: `❌ 업로드 실패: ${text}` });
      }
    } catch (e) {
      setMessage({ type: 'error', text: `❌ 오류 발생: ${e.message}` });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="page">
      <div className="card">

        {/* 헤더 */}
        <div className="card-header">
          <span className="icon">📊</span>
          <h1 className="title">마케팅 보고서 업로드</h1>
          <p className="subtitle">보고서 파일을 업로드하면 자동으로 데이터베이스에 저장됩니다</p>
        </div>

        {/* 드래그앤드롭 영역 */}
        <div
          className={`drop-zone ${dragging ? 'dragging' : ''} ${file ? 'has-file' : ''}`}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          onClick={() => inputRef.current.click()}
        >
          <input
            ref={inputRef}
            type="file"
            accept=".xlsx,.csv"
            style={{ display: 'none' }}
            onChange={e => handleFile(e.target.files?.[0])}
          />
          {file ? (
            <div className="file-info">
              <span className="file-icon">📁</span>
              <span className="file-name">{file.name}</span>
              <span className="file-size">{(file.size / 1024).toFixed(1)} KB</span>
            </div>
          ) : (
            <div className="drop-guide">
              <span className="drop-icon">☁️</span>
              <p className="drop-text">파일을 여기에 드래그하거나 <span className="link">클릭해서 선택</span></p>
              <p className="drop-hint">지원 형식: .xlsx, .csv</p>
            </div>
          )}
        </div>

        {/* 지원 파일 형식 안내 */}
        <div className="format-guide">
          <p className="format-title">지원 파일 형식</p>
          <div className="format-list">
            <span className="badge">검색채널_날짜.xlsx</span>
            <span className="badge">사용자정의채널_날짜.xlsx</span>
            <span className="badge">검색광고_계정명.csv</span>
            <span className="badge">키워드보고서_계정명.csv</span>
            <span className="badge">계정명_pa_daily_keyword_날짜.xlsx</span>
          </div>
        </div>

        {/* 결과 메시지 */}
        {message && (
          <div className={`message ${message.type}`}>
            {message.text}
          </div>
        )}

        {/* 업로드 버튼 */}
        <button
          className={`upload-btn ${loading ? 'loading' : ''}`}
          onClick={handleUpload}
          disabled={!file || loading}
        >
          {loading ? (
            <span className="spinner-wrap">
              <span className="spinner" /> 업로드 중...
            </span>
          ) : '업로드'}
        </button>

      </div>
    </div>
  );
}
