import React, { useState } from 'react';
import './FileUploader.css';

export default function FileUploader() {
  const [file, setFile] = useState(null);

  const handleUpload = async () => {
    if (!file) {
      alert('파일을 선택해주세요.');
      return;
    }

    const url = `/api/upload?filename=${encodeURIComponent(file.name)}`;

    try {
      const resp = await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/octet-stream' },
        body: file
      });

      if (resp.ok) {
        alert('업로드 성공!');
        setFile(null);
      } else {
        const text = await resp.text();
        alert('업로드 실패: ' + text);
      }
    } catch (e) {
      alert('업로드 중 오류: ' + e.message);
    }
  };

  return (
    <div className="page-wrapper">
      {/* 박스 위 제목 */}
      <h1 className="page-title">마케팅 보고서 업로드</h1>

      <div className="uploader-container">
        {/* 박스 안 작은 제목 */}
        <p className="uploader-label">📥 파일 업로드</p>

        {/* 파일 선택 input — "파일 선택" 문구 없이 input만 */}
        <div className="form-group">
          <input
            id="file-input"
            type="file"
            accept=".xlsx,.csv"
            onChange={e => setFile(e.target.files?.[0] ?? null)}
          />
        </div>

        <button
          className="upload-button"
          onClick={handleUpload}
          disabled={!file}
        >
          업로드
        </button>

        {/* 지원 파일 안내 */}
        <div className="format-guide">
          <p className="format-title">지원 파일</p>
          <p className="format-item">
            <span className="format-platform">네이버 :</span>
            검색광고 보고서, 검색채널 보고서, 사용자 정의 채널 보고서, 키워드 보고서
          </p>
          <p className="format-item">
            <span className="format-platform">쿠팡 :</span>
            광고 보고서
          </p>
        </div>
      </div>
    </div>
  );
}
