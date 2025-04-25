import os, re
import pandas as pd
import psycopg2
from psycopg2.extras import execute_values
import traceback

# ── DB 접속 정보 ──
DB_HOST     = "db1-dev.postgres.database.azure.com"
DB_USER     = "dev"
DB_PASSWORD = "@Vkdlxhdnpdl0"
DB_PORT     = 5432
DB_NAME     = "dainDB"

# ── 사용자정의채널 전용 컬럼 정의 ──
CUSTOM_ORDER_COLUMNS = [
    "yymmdd","device","nt_source","nt_medium","nt_detail","nt_keyword",
    "customer_cnt","inflow_cnt","page_cnt","page_inflow_cnt","order_cnt",
    "order_inflow_per","order_price","order_inflow_price","contribute_cnt",
    "contribute_inflow_per","contribute_price","contribute_inflow_price"
]

# ── pa_daily_keyword 전용 컬럼 정의 ──
TARGET_COLUMNS_PA_DAILY = [
    "A","B","sales_type","ad_type","campaign_id","campaign","ad_group",
    "product1","product1_id","product2","product2_id","adspace","keyword","non_ad",
    "impressions","clicks","adcost","clickrate","order_cnt","R","S","out_qty",
    "U","V","gross","X","Y","Z","AA","AB","AC","AD","AE","AF","AG","AH",
    "AI","AJ","AK","AL","AM","AN","AO","AP","reg_date","account"
]

EXCEL_FILENAME_RE = re.compile(r'^(사용자정의채널|검색채널)_(\d{4}-\d{2}-\d{2})_\d{4}-\d{2}-\d{2}$')

# ── 디버깅 헬퍼 ──
def debug_print_columns(df, file_path, label=""):
    print(f"DEBUG ({label}): {file_path} -> columns={df.shape[1]}")
    print("   ", df.columns.tolist())

# ── DB 연결 헬퍼 ──
def get_db_connection():
    try:
        return psycopg2.connect(
            host=DB_HOST, port=DB_PORT,
            dbname=DB_NAME, user=DB_USER,
            password=DB_PASSWORD
        )
    except Exception as e:
        print("DB 연결 오류:", e)
        traceback.print_exc()
        raise

# ── 공통 INSERT 함수 ──
def insert_dataframe(conn, df, table_name, columns):
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
        print(f"{table_name} 삽입 오류:", e)
        traceback.print_exc()
        raise

# ── A,B,C... 컬럼명 생성 헬퍼 ──
def generate_excel_columns(n):
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

# ── 엑셀 기반 채널 처리 ──
import os, re
import pandas as pd

# 파일명 패턴: "사용자정의채널_YYYY-MM-DD_YYYY-MM-DD.xlsx"
EXCEL_FILENAME_RE = re.compile(r'^(사용자정의채널|검색채널)_(\d{4}-\d{2}-\d{2})_\d{4}-\d{2}-\d{2}$')

def process_excel_file(conn, file_path, channel_type):
    # ── 1) file_date를 파일명에서 추출 ──
    fname = os.path.splitext(os.path.basename(file_path))[0]
    m = EXCEL_FILENAME_RE.match(fname)
    if not m:
        raise ValueError(f"파일명 패턴 불일치: {fname}")
    _, file_date = m.groups()  # ex: "2025-04-07"

    # ── 2) 데이터 읽기 ──
    df = pd.read_excel(file_path, header=None, skiprows=1)

    # ── 3) 실제 채널별 컬럼만 슬라이스, 이름 붙이기 ──
    if channel_type == "사용자정의채널":
        base = CUSTOM_ORDER_COLUMNS[1:]   # ['device', 'nt_source', …]
        sub = df.iloc[:, :len(base)].copy()
        sub.columns = base
        # (필요한 수치 변환 로직 모두 여기에…)

        # ── 4) 맨 앞에 file_date 삽입 ──
        sub.insert(0, "yymmdd", file_date)

        table = "Naver_Custom_Order"
        cols  = CUSTOM_ORDER_COLUMNS

    else:  # 검색채널
        cols16 = generate_excel_columns(16)  # ["A","B",…,"P"]
        sub = df.iloc[:, :16].copy()
        sub.columns = cols16
        sub.insert(0, "yymmdd", file_date)

        table = "Naver_Search_Channel"
        cols  = ["yymmdd"] + cols16

    # ── 5) 삽입 ──
    insert_dataframe(conn, sub, table, cols)




# ── pa_daily_keyword 처리 ──
def process_pa_daily_keyword(conn, file_path, account):
    df = pd.read_excel(file_path, header=None, skiprows=1)
    debug_print_columns(df, file_path, "Original")
    if df.shape[1] != 44:
        print(f"ERROR: 컬럼개수 {df.shape[1]} != 44")
        return

    df.columns = generate_excel_columns(44)
    df.insert(13, "non_ad", None)
    df.iloc[:,44] = df["A"].astype(str).apply(
        lambda x: f"{x[:4]}-{x[4:6]}-{x[6:]}" if len(x)>=8 else None
    )
    df.columns.values[44] = "reg_date"
    df["account"] = account

    for col in ["AJ","AK","AL","AM","AN","AO"]:
        if col in df:
            df[col] = pd.to_numeric(
                df[col].astype(str).str.replace("%",""), errors="coerce"
            )

    df.columns = TARGET_COLUMNS_PA_DAILY
    insert_dataframe(conn, df, "ad_coupang", TARGET_COLUMNS_PA_DAILY)

# ── CSV 처리: 검색광고 ──
def process_csv_ad_naver(conn, file_path, sub_account):
    expected = generate_excel_columns(28)
    df = pd.read_csv(file_path, skiprows=2, header=None)
    debug_print_columns(df, file_path, "Original")
    df = df.iloc[:,:28]; df.columns = expected
    df["reg_date"] = df["A"].astype(str).str.replace(".", "-", regex=False).str[:10]
    df["id"] = sub_account
    for c in set(expected[11:])|{"AA","AB"}:
        if c in df:
            df[c] = pd.to_numeric(
                df[c].astype(str).str.replace(",",""), errors="coerce"
            )
    insert_dataframe(conn, df, "ad_naver", expected + ["reg_date","id"])

# ── CSV 처리: 키워드보고서 ──
def process_csv_ad_naver_keyword(conn, file_path, sub_account):
    cols = ["order_date","campaign","ad_group","keyword",
            "imp_cnt","click_cnt","order_cnt","cost","order_price"]
    df = pd.read_csv(file_path, skiprows=2, header=None)
    debug_print_columns(df, file_path, "Original")
    df = df.iloc[:,:len(cols)]; df.columns = cols
    df["yymmdd"]  = df["order_date"].astype(str).str.replace(".", "-", regex=False).str[:10]
    df["account"] = sub_account
    for c in ["imp_cnt","click_cnt","order_cnt","cost","order_price"]:
        df[c] = pd.to_numeric(
            df[c].astype(str).str.replace(",",""), errors="coerce"
        )
    insert_dataframe(conn, df, "ad_naver_keyword2", cols + ["yymmdd","account"])
