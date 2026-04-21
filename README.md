## 마케팅 성과 보고서 업로드 웹사이트

네이버·쿠팡 마케팅 성과 보고서 파일을 웹사이트에 업로드하면, 자동으로 내부 데이터베이스에 저장해주는 시스템입니다.  
매일 수기로 데이터를 가공하던 반복 작업을 자동화하여 업무 시간을 줄여줍니다.

---

#### 💡 주요 기능

- 마케팅 성과 보고서 파일(`.xlsx`, `.csv`) 웹 업로드
- **파일명 기반 자동 판별** — 파일명만 보고 보고서 종류를 자동으로 구분하여 처리
- 처리된 데이터를 PostgreSQL 데이터베이스에 자동 저장
- GitHub Actions를 통한 Azure 자동 배포 (코드 수정 → 즉시 반영)

---

#### 📁 지원 파일 형식

| 파일명 패턴 | 광고 종류 | 저장 테이블 |
|---|---|---|
| `XXX_pa_daily_keyword_XXX.xlsx` | 쿠팡 PA 키워드 보고서 | `ad_coupang` |
| `검색채널_YYYY-MM-DD_YYYY-MM-DD.xlsx` | 네이버 검색채널 | `Naver_Search_Channel` |
| `사용자정의채널_YYYY-MM-DD_YYYY-MM-DD.xlsx` | 네이버 사용자정의채널 | `Naver_Custom_Order` |
| `검색광고_계정명_XXX.csv` | 네이버 검색광고 | `ad_naver` |
| `키워드보고서_계정명_XXX.csv` | 네이버 키워드 보고서 | `ad_naver_keyword2` |

---

#### 🗂️ 프로젝트 구조

```
my-repo/
├── app/                          # 프론트엔드 (React 웹사이트)
│   ├── public/
│   │   └── index.html            # HTML 진입점
│   └── src/
│       ├── App.js                # 최상위 컴포넌트
│       ├── FileUploader.js       # 파일 업로드 UI 핵심 컴포넌트
│       ├── FileUploader.css      # 업로더 스타일
│       ├── index.js              # React 앱 시작점
│       └── index.css             # 전역 스타일
│
├── api/                          # 백엔드 (Azure Functions / Python)
│   ├── function_app.py           # API 엔드포인트 — 파일 수신 및 종류 판별
│   ├── db_upload.py              # 파일 파싱 및 DB 저장 로직
│   ├── requirements.txt          # Python 패키지 목록
│   └── host.json                 # Azure Functions 설정
│
├── .github/workflows/
│   └── azure-static-web-apps-*.yml  # GitHub Actions 자동 배포 설정
│
├── staticwebapp.config.json      # Azure Static Web Apps 설정
└── .gitignore                    # Git 제외 파일 목록
```

---

#### 🛠️ 기술 스택

| 구분 | 기술 |
|------|------|
| 프론트엔드 | React 19, JavaScript, CSS |
| 백엔드 | Python 3.11, Azure Functions |
| 데이터베이스 | PostgreSQL (Azure Database for PostgreSQL) |
| 배포 | Microsoft Azure Static Web Apps |
| CI/CD | GitHub Actions |
| 주요 라이브러리 | pandas, psycopg2-binary, openpyxl |

---

#### ⚙️ 로컬 실행 방법

##### 0. 사전 준비

- Python 3.11 이상
- Node.js 18 이상
- Azure Functions Core Tools

##### 1. 프론트엔드 실행

```bash
cd app
npm install
npm start
```
브라우저에서 `http://localhost:3000` 접속

##### 2. 백엔드 실행

```bash
cd api
pip install -r requirements.txt
func start
```

---

#### ☁️ 배포 방법

`main` 브랜치에 코드를 push하면 GitHub Actions가 자동으로 Azure에 배포합니다.  
별도 수동 배포 작업이 필요하지 않습니다.

##### 배포 흐름

```
코드 수정 → main 브랜치에 push
    ↓
GitHub Actions 실행
    ↓
Python 패키지 설치 → React 빌드 → Azure 배포
    ↓
웹사이트 자동 업데이트 완료
```

---

#### 🔒 환경 변수 설정

DB 접속 정보 등 민감한 정보는 환경 변수로 관리 합니다.

Azure Static Web Apps의 [환경 변수] 에서 DB 관련 정보를 설정하세요.

```
    "DB_HOST": "your-db-host.postgres.database.azure.com",
    "DB_USER": "your-db-user",
    "DB_PASSWORD": "your-db-password",
    "DB_NAME": "your-db-name",
    "DB_PORT": "5432"
```

