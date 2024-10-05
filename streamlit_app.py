import sqlite3
import pandas as pd
import streamlit as st
import logging
from datetime import datetime
import plotly.express as px

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# DB 경로 설정
DB_PATH = "trading_data.db"

def init_db():
    """SQLite 데이터베이스와 필요한 테이블을 초기화합니다."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 거래 결정 테이블 수정 (reflection 컬럼 추가)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS trades (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT NOT NULL,
        decision TEXT NOT NULL CHECK(decision IN ('buy', 'sell', 'hold')),
        percentage INTEGER NOT NULL CHECK(percentage BETWEEN 0 AND 100),
        reason TEXT NOT NULL,
        btc_balance REAL NOT NULL,
        krw_balance REAL NOT NULL,
        btc_avg_buy_price REAL NOT NULL,
        btc_krw_price REAL NOT NULL,
        reflection TEXT
    )
    """)
    
    conn.commit()
    conn.close()
    logger.info("SQLite 데이터베이스가 초기화되었습니다.")

def load_data():
    """데이터베이스에서 trades 테이블의 데이터를 불러옵니다."""
    conn = sqlite3.connect(DB_PATH)
    query = "SELECT * FROM trades ORDER BY timestamp DESC"
    df = pd.read_sql(query, conn)
    conn.close()
    return df

def add_trade(data):
    """새로운 거래 데이터를 데이터베이스에 추가합니다."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO trades (timestamp, decision, percentage, reason, btc_balance, krw_balance, btc_avg_buy_price, btc_krw_price, reflection)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        data['timestamp'],
        data['decision'],
        data['percentage'],
        data['reason'],
        data['btc_balance'],
        data['krw_balance'],
        data['btc_avg_buy_price'],
        data['btc_krw_price'],
        data.get('reflection', '')
    ))
    conn.commit()
    conn.close()
    logger.info("새로운 거래 데이터가 추가되었습니다.")

def main():
    st.set_page_config(page_title="Trading Data Viewer", layout="wide")
    st.title("Trading Data Viewer")
    st.write("이 웹 애플리케이션은 `trading_data.db`에 저장된 거래 데이터를 표시합니다.")

    # 데이터베이스 초기화
    init_db()

    # 사이드바를 이용한 데이터 추가
    st.sidebar.header("새로운 거래 추가")
    with st.sidebar.form(key='add_trade_form'):
        timestamp = st.text_input("타임스탬프 (YYYY-MM-DD HH:MM:SS)", value=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        decision = st.selectbox("결정", options=["buy", "sell", "hold"])
        percentage = st.number_input("퍼센트 (%)", min_value=0, max_value=100, value=50)
        reason = st.text_input("이유")
        btc_balance = st.number_input("BTC 잔고", min_value=0.0, value=0.0)
        krw_balance = st.number_input("KRW 잔고", min_value=0.0, value=0.0)
        btc_avg_buy_price = st.number_input("BTC 평균 매수가격", min_value=0.0, value=0.0)
        btc_krw_price = st.number_input("BTC/KRW 가격", min_value=0.0, value=0.0)
        reflection = st.text_area("반영사항 (선택사항)")
        submit_button = st.form_submit_button(label='추가')

    if submit_button:
        trade_data = {
            'timestamp': timestamp,
            'decision': decision,
            'percentage': percentage,
            'reason': reason,
            'btc_balance': btc_balance,
            'krw_balance': krw_balance,
            'btc_avg_buy_price': btc_avg_buy_price,
            'btc_krw_price': btc_krw_price,
            'reflection': reflection
        }
        add_trade(trade_data)
        st.success("새로운 거래 데이터가 추가되었습니다.")
    
    # 데이터 불러오기
    data = load_data()

    # 데이터 필터링 옵션
    st.sidebar.header("데이터 필터링")
    decision_filter = st.sidebar.multiselect(
        "결정 필터링",
        options=["buy", "sell", "hold"],
        default=["buy", "sell", "hold"]
    )
    date_from = st.sidebar.date_input("시작 날짜", value=datetime(2020, 1, 1))
    date_to = st.sidebar.date_input("종료 날짜", value=datetime.now())

    # 필터 적용
    if not data.empty:
        data['timestamp'] = pd.to_datetime(data['timestamp'])
        mask = (
            data['decision'].isin(decision_filter) &
            (data['timestamp'].dt.date >= date_from) &
            (data['timestamp'].dt.date <= date_to)
        )
        filtered_data = data.loc[mask]
    else:
        filtered_data = data

    # 데이터 표시
    st.write("### 거래 데이터 테이블")
    st.dataframe(filtered_data)
    
    # 간단한 통계 정보
    st.write("### 통계 정보")
    st.write(f"총 거래 건수: {len(filtered_data)}")
    st.write(f"Buy 건수: {len(filtered_data[filtered_data['decision'] == 'buy'])}")
    st.write(f"Sell 건수: {len(filtered_data[filtered_data['decision'] == 'sell'])}")
    st.write(f"Hold 건수: {len(filtered_data[filtered_data['decision'] == 'hold'])}")

    # Trade Decision Distribution 그래프 (Plotly 사용)
    st.write("### Trade Decision Distribution")
    if not filtered_data.empty:
        decision_counts = filtered_data['decision'].value_counts().reset_index()
        decision_counts.columns = ['Decision', 'Count']
        
        fig = px.pie(decision_counts, names='Decision', values='Count', 
                     title='Trade Decision Distribution',
                     color='Decision',
                     color_discrete_map={'buy':'#2ca02c', 'sell':'#d62728', 'hold':'#1f77b4'},
                     hole=0.3)  # 도넛 형태로 만들려면 hole 값을 0.3 등으로 설정
        fig.update_traces(textposition='inside', textinfo='percent+label')
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.write("데이터가 없어 그래프를 표시할 수 없습니다.")

    # 데이터 다운로드
    st.download_button(
        label="데이터 다운로드 (CSV)",
        data=filtered_data.to_csv(index=False).encode('utf-8'),
        file_name='trading_data.csv',
        mime='text/csv',
    )

if __name__ == "__main__":
    main()
