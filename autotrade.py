import os
from dotenv import load_dotenv
import logging
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from PIL import Image
import io
import base64
import pyupbit
import ta
from ta.utils import dropna
import pandas as pd
import json
from openai import OpenAI
import requests
import json
from youtube_transcript_api import YouTubeTranscriptApi

load_dotenv()

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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

def capture_chart_screenshots():
    # 크롬 옵션 설정
    chrome_options = Options()
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument("--headless") # 디버깅시 주석처리
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")

    # 웹 드라이버 실행
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

    # 업비트 차트 페이지로 이동
    url = "https://upbit.com/full_chart?code=CRIX.UPBIT.KRW-BTC"
    driver.get(url)

    # 페이지 로딩 대기
    time.sleep(1)

    screenshots = {}

    try:
        # 30분 옵션 선택 및 스크린샷
        logger.info("30분 옵션 선택 중...")
        menu_button_xpath = '/html/body/div[1]/div[2]/div[3]/span/div/div/div[1]/div/div/cq-menu[1]'
        menu_button = WebDriverWait(driver, 2).until(EC.element_to_be_clickable((By.XPATH, menu_button_xpath)))
        menu_button.click()

        thirty_min_option_xpath = '/html/body/div[1]/div[2]/div[3]/span/div/div/div[1]/div/div/cq-menu[1]/cq-menu-dropdown/cq-item[7]'
        thirty_min_option = WebDriverWait(driver, 2).until(EC.element_to_be_clickable((By.XPATH, thirty_min_option_xpath)))
        thirty_min_option.click()

        time.sleep(1)
        screenshot = driver.get_screenshot_as_png()
        screenshots['30min'] = base64.b64encode(screenshot).decode('utf-8')

        # 스크린샷 이미지를 파일로 저장
        screenshot_image = Image.open(io.BytesIO(screenshot))
        thirty_min_screenshot_path = "upbit_btc_full_chart_30min.png"
        screenshot_image.save(thirty_min_screenshot_path)
        logger.info("30분 옵션 선택 후 스크린샷이 성공적으로 저장되었습니다: %s", thirty_min_screenshot_path)

        # 1시간 옵션 선택 및 스크린샷
        logger.info("1시간 옵션 선택 중...")
        menu_button.click()
        one_hour_option_xpath = '/html/body/div[1]/div[2]/div[3]/span/div/div/div[1]/div/div/cq-menu[1]/cq-menu-dropdown/cq-item[8]'
        one_hour_option = WebDriverWait(driver, 2).until(EC.element_to_be_clickable((By.XPATH, one_hour_option_xpath)))
        one_hour_option.click()

        time.sleep(1)
        screenshot = driver.get_screenshot_as_png()
        screenshots['1hour'] = base64.b64encode(screenshot).decode('utf-8')

        # 스크린샷 이미지를 파일로 저장
        screenshot_image = Image.open(io.BytesIO(screenshot))
        one_hour_screenshot_path = "upbit_btc_full_chart_1hour.png"
        screenshot_image.save(one_hour_screenshot_path)
        logger.info("1시간 옵션 선택 후 스크린샷이 성공적으로 저장되었습니다: %s", one_hour_screenshot_path)

        # 볼린저 밴드 옵션 선택 및 스크린샷
        logger.info("볼린저 밴드 옵션 선택 중...")
        indicator_menu_xpath = '/html/body/div[1]/div[2]/div[3]/span/div/div/div[1]/div/div/cq-menu[3]'
        indicator_menu = WebDriverWait(driver, 2).until(EC.element_to_be_clickable((By.XPATH, indicator_menu_xpath)))
        indicator_menu.click()

        bollinger_band_option_xpath = '/html/body/div[1]/div[2]/div[3]/span/div/div/div[1]/div/div/cq-menu[3]/cq-menu-dropdown/cq-scroll/cq-studies/cq-studies-content/cq-item[15]'
        bollinger_band_option = WebDriverWait(driver, 2).until(EC.element_to_be_clickable((By.XPATH, bollinger_band_option_xpath)))
        bollinger_band_option.click()

        time.sleep(1)
        screenshot = driver.get_screenshot_as_png()
        screenshots['bollinger'] = base64.b64encode(screenshot).decode('utf-8')

        # 스크린샷 이미지를 파일로 저장
        screenshot_image = Image.open(io.BytesIO(screenshot))
        bollinger_screenshot_path = "upbit_btc_full_chart_bollinger.png"
        screenshot_image.save(bollinger_screenshot_path)
        logger.info("볼린저 밴드 옵션 선택 후 스크린샷이 성공적으로 저장되었습니다: %s", bollinger_screenshot_path)

    except Exception as e:
        logger.error("차트 스크린샷 캡처 중 오류 발생: %s", e)

    # 브라우저 종료
    driver.quit()

    return screenshots

