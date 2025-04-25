import azure.functions as func
import logging
import os
from db_upload import get_db_connection, process_excel_file

app = func.FunctionApp()

@app.route(route="upload", auth_level=func.AuthLevel.ANONYMOUS)
def upload(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("File upload endpoint called.")

    try:
        # 1. 파일 데이터 읽기
        file_bytes = req.get_body()
        
        # 2. URL 파라미터에서 메타 정보 받기
        filename = req.params.get('filename')
        channel_type = req.params.get('channel_type')
        file_date = req.params.get('file_date')
        
        if not filename or not file_date:
            return func.HttpResponse("filename와 file_date 파라미터는 필수입니다.", status_code=400)
        
        # 3. 임시 폴더에 파일 저장
        temp_dir = os.environ.get("TEMP", "/tmp")
        temp_file_path = os.path.join(temp_dir, filename)
        with open(temp_file_path, "wb") as f:
            f.write(file_bytes)
        
        # 4. DB 업로드 실행
        conn = get_db_connection()
        if filename.lower().endswith(".xlsx"):
            process_excel_file(conn, temp_file_path, channel_type, file_date)
        else:
            return func.HttpResponse("지원하지 않는 파일 확장자입니다.", status_code=400)
        
        conn.close()
        os.remove(temp_file_path)
        
        return func.HttpResponse("파일이 성공적으로 처리되었습니다.", status_code=200)
    except Exception as e:
        logging.error(f"파일 업로드 처리 중 오류 발생: {str(e)}")
        return func.HttpResponse(f"오류 발생: {str(e)}", status_code=500)
