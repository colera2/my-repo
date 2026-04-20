import os, re
import logging
import pandas as pd
import psycopg2
from psycopg2.extras import execute_values
import traceback

logger = logging.getLogger(__name__)

# =============================================================================
# DB 접속 정보
# - 보안을 위해 코드에 직접 입력하지 않고 환경변수로 작성
# - Azure Static Web Apps 에서 환경변수 값을 불러온다
# =============================================================================
DB_HOST     = os.environ.get("DB_HOST")
DB_USER     = os.environ.get("DB_USER")
DB_PASSWORD = os.environ.get("DB_PASSWORD")
DB_PORT     = int(os.environ.get("DB_PORT", 5432))
DB_NAME     = os.environ.get("DB_NAME")

# 필수 환경변수 누락 시 서버 시작 단계에서 즉시 에러 발생
_REQUIRED = {"DB_HOST": DB_HOST, "DB_USER": DB_USER,
             "DB_PASSWORD": DB_PASSWORD, "DB_NAME": DB_NAME}
_MISSING  = [k for k, v in _REQUIRED.items() if not v]
if _MISSING:
    raise EnvironmentError(f"필수 환경변수가 설정되지 않았습니다: {_MISSING}")

# =============================================================================
# 파일명 및 컬럼 정의
# - 각 파일별 DB에 저장할 컬럼 이름 목록
# - 네이버 엑셀 파일 (사용자정의채널, 검색채널) 파일명 패턴 정의
# =============================================================================

# 네이버 사용자정의채널 엑셀 파일의 컬럼 순서
CUSTOM_ORDER_COLUMNS = [
    "yymmdd","device","nt_source","nt_medium","nt_detail","nt_keyword",
    "customer_cnt","inflow_cnt","page_cnt","page_inflow_cnt","order_cnt",
    "order_inflow_per","order_price","order_inflow_price","contribute_cnt",
    "contribute_inflow_per","contribute_price","contribute_inflow_price"
]

# 쿠팡 PA 키워드 엑셀 파일의 컬럼 순서 (44개 + reg_date + account = 46개)
TARGET_COLUMNS_PA_DAILY = [
    "A","B","sales_type","ad_type","campaign_id","campaign","ad_group",
    "product1","product1_id","product2","product2_id","adspace","keyword","non_ad",
    "impressions","clicks","adcost","clickrate","order_cnt","R","S","out_qty",
    "U","V","gross","X","Y","Z","AA","AB","AC","AD","AE","AF","AG","AH",
    "AI","AJ","AK","AL","AM","AN","AO","AP","reg_date","account"
]

# 네이버 채널 엑셀 파일명 패턴: "사용자정의채널_2025-01-01_2025-01-31.xlsx"
EXCEL_FILENAME_RE = re.compile(r'^(사용자정의채널|검색채널)_(\d{4}-\d{2}-\d{2})_\d{4}-\d{2}-\d{2}$')


# =============================================================================
# DB 연결
# =============================================================================
def get_db_connection():
    """
    환경변수에 등록된 접속 정보로 PostgreSQL DB에 연결합니다.
    연결 실패 시 에러를 위로 전달해 업로드 요청이 500 에러를 반환하게 합니다.
    """
    try:
        return psycopg2.connect(
            host=DB_HOST, port=DB_PORT,
            dbname=DB_NAME, user=DB_USER,
            password=DB_PASSWORD
        )
    except Exception as e:
        logger.error("DB 연결 오류: %s", e)
        traceback.print_exc()
        raise


