import React, { useState } from "react";

export default function FileUploader() {
  const [file, setFile] = useState(null);
  const [channelType, setChannelType] = useState("검색채널");
  const [fileDate, setFileDate] = useState("");

  const handleFileChange = e => {
    setFile(e.target.files[0]);
  };

  const handleUpload = async () => {
    if (!file || !fileDate) return alert("파일과 날짜를 선택해주세요.");
    // 1) 함수 엔드포인트 URL + 쿼리파라미터 조합
    const url = `http://localhost:7071/api/upload?` +
      `filename=${encodeURIComponent(file.name)}` +
      `&channel_type=${encodeURIComponent(channelType)}` +
      `&file_date=${encodeURIComponent(fileDate)}`;

    try {
      const res = await fetch(url, {
        method: "POST",
        headers: {
          "Content-Type": "application/octet-stream"
        },
        body: file
      });
      const text = await res.text();
      if (res.ok) alert("업로드 성공: " + text);
      else alert("업로드 실패: " + text);
    } catch (err) {
      console.error(err);
      alert("네트워크 오류");
    }
  };

  return (
    <div>
      <input type="file" onChange={handleFileChange} />
      <input
        type="date"
        value={fileDate}
        onChange={e => setFileDate(e.target.value)}
      />
      <select value={channelType} onChange={e => setChannelType(e.target.value)}>
        <option value="검색채널">검색채널</option>
        <option value="사용자정의채널">사용자정의채널</option>
      </select>
      <button onClick={handleUpload}>업로드</button>
    </div>
  );
}
