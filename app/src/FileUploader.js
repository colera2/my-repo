// src/FileUploader.jsx
import React, { useState } from 'react';
import './FileUploader.css';

export default function FileUploader() {
  // 1) 타입 매개 변수 지우고 null로 초기화
  const [file, setFile] = useState(null);

  const handleUpload = async () => {
    if (!file) {
      alert('파일을 선택해주세요.');
      return;
    }

    // 2) 이제 filename 파라미터만 넘깁니다.
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
      // 3) TS 어노테이션 제거
      alert('업로드 중 오류: ' + e.message);
    }
  };

  return (
    <div className="uploader-container">
      <h1 className="uploader-title">📤 파일 업로드</h1>

      <div className="form-group">
        <label htmlFor="file-input">파일 선택</label>
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
    </div>
  );
}