# =============================================================================
# 공통 INSERT 함수
# =============================================================================
def insert_dataframe(conn, df, table_name, columns):
    """
    DataFrame을 받아 지정한 테이블에 INSERT합니다.
    - 이미 동일한 데이터가 있으면 건너뜁니다 (ON CONFLICT DO NOTHING)
    - INSERT 실패 시 롤백 후 에러를 위로 전달합니다
    """
    try:
        df2 = df[columns]
        data = [tuple(r) for r in df2.to_numpy()]
        cols_sql = ','.join(f'"{c}"' for c in columns)
        sql = f'INSERT INTO "{table_name}" ({cols_sql}) VALUES %s ON CONFLICT DO NOTHING;'
        with conn.cursor() as cur:
            execute_values(cur, sql, data)
        conn.commit()
    except Exception as e:
        conn.rollback()
        logger.error("%s 삽입 오류: %s", table_name, e)
        traceback.print_exc()
        raise


# =============================================================================
# 헬퍼 함수
# =============================================================================
def generate_excel_columns(n):
    """
    n개의 엑셀식 컬럼명을 생성합니다.
    예) n=3 → ["A", "B", "C"] / n=28 → ["A", ..., "AB"]
    헤더 없는 파일을 읽을 때 컬럼명으로 사용합니다.
    """
    cols = []
    for i in range(n):
        s = ""
        tmp = i
        while True:
            s = chr(tmp % 26 + 65) + s
            tmp = tmp // 26 - 1
            if tmp < 0: break
        cols.append(s)
    return cols


# =============================================================================
# 파일 종류별 처리 함수
# - 파일 읽기 → 컬럼 수 검증(잘못된 파일이면 즉시 에러) → 가공 → DB 저장
# =============================================================================

def process_excel_file(conn, file_path, channel_type):
    """
    네이버 채널 엑셀 파일을 처리합니다.
    - 사용자정의채널 → Naver_Custom_Order 테이블
    - 검색채널       → Naver_Search_Channel 테이블

    파일명에서 날짜를 추출해 yymmdd 컬럼으로 저장합니다.
    파일명 패턴이 맞지 않으면 즉시 에러를 발생시킵니다.
    """
    fname = os.path.splitext(os.path.basename(file_path))[0]
    m = EXCEL_FILENAME_RE.match(fname)
    if not m:
        raise ValueError(f"파일명 패턴 불일치: {fname}")

    _, file_date = m.groups()  # 예) "2025-01-01"
    df = pd.read_excel(file_path, header=None, skiprows=1)  # 1행(헤더) 제외하고 읽기

    if channel_type == "사용자정의채널":
        base = CUSTOM_ORDER_COLUMNS[1:]        # yymmdd 제외한 나머지 컬럼
        sub = df.iloc[:, :len(base)].copy()
        sub.columns = base
        sub.insert(0, "yymmdd", file_date)     # 맨 앞에 날짜 컬럼 추가
        table = "Naver_Custom_Order"
        cols  = CUSTOM_ORDER_COLUMNS

    else:  # 검색채널
        cols16 = generate_excel_columns(16)    # A~P 컬럼명 생성
        sub = df.iloc[:, :16].copy()
        sub.columns = cols16
        sub.insert(0, "yymmdd", file_date)     # 맨 앞에 날짜 컬럼 추가
        table = "Naver_Search_Channel"
        cols  = ["yymmdd"] + cols16

    insert_dataframe(conn, sub, table, cols)


def process_pa_daily_keyword(conn, file_path, account):
    """
    쿠팡 PA 키워드 엑셀 파일을 처리해 ad_coupang 테이블에 저장합니다.
    - 파일은 반드시 44개 컬럼이어야 합니다 (다르면 즉시 에러)
    - 날짜 컬럼(A열)을 YYYY-MM-DD 형식으로 변환합니다
    - 비율 컬럼(AJ~AO)의 % 기호를 제거하고 숫자로 변환합니다
    - account는 파일명에서 추출한 계정명입니다
    """
    df = pd.read_excel(file_path, header=None, skiprows=1)

    if df.shape[1] != 44:
        raise ValueError(
            f"컬럼 개수 오류: {df.shape[1]}개 (44개여야 함) — 파일: {file_path}"
        )

    df.columns = generate_excel_columns(44)

    # 13번째 위치에 non_ad 컬럼 삽입 (원본 파일에 없는 컬럼)
    df.insert(13, "non_ad", None)

    # A열(날짜, 예: "20250101") → "2025-01-01" 형식으로 변환 후 reg_date 컬럼으로 저장
    df.iloc[:, 44] = df["A"].astype(str).apply(
        lambda x: f"{x[:4]}-{x[4:6]}-{x[6:]}" if len(x) >= 8 else None
    )
    df.columns.values[44] = "reg_date"
    df["account"] = account

    # 비율(%) 컬럼에서 % 기호 제거 후 숫자로 변환
    for col in ["AJ", "AK", "AL", "AM", "AN", "AO"]:
        if col in df:
            df[col] = pd.to_numeric(
                df[col].astype(str).str.replace("%", ""), errors="coerce"
            )

    df.columns = TARGET_COLUMNS_PA_DAILY
    insert_dataframe(conn, df, "ad_coupang", TARGET_COLUMNS_PA_DAILY)


