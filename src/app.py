"""
실시간 네이버 금융 ETF 종합 EDA 대시보드
=========================================
이 애플리케이션은 네이버 금융 API에서 제공하는 실시간 ETF 데이터를 수집하여
시가총액, 거래대금, 3개월 수익률, NAV 괴리율 등 다양한 금융 차원에서의
탐색적 데이터 분석(EDA) 및 대시보드 시각화를 제공합니다.
"""

from typing import Tuple
from datetime import datetime
import json
import re
import requests
import numpy as np
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

# -----------------------------------------------------------------------------
# 설정 및 상수 정의
# -----------------------------------------------------------------------------
# 사용자가 제공한 exact URL (JSONP 콜백 파라미터 포함)
NAVER_ETF_API_URL: str = (
    "https://finance.naver.com/api/sise/etfItemList.nhn?etfType=0&targetColumn=market_sum&sortOrder=desc&_callback=window.__jindo2_callback._7957"
)

TAB_CODE_MAP: dict[int, str] = {
    1: "국내 시장지수",
    2: "국내 업종/테마",
    3: "국내 파생",
    4: "해외 주식",
    5: "원자재",
    6: "채권",
    7: "기타"
}

# Streamlit 페이지 기본 설정
st.set_page_config(
    page_title="실시간 ETF 종합 EDA 대시보드",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# -----------------------------------------------------------------------------
# 커스텀 CSS 스타일 적용 (모던 다크/글래스 스타일)
# -----------------------------------------------------------------------------
st.markdown(
    """
    <style>
    .stApp {
        background-color: #0e1117;
        color: #e0e6ed;
    }
    .metric-card {
        background: linear-gradient(135deg, rgba(30, 41, 59, 0.7), rgba(15, 23, 42, 0.8));
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 12px;
        padding: 18px 22px;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.25);
        backdrop-filter: blur(10px);
        margin-bottom: 12px;
    }
    .metric-title {
        font-size: 0.85rem;
        color: #94a3b8;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .metric-value {
        font-size: 1.75rem;
        font-weight: 700;
        color: #f8fafc;
        margin-top: 4px;
    }
    .metric-sub {
        font-size: 0.8rem;
        color: #38bdf8;
        margin-top: 4px;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: rgba(15, 23, 42, 0.6);
        padding: 6px;
        border-radius: 10px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 44px;
        border-radius: 8px;
        color: #94a3b8;
        font-weight: 600;
    }
    .stTabs [aria-selected="true"] {
        background-color: #2563eb !important;
        color: #ffffff !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# -----------------------------------------------------------------------------
# JSONP 처리 함수
# -----------------------------------------------------------------------------
def extract_json_from_jsonp(text: str) -> dict:
    """JSONP 응답 문자열에서 콜백 함수 래퍼를 제거하고 순수 JSON 객체를 파싱합니다.

    Args:
        text (str): API 응답 문자열 (예: window.__jindo2_callback._7957({...}))

    Returns:
        dict: 파싱된 JSON 데이터 dictionary
    """
    text = text.strip()
    # JSONP 콜백 패턴 정규식 검색
    match = re.search(r"^\s*[\w\.]+\s*\((.*)\)\s*;?\s*$", text, re.DOTALL)
    if match:
        json_str = match.group(1)
    else:
        json_str = text
    return json.loads(json_str)

# -----------------------------------------------------------------------------
# 데이터 수집 및 전처리 함수
# -----------------------------------------------------------------------------
@st.cache_data(ttl=60, show_spinner=False)
def fetch_etf_data(api_url: str = NAVER_ETF_API_URL) -> Tuple[pd.DataFrame, datetime]:
    """네이버 금융 API를 호출하여 JSONP 및 JSON 응답을 자동 전처리 후 DataFrame으로 반환합니다.

    Args:
        api_url (str): 네이버 금융 ETF API URL (기본값: 사용자 지정 exact URL)

    Returns:
        Tuple[pd.DataFrame, datetime]: 가공된 ETF DataFrame 및 수집 시각
    """
    headers: dict[str, str] = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
    }
    try:
        response = requests.get(api_url, headers=headers, timeout=10)
        response.raise_for_status()
        
        # 인코딩 설정 (EUC-KR 또는 UTF-8 자동 대응)
        if response.encoding is None or response.encoding.lower() == 'iso-8859-1':
            response.encoding = 'euc-kr'
            
        json_data = extract_json_from_jsonp(response.text)
        raw_list = json_data.get("result", {}).get("etfItemList", [])
        df = pd.DataFrame(raw_list)
    except Exception as exc:
        st.error(f"데이터 수집 및 파싱 실패: {exc}")
        return pd.DataFrame(), datetime.now()

    if df.empty:
        return df, datetime.now()

    # 데이터 수치형 변환 및 필드 파생
    df["etfTabName"] = df["etfTabCode"].map(TAB_CODE_MAP).fillna("기타")
    
    numeric_cols: list[str] = [
        "nowVal", "changeVal", "changeRate", "nav",
        "threeMonthEarnRate", "quant", "amonut", "marketSum"
    ]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # 괴리율 (NAV 대비 현재가 비율 %) 및 괴리금액 생성
    df["disparateRate"] = np.where(
        (df["nav"].notnull()) & (df["nav"] > 0),
        ((df["nowVal"] - df["nav"]) / df["nav"]) * 100,
        np.nan
    )
    df["disparateVal"] = df["nowVal"] - df["nav"]

    return df, datetime.now()

# -----------------------------------------------------------------------------
# 메인 대시보드 로직
# -----------------------------------------------------------------------------
def main() -> None:
    """Streamlit 메인 대시보드 애플리케이션 실행 함수"""
    
    # 1. 헤더 영역
    col_h1, col_h2 = st.columns([3, 1])
    with col_h1:
        st.title("📈 실시간 Naver ETF 종합 EDA 대시보드")
        st.caption(f"연동 API: `{NAVER_ETF_API_URL[:65]}...` (JSONP 콜백 처리 완료)")
    
    with col_h2:
        st.write("")
        if st.button("🔄 실시간 데이터 새로고침", use_container_width=True):
            st.cache_data.clear()
            st.rerun()

    # 2. 데이터 가져오기
    with st.spinner("실시간 ETF API 데이터를 파싱하는 중입니다..."):
        df_raw, fetch_time = fetch_etf_data(NAVER_ETF_API_URL)

    if df_raw.empty:
        st.warning("수집된 ETF 데이터가 없습니다. 잠시 후 다시 시도해 주세요.")
        return

    # 3. 사이드바 필터링 컨트롤러
    st.sidebar.header("🔍 ETF 탐색 필터")
    
    all_categories: list[str] = sorted(df_raw["etfTabName"].unique().tolist())
    selected_categories = st.sidebar.multiselect(
        "ETF 카테고리 선택",
        options=all_categories,
        default=all_categories
    )

    search_keyword = st.sidebar.text_input("종목명 / 종목코드 검색", "").strip()

    min_ms, max_ms = int(df_raw["marketSum"].min()), int(df_raw["marketSum"].max())
    selected_ms = st.sidebar.slider(
        "시가총액 범위 (억원)",
        min_value=min_ms,
        max_value=max_ms,
        value=(min_ms, max_ms)
    )

    min_amt, max_amt = int(df_raw["amonut"].min()), int(df_raw["amonut"].max())
    selected_amt = st.sidebar.slider(
        "거래대금 범위 (백만원)",
        min_value=min_amt,
        max_value=max_amt,
        value=(min_amt, max_amt)
    )

    min_earn = float(df_raw["threeMonthEarnRate"].dropna().min())
    max_earn = float(df_raw["threeMonthEarnRate"].dropna().max())
    selected_earn = st.sidebar.slider(
        "3개월 수익률 범위 (%)",
        min_value=min_earn,
        max_value=max_earn,
        value=(min_earn, max_earn)
    )

    df_filtered = df_raw[
        (df_raw["etfTabName"].isin(selected_categories)) &
        (df_raw["marketSum"] >= selected_ms[0]) &
        (df_raw["marketSum"] <= selected_ms[1]) &
        (df_raw["amonut"] >= selected_amt[0]) &
        (df_raw["amonut"] <= selected_amt[1]) &
        (df_raw["threeMonthEarnRate"] >= selected_earn[0]) &
        (df_raw["threeMonthEarnRate"] <= selected_earn[1])
    ]

    if search_keyword:
        df_filtered = df_filtered[
            df_filtered["itemname"].str.contains(search_keyword, case=False, na=False) |
            df_filtered["itemcode"].str.contains(search_keyword, case=False, na=False)
        ]

    # 4. 주요 KPI 메트릭 카드
    st.markdown("---")
    kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)

    total_count = len(df_filtered)
    total_market_sum = df_filtered["marketSum"].sum()
    total_amount = df_filtered["amonut"].sum()
    avg_three_month = df_filtered["threeMonthEarnRate"].mean()
    avg_disparate = df_filtered["disparateRate"].abs().mean()

    with kpi1:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-title">선택된 ETF 개수</div>
                <div class="metric-value">{total_count:,} 개</div>
                <div class="metric-sub">전체 {len(df_raw):,} 개 중</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with kpi2:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-title">총 시가총액 합계</div>
                <div class="metric-value">{total_market_sum / 10000:,.1f} 조원</div>
                <div class="metric-sub">{total_market_sum:,.0f} 억원</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with kpi3:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-title">총 거래대금 합계</div>
                <div class="metric-value">{total_amount / 100:,.1f} 억원</div>
                <div class="metric-sub">{total_amount:,.0f} 백만원</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with kpi4:
        earn_color = "#f43f5e" if avg_three_month < 0 else "#10b981"
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-title">평균 3개월 수익률</div>
                <div class="metric-value" style="color: {earn_color};">{avg_three_month:+.2f}%</div>
                <div class="metric-sub">필터 적용 평균값</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with kpi5:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-title">평균 절대 괴리율</div>
                <div class="metric-value">{avg_disparate:.2f}%</div>
                <div class="metric-sub">수집 시각: {fetch_time.strftime('%H:%M:%S')}</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    st.markdown("---")

    # 5. EDA 탐색 탭 구성
    tab1, tab2, tab3, tab4 = st.tabs([
        "📊 시장 개요 & 분포 EDA",
        "📈 수익률 & 상관관계 EDA",
        "🔍 종목 탐색기 & 괴리율 분석",
        "📋 기술통계량 및 데이터 리포트"
    ])

    # -------------------------------------------------------------------------
    # TAB 1: 시장 개요 & 분포 EDA
    # -------------------------------------------------------------------------
    with tab1:
        st.subheader("📌 ETF 시장 구조 및 분포 분석")
        row1_col1, row1_col2 = st.columns(2)
        
        with row1_col1:
            st.markdown("#### 🏆 시가총액 Top 15 ETF")
            top_market_sum = df_filtered.nlargest(15, "marketSum")
            fig_ms = px.bar(
                top_market_sum,
                x="marketSum",
                y="itemname",
                orientation="h",
                color="etfTabName",
                text="marketSum",
                labels={"marketSum": "시가총액 (억원)", "itemname": "ETF 종목명", "etfTabName": "카테고리"},
                color_discrete_sequence=px.colors.qualitative.Bold
            )
            fig_ms.update_layout(
                yaxis={"categoryorder": "total ascending"},
                template="plotly_dark",
                height=450,
                margin=dict(l=20, r=20, t=30, b=20)
            )
            fig_ms.update_traces(texttemplate="%{text:,.0f}억", textposition="outside")
            st.plotly_chart(fig_ms, use_container_width=True)

        with row1_col2:
            st.markdown("#### 💰 거래대금 Top 15 ETF")
            top_amount = df_filtered.nlargest(15, "amonut")
            fig_amt = px.bar(
                top_amount,
                x="amonut",
                y="itemname",
                orientation="h",
                color="etfTabName",
                text="amonut",
                labels={"amonut": "거래대금 (백만원)", "itemname": "ETF 종목명", "etfTabName": "카테고리"},
                color_discrete_sequence=px.colors.qualitative.Vivid
            )
            fig_amt.update_layout(
                yaxis={"categoryorder": "total ascending"},
                template="plotly_dark",
                height=450,
                margin=dict(l=20, r=20, t=30, b=20)
            )
            fig_amt.update_traces(texttemplate="%{text:,.0f}백만", textposition="outside")
            st.plotly_chart(fig_amt, use_container_width=True)

        row2_col1, row2_col2 = st.columns(2)

        with row2_col1:
            st.markdown("#### 🍕 카테고리별 시가총액 비중")
            cat_summary = (
                df_filtered.groupby("etfTabName")["marketSum"]
                .sum()
                .reset_index()
            )
            fig_pie = px.pie(
                cat_summary,
                values="marketSum",
                names="etfTabName",
                hole=0.4,
                color_discrete_sequence=px.colors.qualitative.Pastel
            )
            fig_pie.update_layout(template="plotly_dark", height=400)
            fig_pie.update_traces(textinfo="percent+label")
            st.plotly_chart(fig_pie, use_container_width=True)

        with row2_col2:
            st.markdown("#### 📦 3개월 수익률 분포 (Histogram & Box Plot)")
            fig_box = px.box(
                df_filtered,
                x="etfTabName",
                y="threeMonthEarnRate",
                color="etfTabName",
                points="outliers",
                labels={"threeMonthEarnRate": "3개월 수익률 (%)", "etfTabName": "카테고리"}
            )
            fig_box.update_layout(template="plotly_dark", height=400, showlegend=False)
            st.plotly_chart(fig_box, use_container_width=True)

    # -------------------------------------------------------------------------
    # TAB 2: 수익률 & 상관관계 EDA
    # -------------------------------------------------------------------------
    with tab2:
        st.subheader("📌 수익률 및 자산 간 상관관계 분석")

        r1_c1, r1_c2 = st.columns(2)
        with r1_c1:
            st.markdown("#### 🚀 3개월 수익률 상위 Top 10 종목")
            top_earn = df_filtered.nlargest(10, "threeMonthEarnRate")
            fig_top_earn = px.bar(
                top_earn,
                x="threeMonthEarnRate",
                y="itemname",
                orientation="h",
                color="threeMonthEarnRate",
                color_continuous_scale="Reds",
                text="threeMonthEarnRate",
                labels={"threeMonthEarnRate": "수익률 (%)", "itemname": "종목명"}
            )
            fig_top_earn.update_layout(yaxis={"categoryorder": "total ascending"}, template="plotly_dark", height=400)
            fig_top_earn.update_traces(texttemplate="%{text:+.2f}%", textposition="outside")
            st.plotly_chart(fig_top_earn, use_container_width=True)

        with r1_c2:
            st.markdown("#### 📉 3개월 수익률 하위 Bottom 10 종목")
            bot_earn = df_filtered.nsmallest(10, "threeMonthEarnRate")
            fig_bot_earn = px.bar(
                bot_earn,
                x="threeMonthEarnRate",
                y="itemname",
                orientation="h",
                color="threeMonthEarnRate",
                color_continuous_scale="Blues_r",
                text="threeMonthEarnRate",
                labels={"threeMonthEarnRate": "수익률 (%)", "itemname": "종목명"}
            )
            fig_bot_earn.update_layout(yaxis={"categoryorder": "total descending"}, template="plotly_dark", height=400)
            fig_bot_earn.update_traces(texttemplate="%{text:+.2f}%", textposition="outside")
            st.plotly_chart(fig_bot_earn, use_container_width=True)

        st.markdown("#### 🌌 시가총액 vs 거래대금 vs 3개월 수익률 관계 (Scatter)")
        fig_scatter = px.scatter(
            df_filtered,
            x="marketSum",
            y="amonut",
            size="marketSum",
            color="threeMonthEarnRate",
            hover_name="itemname",
            hover_data=["itemcode", "nowVal", "nav", "disparateRate"],
            labels={
                "marketSum": "시가총액 (억원)",
                "amonut": "거래대금 (백만원)",
                "threeMonthEarnRate": "3개월 수익률 (%)"
            },
            color_continuous_scale="Spectral",
            log_x=True,
            log_y=True
        )
        fig_scatter.update_layout(template="plotly_dark", height=500)
        st.plotly_chart(fig_scatter, use_container_width=True)

        st.markdown("#### 🌡️ 수치형 변수 상관관계 히트맵 (Correlation Heatmap)")
        corr_cols = ["nowVal", "changeRate", "nav", "threeMonthEarnRate", "quant", "amonut", "marketSum", "disparateRate"]
        corr_df = df_filtered[corr_cols].corr()
        
        fig_corr = px.imshow(
            corr_df,
            text_auto=".2f",
            color_continuous_scale="Viridis",
            labels=dict(x="변수", y="변수", color="상관계수"),
            x=corr_cols,
            y=corr_cols
        )
        fig_corr.update_layout(template="plotly_dark", height=450)
        st.plotly_chart(fig_corr, use_container_width=True)

    # -------------------------------------------------------------------------
    # TAB 3: 종목 탐색기 & 괴리율 분석
    # -------------------------------------------------------------------------
    with tab3:
        st.subheader("📌 괴리율 및 개별 종목 심층 탐색")

        c_disp1, c_disp2 = st.columns(2)
        with c_disp1:
            st.markdown("#### ⚠️ 괴리율 최고 (+) 종목 (고평가 상태)")
            top_disp = df_filtered.nlargest(10, "disparateRate")[["itemcode", "itemname", "nowVal", "nav", "disparateRate", "marketSum"]]
            st.dataframe(
                top_disp.style.format({
                    "nowVal": "{:,.0f}원",
                    "nav": "{:,.0f}원",
                    "disparateRate": "{:+.2f}%",
                    "marketSum": "{:,.0f}억원"
                }),
                use_container_width=True
            )

        with c_disp2:
            st.markdown("#### 🧊 괴리율 최저 (-) 종목 (저평가 상태)")
            bot_disp = df_filtered.nsmallest(10, "disparateRate")[["itemcode", "itemname", "nowVal", "nav", "disparateRate", "marketSum"]]
            st.dataframe(
                bot_disp.style.format({
                    "nowVal": "{:,.0f}원",
                    "nav": "{:,.0f}원",
                    "disparateRate": "{:+.2f}%",
                    "marketSum": "{:,.0f}억원"
                }),
                use_container_width=True
            )

        st.markdown("#### 🔎 실시간 ETF 전체 데이터 그리드")
        display_cols = [
            "itemcode", "itemname", "etfTabName", "nowVal", "changeRate",
            "nav", "disparateRate", "threeMonthEarnRate", "quant", "amonut", "marketSum"
        ]
        
        st.dataframe(
            df_filtered[display_cols].style.format({
                "nowVal": "{:,.0f}",
                "changeRate": "{:+.2f}%",
                "nav": "{:,.0f}",
                "disparateRate": "{:+.2f}%",
                "threeMonthEarnRate": "{:+.2f}%",
                "quant": "{:,.0f}",
                "amonut": "{:,.0f}",
                "marketSum": "{:,.0f}"
            }),
            use_container_width=True,
            height=450
        )

    # -------------------------------------------------------------------------
    # TAB 4: 기술통계량 및 데이터 리포트
    # -------------------------------------------------------------------------
    with tab4:
        st.subheader("📌 데이터 통계 요약 및 결측치 리포트")
        
        col_st1, col_st2 = st.columns(2)

        with col_st1:
            st.markdown("#### 📐 주요 변수 기술통계량 (Descriptive Statistics)")
            stats_df = df_filtered[corr_cols].describe().T[["mean", "std", "min", "50%", "max"]]
            stats_df.columns = ["평균(Mean)", "표준편차(Std)", "최소값(Min)", "중앙값(Median)", "최대값(Max)"]
            st.dataframe(stats_df.style.format("{:,.2f}"), use_container_width=True)

        with col_st2:
            st.markdown("#### 🧪 데이터 무결성 & 결측치 점검")
            null_info = pd.DataFrame({
                "컬럼명": df_filtered.columns,
                "결측치 수": df_filtered.isnull().sum().values,
                "결측 비율(%)": (df_filtered.isnull().sum().values / len(df_filtered)) * 100,
                "데이터 타입": [str(dtype) for dtype in df_filtered.dtypes.values]
            })
            st.dataframe(null_info, use_container_width=True)


if __name__ == "__main__":
    main()
