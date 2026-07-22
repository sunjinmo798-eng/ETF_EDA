"""
ETF Interactive EDA Dashboard application built with Streamlit.

이 대시보드 앱은 사용자가 시각적으로 ETF 데이터를 탐색하고
수익률 그래프, 상관관계 히트맵, 리스크 지표를 한눈에 비교 분석할 수 있도록 지원합니다.
"""

import sys
from pathlib import Path
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

# Root 경로 추가를 통해 src 모듈 참조 가능하게 설정
sys.path.append(str(Path(__file__).resolve().parent.parent))

from src.data_loader import ETFDataLoader
from src.eda_analyzer import ETFAnalyzer


def run_dashboard() -> None:
    """
    Streamlit 기반 ETF EDA 대시보드 구동 함수.
    """
    st.set_page_config(
        page_title="ETF EDA Dashboard",
        page_icon="📈",
        layout="wide"
    )

    st.title("📈 ETF Exploratory Data Analysis Dashboard")
    st.markdown("주요 ETF의 실시간 시세 수집 및 투자 성과/리스크 분석 대시보드입니다.")

    # 사이드바 입력 컨트롤
    st.sidebar.header("설정 (Settings)")
    default_tickers = "SPY, QQQ, SCHD, TLT"
    user_tickers_input = st.sidebar.text_input("ETF 티커 입력 (쉼표로 구분)", default_tickers)
    period = st.sidebar.selectbox("조회 기간", ["3mo", "6mo", "1y", "2y", "5y"], index=2)
    risk_free_rate = st.sidebar.number_input("무위험 이자율 (%)", value=3.5, step=0.1) / 100.0

    tickers = [t.strip().upper() for t in user_tickers_input.split(",") if t.strip()]

    if not tickers:
        st.warning("최소 하나 이상의 ETF 티커를 입력해주세요.")
        return

    # 데이터 로드
    with st.spinner("데이터 로딩 중..."):
        try:
            loader = ETFDataLoader(tickers=tickers)
            price_df = loader.fetch_history(period=period)
        except Exception as e:
            st.error(f"데이터를 불러오는 중 오류가 발생했습니다: {e}")
            return

    analyzer = ETFAnalyzer(price_df=price_df, risk_free_rate=risk_free_rate)

    # 1. 누적 수익률 차트
    st.subheader("1. 누적 수익률 추이 (Cumulative Return)")
    cum_returns = analyzer.get_cumulative_returns() * 100.0
    fig_line = px.line(
        cum_returns,
        labels={"value": "수익률 (%)", "Date": "날짜"},
        title=f"ETF 누적 수익률 비교 ({period})"
    )
    st.plotly_chart(fig_line, use_container_width=True)

    # 2. 요약 지표 및 상관관계
    col1, col2 = st.columns([1, 1])

    with col1:
        st.subheader("2. 성과 및 리스크 요약")
        metrics = analyzer.calculate_performance_metrics().round(4)
        st.dataframe(metrics, use_container_width=True)

    with col2:
        st.subheader("3. ETF 간 상관관계 히트맵")
        corr = analyzer.get_correlation_matrix().round(3)
        fig_heat = px.imshow(
            corr,
            text_auto=True,
            color_continuous_scale="Blues",
            title="수익률 상관계수 (Correlation Matrix)"
        )
        st.plotly_chart(fig_heat, use_container_width=True)


if __name__ == "__main__":
    run_dashboard()
