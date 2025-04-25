import os
import logging
import azure.functions as func

from db_upload import (
    get_db_connection,
    process_excel_file,
    process_pa_daily_keyword,
    process_csv_ad_naver,
    process_csv_ad_naver_keyword
)

app = func.FunctionApp()

@app.route(route="upload", auth_level=func.AuthLevel.ANONYMOUS)
def upload(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("File upload endpoint called.")

    # 1) 바이너리 읽기 (한 번만)
    body = req.get_body()

    # 2) 필수 파라미터: filename
    filename = req.params.get('filename')
    if not filename:
        return func.HttpResponse("filename 파라미터는 필수입니다.", status_code=400)

    # 3) 파일명으로 타입/채널 자동 판별
    if "_pa_daily_keyword_" in filename:
        file_type = "pa_daily_keyword"
        account   = filename.split("_pa_daily_keyword_")[0]

    elif filename.startswith("검색채널_") or filename.startswith("사용자정의채널_"):
        file_type    = "excel_channel"
        channel_type = "검색채널" if filename.startswith("검색채널_") else "사용자정의채널"

    elif filename.startswith("검색광고_"):
        file_type    = "csv_ad_naver"
        sub_account  = filename.split("_")[1]

    elif filename.startswith("키워드보고서_"):
        file_type    = "csv_ad_naver_keyword"
        sub_account  = filename.split("_")[1]

    else:
        return func.HttpResponse("지원하지 않는 파일명 형식입니다.", status_code=400)

    # 4) 임시 저장
    tmp = os.path.join(os.environ.get("TEMP", "/tmp"), filename)
    with open(tmp, "wb") as f:
        f.write(body)

    conn = get_db_connection()
    try:
        # 5) 타입별 처리 함수 호출
        if file_type == "pa_daily_keyword":
            process_pa_daily_keyword(conn, tmp, account)

        elif file_type == "excel_channel":
            process_excel_file(conn, tmp, channel_type)

        elif file_type == "csv_ad_naver":
            process_csv_ad_naver(conn, tmp, sub_account)

        elif file_type == "csv_ad_naver_keyword":
            process_csv_ad_naver_keyword(conn, tmp, sub_account)

        return func.HttpResponse("파일이 성공적으로 처리되었습니다.", status_code=200)

    except Exception as e:
        logging.error(f"업로드 처리 중 오류: {e}")
        return func.HttpResponse(f"오류 발생: {e}", status_code=500)

    finally:
        conn.close()
        try:
            os.remove(tmp)
        except OSError:
            pass