def process_csv_ad_naver(conn, file_path, sub_account):
    """
    네이버 검색광고 CSV 파일을 처리해 ad_naver 테이블에 저장합니다.
    - 상위 2행(설명 행)을 건너뛰고 읽습니다
    - 28개 컬럼이 필요합니다 (부족하면 즉시 에러)
    - A열(날짜)을 YYYY-MM-DD 형식으로 변환합니다
    - 숫자 컬럼의 쉼표(,)를 제거하고 숫자로 변환합니다
    - sub_account는 파일명에서 추출한 하위 계정명입니다
    """
    expected = generate_excel_columns(28)
    df = pd.read_csv(file_path, skiprows=2, header=None)

    if df.shape[1] < 28:
        raise ValueError(
            f"컬럼 개수 오류: {df.shape[1]}개 (28개 이상이어야 함) — 파일: {file_path}"
        )

    df = df.iloc[:, :28]
    df.columns = expected
    df["reg_date"] = df["A"].astype(str).str.replace(".", "-", regex=False).str[:10]
    df["id"] = sub_account

    # 쉼표 제거 후 숫자로 변환
    for c in set(expected[11:]) | {"AA", "AB"}:
        if c in df:
            df[c] = pd.to_numeric(
                df[c].astype(str).str.replace(",", ""), errors="coerce"
            )

    insert_dataframe(conn, df, "ad_naver", expected + ["reg_date", "id"])


def process_csv_ad_naver_keyword(conn, file_path, sub_account):
    """
    네이버 키워드보고서 CSV 파일을 처리해 ad_naver_keyword2 테이블에 저장합니다.
    - 상위 2행(설명 행)을 건너뛰고 읽습니다
    - 9개 컬럼이 필요합니다 (부족하면 즉시 에러)
    - 날짜를 YYYY-MM-DD 형식으로 변환합니다
    - 수치 컬럼의 쉼표(,)를 제거하고 숫자로 변환합니다
    - sub_account는 파일명에서 추출한 하위 계정명입니다
    """
    cols = ["order_date", "campaign", "ad_group", "keyword",
            "imp_cnt", "click_cnt", "order_cnt", "cost", "order_price"]
    df = pd.read_csv(file_path, skiprows=2, header=None)

    if df.shape[1] < len(cols):
        raise ValueError(
            f"컬럼 개수 오류: {df.shape[1]}개 ({len(cols)}개 이상이어야 함) — 파일: {file_path}"
        )

    df = df.iloc[:, :len(cols)]
    df.columns = cols
    df["yymmdd"]  = df["order_date"].astype(str).str.replace(".", "-", regex=False).str[:10]
    df["account"] = sub_account

    # 쉼표 제거 후 숫자로 변환
    for c in ["imp_cnt", "click_cnt", "order_cnt", "cost", "order_price"]:
        df[c] = pd.to_numeric(
            df[c].astype(str).str.replace(",", ""), errors="coerce"
        )

    insert_dataframe(conn, df, "ad_naver_keyword2", cols + ["yymmdd", "account"])
