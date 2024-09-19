import os
from dotenv import load_dotenv
load_dotenv()

def get_fear_and_greed_index():
    import requests

    # Fear and Greed Index 데이터 가져오기
    fng_api_url = "https://api.alternative.me/fng/"
    params = {
        'limit': 1,
        'format': 'json'
    }
    try:
        response = requests.get(fng_api_url, params=params)
        response.raise_for_status()
        fng_data = response.json()
        # Fear and Greed Index 값 추출
        fng_value = fng_data['data'][0]['value']
        fng_classification = fng_data['data'][0]['value_classification']
        fng_timestamp = fng_data['data'][0]['timestamp']
        return {
            'value': fng_value,
            'classification': fng_classification,
            'timestamp': fng_timestamp
        }
    except requests.exceptions.RequestException as e:
        print("Fear and Greed Index 데이터를 가져오는 중 오류 발생:", e)
        return None

def get_latest_news_headlines():
    import requests

    # SerpApi를 사용하여 최신 뉴스 헤드라인 가져오기
    serpapi_api_key = os.getenv("SERPAPI_API_KEY")
    if not serpapi_api_key:
        print("SerpApi API 키가 설정되어 있지 않습니다.")
        return None

    serpapi_url = "https://serpapi.com/search"
    params = {
        'engine': 'google_news',
        'q': 'bitcoin OR cryptocurrency OR blockchain',  # 검색어
        'hl': 'en',  # 언어 설정 (영어)
        'gl': 'us',  # 국가 설정 (미국)
        'api_key': serpapi_api_key
    }
    try:
        response = requests.get(serpapi_url, params=params)
        response.raise_for_status()
        news_data = response.json()
        # 뉴스 헤드라인에서 title과 date만 추출
        news_results = news_data.get('news_results', [])
        headlines = [
            {
                'title': article.get('title', 'No Title'),
                'date': article.get('date', 'No Date')
            }
            for article in news_results[:5]
        ]
        return headlines
    except requests.exceptions.RequestException as e:
        print("뉴스 데이터를 가져오는 중 오류 발생:", e)
        return None