def analyze_chart_with_gpt4o(screenshots):
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    analysis_results = {}

    for chart_type, base64_image in screenshots.items():
        prompt = f"이 비트코인 차트는 {chart_type} 설정의 스크린샷입니다. 이 차트를 분석하고, 현재 시장 상황과 향후 단기 트렌드에 대해 설명해주세요. 또한 이 차트를 바탕으로 매수/매도/홀드 중 어떤 행동을 취해야 할지 제안해주세요."

        try:
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{base64_image}"}}
                        ]
                    }
                ],
                max_tokens=300
            )
            analysis_results[chart_type] = response.choices[0].message.content
        except Exception as e:
            logger.error(f"GPT-4o API 요청 중 오류 발생 ({chart_type}): {e}")
            analysis_results[chart_type] = "분석 실패"

    return analysis_results

def get_full_transcript(video_id):
    try:
        # Get the transcript data
        transcript_data = YouTubeTranscriptApi.get_transcript(video_id)

        # Extract and concatenate all text items
        full_transcript = ' '.join(item['text'] for item in transcript_data)

        return full_transcript
    except Exception as e:
        logger.error(f"유튜브 자막 가져오기 실패 (video_id: {video_id}): {e}")
        return None

def ai_trading():
    access = os.getenv("UPBIT_ACCESS_KEY")
    secret = os.getenv("UPBIT_SECRET_KEY")
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

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

    # 차트 스크린샷 캡처 및 gpt-4o 분석
    screenshots = capture_chart_screenshots()
    chart_analysis = analyze_chart_with_gpt4o(screenshots)

    # 데이터 준비 (index를 string으로 변환하여 JSON 직렬화 가능하게 처리)
    df_daily_selected = df_daily[['open', 'high', 'low', 'close', 'volume', 'RSI', 'MACD', 'MACD_Signal', 'MACD_Hist', 'SMA50', 'SMA200']].tail(60)
    df_hourly_selected = df_hourly[['open', 'high', 'low', 'close', 'volume', 'RSI', 'MACD', 'MACD_Signal', 'MACD_Hist']].tail(100)

    # 여기서 DataFrame의 인덱스를 문자열로 변환하여 직렬화 가능하게 만듭니다.
    df_daily_selected.index = df_daily_selected.index.astype(str)
    df_hourly_selected.index = df_hourly_selected.index.astype(str)

    # YouTube 자막 데이터 가져오기
    video_ids = ["TWINrTppUl4"]  # 분석하고자 하는 영상의 ID 리스트
    youtube_transcripts = []
    for video_id in video_ids:
        transcript = get_full_transcript(video_id)
        if transcript:
            youtube_transcripts.append(transcript)    

    data = {
        "daily_ohlcv": df_daily_selected.to_dict(),
        "hourly_ohlcv": df_hourly_selected.to_dict(),
        "orderbook": orderbook,
        "balance": filtered_balance,
        "fear_and_greed_index": fng,
        "news_headlines": news_headlines,
        "chart_analysis": chart_analysis,
        "youtube_transcripts": youtube_transcripts
    }

    # JSON 직렬화
    data_json = json.dumps(data)

    # 프롬프트 작성 및 GPT-4o 요청
    prompt = f"""
    당신은 비트코인 투자 전문가이자 퀀트 트레이더입니다.
    제공된 데이터 (현재 투자 상태, 호가 데이터, 보조지표가 포함된 60일 일봉 OHLCV, 보조지표가 포함된 100시간 시간봉 OHLCV, Fear and Greed Index, 최신 뉴스 헤드라인, gpt-4o의 차트 분석 결과, YouTube 투자 관련 영상의 자막 데이터)를 분석하여,
    RSI, MACD, 이동평균선 등의 기술적 지표와 시장 심리 지표인 Fear and Greed Index, 최신 뉴스 헤드라인, gpt-4o의 차트 분석 결과, 그리고 YouTube 영상의 자막 내용을 종합적으로 고려하여 현재 시점에서 매수, 매도, 보류 중 무엇을 할지 판단해 주세요.
    판단 근거를 상세히 설명하고, 수익률을 높일 수 있는 전략을 제시하세요.
    JSON 형식으로 응답하세요.

    현재 Fear and Greed Index 값은 {fng['value']}이며, 이는 '{fng['classification']}' 상태를 나타냅니다.

    최신 뉴스 헤드라인은 다음과 같습니다 (각 뉴스는 'title'과 'date'를 포함합니다):
    {news_headlines}

    gpt-4o의 차트 분석 결과:
    1시간 차트: {chart_analysis['1hour']}
    30분 차트: {chart_analysis['30min']}
    볼린저 밴드: {chart_analysis['bollinger']}
    
    YouTube 투자 관련 영상의 자막 데이터도 제공되었습니다. 이 정보를 분석에 활용하세요.

    응답 예시:
    {{"decision":"buy","reason":"RSI가 과매도 영역에서 상승 반전했고, MACD가 골든크로스를 형성하였습니다. 또한 최근 뉴스와 YouTube 영상에서 긍정적인 전망이 제시되고 있고, Fear and Greed Index가 '공포' 상태로 반등 가능성이 있습니다. gpt-4o의 차트 분석에서도 단기 상승 추세가 예상됩니다."}}
    {{"decision":"sell","reason":"RSI가 과매수 상태이고, MACD 히스토그램이 감소 추세입니다. 또한 최근 뉴스와 YouTube 영상에서 부정적인 이슈가 언급되고 있고, Fear and Greed Index가 '탐욕' 상태로 조정이 예상됩니다. gpt-4o의 차트 분석에서도 단기 하락 가능성이 언급되었습니다."}}
    {{"decision":"hold","reason":"현재 시장 변동성이 높아 관망이 필요합니다. 주요 지표들이 명확한 신호를 제공하지 않고 있으며, 최근 뉴스와 YouTube 영상에서도 상반된 의견이 제시되고 있습니다. Fear and Greed Index가 중립 상태이며, gpt-4o의 차트 분석에서도 뚜렷한 추세가 보이지 않아 현 포지션 유지가 권장됩니다."}}
    """

    response = client.chat.completions.create(
        model="gpt-4o",
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

    result = response.choices[0].message.content

    # AI의 판단에 따라 자동매매 진행
    response_content = response.choices[0].message.content.strip()

    # 우선 응답 내용 출력 (디버깅 용도)
    # print("응답 내용:", response_content)

    # '```json'과 '```'을 제거
    if response_content.startswith("```json") and response_content.endswith("```"):
        response_content = response_content.replace("```json", "").replace("```", "").strip()

    # 이제 JSON으로 파싱 시도
    if response_content.startswith("{") and response_content.endswith("}"):
        try:
            # JSON 파싱 시도
            result_json = json.loads(response_content)
            print("### AI Decision: ", result_json["decision"].upper(), "###")
            print(f"### Reason: {result_json['reason']} ###")
        except json.JSONDecodeError as e:
            print("JSON 파싱 에러 발생:", e)
            print("AI의 응답이 JSON 형식이 아닙니다. 응답 내용:")
            print(response_content)
    else:
        print("AI 응답이 JSON 형식이 아닙니다. 응답 내용을 수동으로 처리해야 합니다.")
        print(response_content)
   
    # 매수/매도 금액 설정 (real)
    # buy_amount = 5000  # 매수 금액 5,000원
    # sell_amount = 5000  # 매도 시 5,000원어치 BTC 판매
    
    # 매수/매도 금액 설정 (test)
    buy_amount = 0
    sell_amount = 0

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