# 📊 ETF Exploratory Data Analysis (ETF EDA)

주요 ETF(Exchange Traded Fund)의 시세 데이터를 수집하고, 수익률·변동성·샤프 지수·MDD(최대 낙폭) 및 자산 간 상관관계를 시각화 및 분석하는 파이썬 기반 금융 탐색적 데이터 분석(EDA) 프로젝트입니다.

---

## 📁 디렉토리 구조 (Directory Structure)

```text
ETF_EDA/
├── dashboard/        # Streamlit / Web 기반 파이낸셜 대시보드
├── data/             # 로컬 저장 데이터셋 (.gitkeep 적용)
├── docs/             # 보고서 및 분석 문서
├── images/           # 그래프 및 시각화 이미지 캡처
├── src/              # 데이터 수집 및 분석 모듈
│   ├── __init__.py
│   ├── data_loader.py    # yfinance 데이터 로더
│   └── eda_analyzer.py   # 성과 지표 & 상관관계 분석기
├── .gitignore        # Git 추적 제외 항목 설정
├── main.py           # EDA 실습 및 메인 엔트리포인트
├── README.md         # 프로젝트 안내 문서
└── requirements.txt  # 필수 파이썬 라이브러리 목록
```

---

## 🚀 시작하기 (Getting Started)

### 1. 가상환경 세팅 (`uv` 사용)

본 프로젝트는 가상환경 패키지 관리자로 `uv` 사용을 권장합니다.

```bash
# 워크스페이스 루트에서 uv 가상환경 생성 (.venv)
uv venv .venv

# 가상환경 활성화 (Windows PowerShell)
.venv\Scripts\activate

# 필요 패키지 설치
uv pip install -r requirements.txt
```

### 2. 분석 실행 (Main Run)

```bash
python main.py
```

---

## 📤 GitHub에 올리는 방법 (How to Push to GitHub)

새로운 GitHub 레포지토리를 만드신 후, 아래 명령어를 실행하여 첫 커밋을 푸시하세요:

```bash
# 1. git 저장소 초기화
git init

# 2. 파일 스테이징 및 첫 커밋
git add .
git commit -m "feat: Initial commit for ETF EDA project"

# 3. 브랜치명을 main으로 변경
git branch -M main

# 4. GitHub 원격 저장소 연결
git remote add origin https://github.com/sunjinmo798-eng/ETF_EDA.git

# 5. GitHub로 푸시
git push -u origin main
```

---

## 🛠️ 기술 스택 (Tech Stack)

- **Language**: Python 3.10+
- **Environment**: uv
- **Data & Math**: Pandas, NumPy, yfinance
- **Visualization**: Matplotlib, Seaborn, Plotly