def ai_trading():
    # 필요한 라이브러리 임포트
    import pyupbit
    import ta
    from ta.utils import dropna
    import pandas as pd
    import json
    import openai

    access = os.getenv("UPBIT_ACCESS_KEY")
    secret = os.getenv("UPBIT_SECRET_KEY")
    openai.api_key = os.getenv("OPENAI_API_KEY")

    upbit = pyupbit.Upbit(access, secret)

    # 업비트 차트 데이터 가져오기 (60일 일봉)
    df_daily = pyupbit.get_ohlcv("KRW-BTC", count=60, interval="day")
    df_daily = dropna(df_daily)

    # 일봉 데이터에 보조지표 추가
    df_daily['RSI'] = ta.momentum.RSIIndicator(df_daily['close'], window=14).rsi()
    macd = ta.trend.MACD(df_daily['close'])
    df_daily['MACD'] = macd.macd()
    df_daily['MACD_Signal'] = macd.macd_signal()
    df_daily['MACD_Hist'] = macd.macd_diff()
    df_daily['SMA50'] = ta.trend.SMAIndicator(df_daily['close'], window=50).sma_indicator()
    df_daily['SMA200'] = ta.trend.SMAIndicator(df_daily['close'], window=200).sma_indicator()

    # 업비트 차트 데이터 가져오기 (100시간 시간봉)
    df_hourly = pyupbit.get_ohlcv("KRW-BTC", count=100, interval="minute60")
    df_hourly = dropna(df_hourly)

    # 시간봉 데이터에 보조지표 추가
    df_hourly['RSI'] = ta.momentum.RSIIndicator(df_hourly['close'], window=14).rsi()
    macd_hourly = ta.trend.MACD(df_hourly['close'])
    df_hourly['MACD'] = macd_hourly.macd()
    df_hourly['MACD_Signal'] = macd_hourly.macd_signal()
    df_hourly['MACD_Hist'] = macd_hourly.macd_diff()

    # 업비트 호가 데이터 가져오기
    orderbook = pyupbit.get_orderbook(ticker="KRW-BTC")

    # 현재 투자 상태 가져오기
    balance = upbit.get_balances()
    filtered_balance = [item for item in balance if item['currency'] in ['BTC', 'KRW']]

    # Fear and Greed Index 데이터 가져오기
    fng = get_fear_and_greed_index()
    if fng is None:
        print("Fear and Greed Index 데이터를 가져오지 못하여 거래를 중단합니다.")
        return

    # 최신 뉴스 헤드라인 가져오기
    news_headlines = get_latest_news_headlines()
    if news_headlines is None:
        print("뉴스 데이터를 가져오지 못하여 거래를 중단합니다.")
        return

    # 데이터 준비
    df_daily_selected = df_daily[['open', 'high', 'low', 'close', 'volume', 'RSI', 'MACD', 'MACD_Signal', 'MACD_Hist', 'SMA50', 'SMA200']].tail(60)
    df_hourly_selected = df_hourly[['open', 'high', 'low', 'close', 'volume', 'RSI', 'MACD', 'MACD_Signal', 'MACD_Hist']].tail(100)

    data = {
        "daily_ohlcv": df_daily_selected.to_dict(),
        "hourly_ohlcv": df_hourly_selected.to_dict(),
        "orderbook": orderbook,
        "balance": filtered_balance,
        "fear_and_greed_index": fng,
        "news_headlines": news_headlines
    }

    data_json = json.dumps(data)

    # 프롬프트 작성
    prompt = f"""
    당신은 비트코인 투자 전문가이자 퀀트 트레이더입니다.
    제공된 데이터 (현재 투자 상태, 호가 데이터, 보조지표가 포함된 60일 일봉 OHLCV, 보조지표가 포함된 100시간 시간봉 OHLCV, Fear and Greed Index, 최신 뉴스 헤드라인)를 분석하여,
    RSI, MACD, 이동평균선 등의 기술적 지표와 시장 심리 지표인 Fear and Greed Index, 그리고 최신 뉴스 헤드라인을 기반으로 현재 시점에서 매수, 매도, 보류 중 무엇을 할지 판단해 주세요.
    판단 근거를 상세히 설명하고, 수익률을 높일 수 있는 전략을 제시하세요.
    JSON 형식으로 응답하세요.

    현재 Fear and Greed Index 값은 {fng['value']}이며, 이는 '{fng['classification']}' 상태를 나타냅니다.

    최신 뉴스 헤드라인은 다음과 같습니다 (각 뉴스는 'title'과 'date'를 포함합니다):
    {news_headlines}

    응답 예시:
    {{"decision":"buy","reason":"RSI가 과매도 영역에서 상승 반전했고, MACD가 골든크로스를 형성하였습니다. 또한 최근 뉴스에서 긍정적인 소식이 전해지고 있고, Fear and Greed Index가 '공포' 상태로 반등 가능성이 있습니다."}}
    {{"decision":"sell","reason":"RSI가 과매수 상태이고, MACD 히스토그램이 감소 추세입니다. 또한 최근 뉴스에서 부정적인 이슈가 보도되고 있고, Fear and Greed Index가 '탐욕' 상태로 조정이 예상됩니다."}}
    {{"decision":"hold","reason":"현재 시장 변동성이 높아 관망이 필요합니다. 주요 지표들이 명확한 신호를 제공하지 않고 있으며, 최근 뉴스에서도 특별한 이슈가 없고, Fear and Greed Index가 중립 상태입니다."}}
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

    # AI의 판단에 따라 자동매매 진행
    try:
        result_json = json.loads(result)
    except json.JSONDecodeError:
        print("AI의 응답이 JSON 형식이 아닙니다. 응답 내용:")
        print(result)
        return

    print("### AI Decision: ", result_json["decision"].upper(), "###")
    print(f"### Reason: {result_json['reason']} ###")

    # 매수/매도 금액 설정
    buy_amount = 6000  # 매수 금액 6,000원
    sell_amount = 6000  # 매도 시 6,000원어치 BTC 판매

    # 현재 BTC 가격 가져오기
    current_price = pyupbit.get_current_price("KRW-BTC")

    # 매도할 BTC 수량 계산
    btc_to_sell = sell_amount / current_price

    decision = result_json["decision"].lower()
    if decision == "buy":
        # 매수
        krw_balance = float(upbit.get_balance("KRW"))
        if krw_balance >= buy_amount:
            print(upbit.buy_market_order("KRW-BTC", buy_amount))
            print("buy:", result_json["reason"])
        else:
            print("매수할 금액이 부족합니다.")
    elif decision == "sell":
        # 매도
        btc_balance = float(upbit.get_balance("BTC"))
        if btc_balance >= btc_to_sell:
            print(upbit.sell_market_order("KRW-BTC", btc_to_sell))
            print("sell:", result_json["reason"])
        elif btc_balance > 0:
            print(upbit.sell_market_order("KRW-BTC", btc_balance))
            print("보유한 모든 비트코인을 매도했습니다.")
        else:
            print("매도할 비트코인 보유량이 없습니다.")
    elif decision == "hold":
        # 보류
        print("hold:", result_json["reason"])
    else:
        print("알 수 없는 결정입니다:", result_json["decision"])

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
