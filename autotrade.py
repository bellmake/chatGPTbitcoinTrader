import os
from dotenv import load_dotenv
load_dotenv()

def ai_trading():
    # 0. Upbit 클라이언트 초기화
    import pyupbit
    access = os.getenv("UPBIT_ACCESS_KEY")
    secret = os.getenv("UPBIT_SECRET_KEY")
    upbit = pyupbit.Upbit(access, secret)

    # 1. 업비트 차트 데이터 가져오기 (30일 일봉)
    df_daily = pyupbit.get_ohlcv("KRW-BTC", count=30, interval="day")
    print("daily:",df_daily)

    # 1-1. 업비트 차트 데이터 가져오기 (24시간 1시간봉)
    df_hourly = pyupbit.get_ohlcv("KRW-BTC", count=24, interval="minute60")
    print("hourly:",df_hourly)

    # 1-2. 업비트 호가 데이터 가져오기
    orderbook = pyupbit.get_orderbook(ticker="KRW-BTC")

    # 1-3. 현재 투자 상태 가져오기
    balance = upbit.get_balances()

    # BTC와 KRW에 대한 정보만 필터링
    filtered_balance = [item for item in balance if item['currency'] in ['BTC', 'KRW']]
    
    print("filtered balance:",filtered_balance)

    # 2. AI에게 데이터 제공하고 판단 받기
    import json

    data = {
        "daily_ohlcv": df_daily.to_dict(),
        "hourly_ohlcv": df_hourly.to_dict(),
        "orderbook": orderbook,
        "balance": filtered_balance  # 수정된 부분
    }

    data_json = json.dumps(data)

    import openai
    openai.api_key = os.getenv("OPENAI_API_KEY")

    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {
                "role": "system",
                "content": "당신은 비트코인 투자 전문가입니다. 제공된 데이터 (현재 투자 상태, 호가 데이터, 30일 일봉 OHLCV, 24시간 시간봉 OHLCV)를 기반으로 현재 시점에서 매수, 매도, 보류 중 무엇을 할지 판단해 주세요. JSON 형식으로 응답하세요.\n\n응답 예시:\n{\"decision\":\"buy\",\"reason\":\"기술적 분석 결과 상승 추세입니다.\"}\n{\"decision\":\"sell\",\"reason\":\"지표상 과매수 상태입니다.\"}\n{\"decision\":\"hold\",\"reason\":\"시장 변동성이 높아 관망이 필요합니다.\"}"
            },
            {
                "role": "user",
                "content": data_json
            }
        ]
    )

    result = response['choices'][0]['message']['content']
    # print(type(result))
    # print(result)

    # 3. AI의 판단에 따라 실제로 자동매매 진행하기
    result = json.loads(result)

    print("### AI Decision: ", result["decision"].upper(), "###")
    print(f"### Reason: {result['reason']} ###")

    match result["decision"]:
        case "buy":
            # 매수
            print(upbit.buy_market_order("KRW-BTC", 6000))  # 6,000원어치 비트코인 매수
            print("buy:", result["reason"])
        case "sell":
            # 매도
            btc_balance = upbit.get_balance("BTC")
            if btc_balance > 0:
                print(upbit.sell_market_order("KRW-BTC", btc_balance))  # 보유한 비트코인 전량 매도
                print("sell:", result["reason"])
            else:
                print("매도할 비트코인 보유량이 없습니다.")
        case "hold":
            # 보류
            print("hold:", result["reason"])
        case _:
            print("알 수 없는 결정입니다:", result["decision"])

# while True:
    # import time
ai_trading()
    # time.sleep(30)
