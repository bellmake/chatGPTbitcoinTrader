import os
from dotenv import load_dotenv
load_dotenv()

def ai_trading():
  # 1. 업비트 차트 데이터 가져오기 (30일 일봉)
  import pyupbit
  df = pyupbit.get_ohlcv("KRW-BTC", count=30, interval="day")
  # print(df.to_json())

  # 2. AI에게 데이터 제공하고 판단 받기
  from openai import OpenAI
  client = OpenAI()

  response = client.chat.completions.create(
    model="gpt-4o",
    messages=[
      {
        "role": "system",
        "content": [
          {
            "type": "text",
            "text": "You are an expert in Bitcoin investing. Tell me whether to buy, sell, or hold at the moment based on the char data provided. response in json format.\n\nResponse Example:\n{\"decision\":\"buy\",\"reason\":\"some technical reason\"}\n{\"decision\":\"sell\",\"reason\":\"some technical reason\"}\n{\"decision\":\"hold\",\"reason\":\"some technical reason\"}"
          }
        ]
      },
      {
        "role": "user",
        "content": [
          {
            "type": "text",
            "text": df.to_json()
          }
        ]
      }
    ],
    response_format={
      "type": "json_object"
    }
)
  result = response.choices[0].message.content
  print(type(result))
  # print(response.choices[0].message.content)

  # 3. AI의 판단에 따라 실제로 자동매매 진행하기
  import json
  result = json.loads(result)

  import pyupbit
  access = os.getenv("UPBIT_ACCESS_KEY")
  secret = os.getenv("UPBIT_SECRET_KEY")
  upbit = pyupbit.Upbit(access, secret)

  print("### AI Decision: ", result["decision"].upper(), "###")
  print(f"### Reason: {result['reason']} ###")

  match result["decision"]:
      case "buy":
          # 매수
          print(upbit.buy_market_order("KRW-BTC",price=6000)) # 비트코인 0.000075개
          print("buy:",result["reason"])
      case "sell":
          # 매도
          print(upbit.sell_market_order("KRW-BTC",volume=0.000075)) # 비트코인 약 6000원
          print("sell:",result["reason"])
      case "hold":
          # 보류
          print("hold:",result["reason"])
        
while True:
  import time
  ai_trading()
  time.sleep(30)
  