import os
from dotenv import load_dotenv
load_dotenv()

def ai_trading():
    # 0. Upbit 클라이언트 초기화
    import pyupbit
    import ta
    from ta.utils import dropna
    import pandas as pd
    access = os.getenv("UPBIT_ACCESS_KEY")
    secret = os.getenv("UPBIT_SECRET_KEY")
    upbit = pyupbit.Upbit(access, secret)

    # 1. 업비트 차트 데이터 가져오기 (60일 일봉)
    df_daily = pyupbit.get_ohlcv("KRW-BTC", count=60, interval="day")
    df_daily = dropna(df_daily)

    # 1-1. 일봉 데이터에 보조지표 추가
    # RSI 지표 추가
    df_daily['RSI'] = ta.momentum.RSIIndicator(df_daily['close'], window=14).rsi()
    # MACD 지표 추가
    macd = ta.trend.MACD(df_daily['close'])
    df_daily['MACD'] = macd.macd()
    df_daily['MACD_Signal'] = macd.macd_signal()
    df_daily['MACD_Hist'] = macd.macd_diff()
    # 이동평균선 추가
    df_daily['SMA50'] = ta.trend.SMAIndicator(df_daily['close'], window=50).sma_indicator()
    df_daily['SMA200'] = ta.trend.SMAIndicator(df_daily['close'], window=200).sma_indicator()

    # 1-2. 업비트 차트 데이터 가져오기 (100시간 시간봉)
    df_hourly = pyupbit.get_ohlcv("KRW-BTC", count=100, interval="minute60")
    df_hourly = dropna(df_hourly)

    # 1-3. 시간봉 데이터에 보조지표 추가
    # RSI 지표 추가
    df_hourly['RSI'] = ta.momentum.RSIIndicator(df_hourly['close'], window=14).rsi()
    # MACD 지표 추가
    macd_hourly = ta.trend.MACD(df_hourly['close'])
    df_hourly['MACD'] = macd_hourly.macd()
    df_hourly['MACD_Signal'] = macd_hourly.macd_signal()
    df_hourly['MACD_Hist'] = macd_hourly.macd_diff()

    # 1-4. 업비트 호가 데이터 가져오기
    orderbook = pyupbit.get_orderbook(ticker="KRW-BTC")

    # 1-5. 현재 투자 상태 가져오기
    balance = upbit.get_balances()
    # BTC와 KRW에 대한 정보만 필터링
    filtered_balance = [item for item in balance if item['currency'] in ['BTC', 'KRW']]

    # 2. AI에게 데이터 제공하고 판단 받기
    import json

    # 데이터 크기를 줄이기 위해 필요한 열만 선택
    df_daily_selected = df_daily[['open', 'high', 'low', 'close', 'volume', 'RSI', 'MACD', 'MACD_Signal', 'MACD_Hist', 'SMA50', 'SMA200']].tail(60)
    df_hourly_selected = df_hourly[['open', 'high', 'low', 'close', 'volume', 'RSI', 'MACD', 'MACD_Signal', 'MACD_Hist']].tail(100)

    data = {
        "daily_ohlcv": df_daily_selected.to_dict(),
        "hourly_ohlcv": df_hourly_selected.to_dict(),
        "orderbook": orderbook,
        "balance": filtered_balance
    }

    data_json = json.dumps(data)

    import openai
    openai.api_key = os.getenv("OPENAI_API_KEY")

    # 프롬프트 수정: 보조지표 활용하여 수익률을 높일 수 있는 전략 제안
    prompt = """
    당신은 비트코인 투자 전문가이자 퀀트 트레이더입니다.
    제공된 데이터 (현재 투자 상태, 호가 데이터, 보조지표가 포함된 60일 일봉 OHLCV, 보조지표가 포함된 100시간 시간봉 OHLCV)를 분석하여,
    RSI, MACD, 이동평균선 등의 기술적 지표를 기반으로 현재 시점에서 매수, 매도, 보류 중 무엇을 할지 판단해 주세요.
    판단 근거를 상세히 설명하고, 수익률을 높일 수 있는 전략을 제시하세요.
    JSON 형식으로 응답하세요.

    응답 예시:
    {"decision":"buy","reason":"RSI가 과매도 영역에서 상승 반전했고, MACD가 골든크로스를 형성하였습니다. 또한 단기 이동평균선이 장기 이동평균선을 상향 돌파하였습니다."}
    {"decision":"sell","reason":"RSI가 과매수 상태이고, MACD 히스토그램이 감소 추세입니다. 단기 이동평균선이 장기 이동평균선을 하향 돌파하였습니다."}
    {"decision":"hold","reason":"현재 시장 변동성이 높아 관망이 필요합니다. 주요 지표들이 명확한 신호를 제공하지 않고 있습니다."}
    """

    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {
                "role": "system",
                "content": prompt
            },
            {
                "role": "user",
                "content": data_json
            }
        ]
    )

    result = response['choices'][0]['message']['content']

    # 3. AI의 판단에 따라 실제로 자동매매 진행하기
    result = json.loads(result)

    print("### AI Decision: ", result["decision"].upper(), "###")
    print(f"### Reason: {result['reason']} ###")

    # 매수/매도 금액 설정
    buy_amount = 6000  # 매수 금액 6,000원
    sell_amount = 6000  # 매도 시 6,000원어치 BTC 판매

    # 현재 BTC 가격 가져오기
    current_price = pyupbit.get_current_price("KRW-BTC")

    # 매도할 BTC 수량 계산
    btc_to_sell = sell_amount / current_price

    match result["decision"]:
        case "buy":
            # 매수
            if buy_amount >= 5000:  # 최소 거래 금액 확인
                print(upbit.buy_market_order("KRW-BTC", buy_amount))
                print("buy:", result["reason"])
            else:
                print("매수할 금액이 부족합니다.")
        case "sell":
            # 매도
            btc_balance = float(upbit.get_balance("BTC"))
            if btc_balance >= btc_to_sell:
                print(upbit.sell_market_order("KRW-BTC", btc_to_sell))
                print("sell:", result["reason"])
            elif btc_balance > 0:
                print(upbit.sell_market_order("KRW-BTC", btc_balance))
                print("보유한 모든 비트코인을 매도했습니다.")
            else:
                print("매도할 비트코인 보유량이 없습니다.")
        case "hold":
            # 보류
            print("hold:", result["reason"])
        case _:
            print("알 수 없는 결정입니다:", result["decision"])

    # 마지막에 일봉 데이터와 시간봉 데이터의 tail() 출력
    print("\n=== 일봉 데이터 (최근 5개) ===")
    print(df_daily_selected.tail())

    print("\n=== 시간봉 데이터 (최근 5개) ===")
    print(df_hourly_selected.tail())

if __name__ == "__main__":
    while True:
        import time
        ai_trading()
        time.sleep(300)  # 5분마다 실행
