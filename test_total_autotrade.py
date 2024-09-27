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
import openai
from openai import OpenAI
from openai import RateLimitError, OpenAIError
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
    client = OpenAI(api_key=os.getenv(key="OPENAI_API_KEY"))

    analysis_results = {}

    for chart_type, base64_image in screenshots.items():
        prompt = f"이 비트코인 차트는 {chart_type} 설정의 스크린샷입니다. 이 차트를 분석하고, 현재 시장 상황과 향후 단기 트렌드에 대해 설명해주세요. 또한 이 차트를 바탕으로 매수/매도/홀드 중 어떤 행동을 취해야 할지 제안해주세요."

        try:
            response = client.chat.completions.create(
                model="gpt-4o-2024-08-06",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{base64_image}"}}
                        ]
                    }
                ],
                max_tokens=4095
            )
            analysis_results[chart_type] = response.choices[0].message.content
        except Exception as e:
            logger.error(f"GPT-4o API 요청 중 오류 발생 ({chart_type}): {e}")
            analysis_results[chart_type] = "분석 실패"

    return analysis_results

def get_full_transcript(video_id):
    try:
        # Get the transcript data
        transcript_data = YouTubeTranscriptApi.get_transcript(video_id, languages=['ko'])

        # Extract and concatenate all text items
        full_transcript = ' '.join(item['text'] for item in transcript_data)

        return full_transcript
    except Exception as e:
        logger.error(f"유튜브 자막 가져오기 실패 (video_id: {video_id}): {e}")
        return None

def ai_trading():
    access = os.getenv("UPBIT_ACCESS_KEY")
    secret = os.getenv("UPBIT_SECRET_KEY")
    client = OpenAI(api_key=os.getenv(key="OPENAI_API_KEY"))

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
    video_ids = ["3XbtEX3jUv4"]  # 워뇨띠님의 영상 ID
    youtube_transcripts = []
    for video_id in video_ids:
        transcript = get_full_transcript(video_id)
        if transcript:
            youtube_transcripts.append(transcript)

    # 워뇨띠님의 매매법을 시스템 메시지에 포함
    wonyotti_strategy = youtube_transcripts[0] if youtube_transcripts else "워뇨띠님의 매매법 데이터를 가져오지 못했습니다."

    data = {
        "daily_ohlcv": df_daily_selected.to_dict(),
        "hourly_ohlcv": df_hourly_selected.to_dict(),
        "orderbook": orderbook,
        "balance": filtered_balance,
        "fear_and_greed_index": fng,
        "news_headlines": news_headlines,
        "chart_analysis": chart_analysis
    }

    # JSON 직렬화
    data_json = json.dumps(data)

    # 프롬프트 작성 및 GPT-4o 요청
    system_message = f"""
    당신은 비트코인 투자 전문가이자 퀀트 트레이더입니다.
    항상 아래의 워뇨띠님의 매매법을 참고하여 현재 상황을 파악하고 매매 결정을 내려야 합니다:

    {wonyotti_strategy}

    제공된 데이터 (현재 투자 상태, 호가 데이터, 보조지표가 포함된 60일 일봉 OHLCV, 보조지표가 포함된 100시간 시간봉 OHLCV, Fear and Greed Index, 최신 뉴스 헤드라인, gpt-4o의 차트 분석 결과)를 분석하여,
    RSI, MACD, 이동평균선 등의 기술적 지표와 시장 심리 지표인 Fear and Greed Index, 최신 뉴스 헤드라인, gpt-4o의 차트 분석 결과를 종합적으로 고려하되, 반드시 워뇨띠님의 매매법을 기반으로 현재 시점에서 매수, 매도, 보류 중 무엇을 할지 판단해 주세요.
    매수 또는 매도 결정을 내릴 경우, 보유한 KRW 중 몇 퍼센트를 매수할지 또는 보유한 BTC 중 몇 퍼센트를 매도할지 `percentage` 필드에 명시해 주세요. (0에서 100 사이의 정수)
    판단 근거를 상세히 설명하고, 수익률을 높일 수 있는 전략을 제시하세요. 특히 워뇨띠님의 매매법과 현재 상황을 어떻게 연관지었는지 설명해주세요.
    JSON 형식으로 응답하되, 반드시 한국어로 작성해 주세요.

    현재 Fear and Greed Index 값은 {fng['value']}이며, 이는 '{fng['classification']}' 상태를 나타냅니다.

    최신 뉴스 헤드라인은 다음과 같습니다 (각 뉴스는 'title'과 'date'를 포함합니다):
    {news_headlines}

    gpt-4o의 차트 분석 결과:
    1시간 차트: {chart_analysis['1hour']}
    30분 차트: {chart_analysis['30min']}
    볼린저 밴드: {chart_analysis['bollinger']}

    응답 예시:
    {{"decision":"buy","percentage":10,"reason":"워뇨띠님의 매매법에 따르면 [구체적인 설명]. 현재 RSI가 과매도 영역에서 상승 반전했고, MACD가 골든크로스를 형성하였습니다. 또한 최근 뉴스에서 긍정적인 전망이 제시되고 있고, Fear and Greed Index가 '공포' 상태로 반등 가능성이 있습니다. gpt-4o의 차트 분석에서도 단기 상승 추세가 예상됩니다."}}
    {{"decision":"sell","percentage":20,"reason":"워뇨띠님의 매매법에 따르면 [구체적인 설명]. 현재 RSI가 과매수 상태이고, MACD 히스토그램이 감소 추세입니다. 또한 최근 뉴스에서 부정적인 이슈가 언급되고 있고, Fear and Greed Index가 '탐욕' 상태로 조정이 예상됩니다. gpt-4o의 차트 분석에서도 단기 하락 가능성이 언급되었습니다."}}
    {{"decision":"hold","percentage":0,"reason":"워뇨띠님의 매매법에 따르면 [구체적인 설명]. 현재 시장 변동성이 높아 관망이 필요합니다. 주요 지표들이 명확한 신호를 제공하지 않고 있으며, 최근 뉴스에서도 상반된 의견이 제시되고 있습니다. Fear and Greed Index가 중립 상태이며, gpt-4o의 차트 분석에서도 뚜렷한 추세가 보이지 않아 현 포지션 유지가 권장됩니다."}}
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4o-2024-08-06",  # 최신 지원 모델명 사용
            messages=[
                {
                    "role": "system",
                    "content": system_message
                },
                {
                    "role": "user",
                    "content": data_json
                }
            ],
            temperature=0,
            max_tokens=4095,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0,
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": "TradingDecision",
                    "description": "Decision to buy, sell, or hold based on analysis, including confidence percentage",
                    "strict": True,
                    "schema": {
                        "type": "object",
                        "properties": {
                            "decision": {
                                "type": "string",
                                "enum": ["buy", "sell", "hold"]
                            },
                            "percentage": {
                                "type": "integer",
                                "description": "Confidence level of the decision (0-100)"
                            },
                            "reason": {
                                "type": "string"
                            }
                        },
                        "required": ["decision", "percentage", "reason"],
                        "additionalProperties": False
                    }
                }
            }
        )

        response_content = response.choices[0].message.content
        trading_decision = json.loads(response_content)
    
        # 필수 필드 확인 및 percentage 유효성 검증
        required_fields = {"decision", "percentage", "reason"}
        if not isinstance(trading_decision, dict) or not required_fields.issubset(trading_decision.keys()):
            logger.error("GPT 응답이 예상한 형식이 아닙니다. 기본값으로 설정합니다.")
            trading_decision = {"decision": "hold", "percentage": 0, "reason": "분석 실패 - 잘못된 응답 형식"}

        percentage = trading_decision.get("percentage", 0)
        if not isinstance(percentage, (int, float)) or not (0 <= percentage <= 100):
            logger.error("GPT 응답의 percentage 값이 유효하지 않습니다. 기본값으로 설정합니다.")
            trading_decision["percentage"] = 0

    except json.JSONDecodeError:
        logger.error("GPT 응답을 JSON으로 파싱할 수 없습니다.")
        trading_decision = {"decision": "hold", "percentage": 0, "reason": "분석 실패 - JSON 파싱 오류"}
    except RateLimitError as e:
        logger.error(f"GPT-4o API 요청 중 오류 발생: {e}")
        trading_decision = {"decision": "hold", "percentage": 0, "reason": "분석 실패 - Rate limit exceeded"}
    except OpenAIError as e:
        logger.error(f"GPT-4o API 요청 중 오류 발생: {e}")
        trading_decision = {"decision": "hold", "percentage": 0, "reason": "분석 실패"}
    except Exception as e:
        logger.error(f"예기치 않은 오류 발생: {e}")
        trading_decision = {"decision": "hold", "percentage": 0, "reason": "분석 실패"}

    # 현재 BTC 가격 가져오기
    current_price = pyupbit.get_current_price("KRW-BTC")
    
    # AI의 판단에 따라 자동매매 진행
    print(f"### Decision: {trading_decision['decision'].upper()} (현재 BTC 가격 : {current_price:,.0f} KRW) ###")
    print(f"### Percentage: {trading_decision['percentage']} ###")
    print(f"### Reason: {trading_decision['reason']} ###")
    result_json = trading_decision

    decision = result_json['decision']
    if decision == "buy":
        # 매수: 보유한 KRW 중 percentage% 매수
        krw_balance = float(upbit.get_balance("KRW"))
        buy_amount = krw_balance * (percentage / 100) * 0.9995  # 수수료 고려

        # 매수 금액이 5,000 KRW 이상인지 확인
        if buy_amount >= 5000:
            if krw_balance >= buy_amount:
                try:
                    # 실제 매수 주문 실행
                    # upbit.buy_market_order("KRW-BTC", buy_amount)
                    
                    # 매수한 BTC 수량 계산 (현재 가격 기준)
                    btc_bought = buy_amount / current_price

                    logger.info(f"매수 성공: {buy_amount:.2f} KRW 매수 완료 - {btc_bought:.6f} BTC 매수")
                    print(f"buy: {result_json['reason']} - {percentage}% 매수 - 매수 금액: {buy_amount:.2f} KRW - 매수된 BTC: {btc_bought:.6f} BTC")
                except Exception as e:
                    logger.error(f"매수 주문 중 오류 발생: {e}")
                    print(f"매수 주문 중 오류 발생: {e}")
            else:
                logger.warning("매수할 금액이 부족합니다.")
                print("매수할 금액이 부족합니다.")
        else:
            logger.warning(f"매수 금액이 최소 5,000 KRW 미만입니다. 매수를 건너뜁니다. (매수 금액: {buy_amount:.2f} KRW)")
            print(f"매수 금액이 최소 5,000 KRW 미만입니다. 매수를 건너뜁니다. (매수 금액: {buy_amount:.2f} KRW)")

    elif decision == "sell":
        # 매도: 보유한 BTC 중 percentage% 매도
        btc_balance = float(upbit.get_balance("BTC"))
        btc_to_sell = btc_balance * (percentage / 100)

        # 매도 금액이 5,000 KRW 이상인지 확인
        sell_value = btc_to_sell * current_price
        if sell_value >= 5000:
            if btc_balance >= btc_to_sell:
                try:
                    # 실제 매도 주문 실행
                    # upbit.sell_market_order("KRW-BTC", btc_to_sell)
                    
                    logger.info(f"매도 성공: {btc_to_sell:.6f} BTC 매도 완료 - {sell_value:,.2f} KRW 매도")
                    print(f"sell: {result_json['reason']} - {percentage}% 매도 - 매도 수량: {btc_to_sell:.6f} BTC - 매도 금액: {sell_value:,.2f} KRW")
                except Exception as e:
                    logger.error(f"매도 주문 중 오류 발생: {e}")
                    print(f"매도 주문 중 오류 발생: {e}")
            elif btc_balance > 0:
                # 모든 BTC를 매도하되, 최소 매도 금액을 충족하는지 확인
                total_sell_value = btc_balance * current_price
                if total_sell_value >= 5000:
                    try:
                        # 실제 매도 주문 실행
                        # upbit.sell_market_order("KRW-BTC", btc_balance)
                        
                        logger.info("매도 성공: 보유한 모든 비트코인을 매도했습니다.")
                        print("매도: 보유한 모든 비트코인을 매도했습니다. - 매도 금액: {:,.2f} KRW".format(total_sell_value))
                    except Exception as e:
                        logger.error(f"매도 주문 중 오류 발생: {e}")
                        print(f"매도 주문 중 오류 발생: {e}")
                else:
                    logger.warning(f"보유한 모든 비트코인의 가치가 최소 5,000 KRW 미만입니다. 매도를 건너뜁니다. (매도 가치: {total_sell_value:,.2f} KRW)")
                    print(f"보유한 모든 비트코인의 가치가 최소 5,000 KRW 미만입니다. 매도를 건너뜁니다. (매도 가치: {total_sell_value:,.2f} KRW)")
        else:
            logger.warning(f"매도 금액이 최소 5,000 KRW 미만입니다. 매도를 건너뜁니다. (매도 금액: {sell_value:,.2f} KRW)")
            print(f"매도 금액이 최소 5,000 KRW 미만입니다. 매도를 건너뜁니다. (매도 금액: {sell_value:,.2f} KRW)")
            
    elif decision == "hold":
        # 보류
        logger.info(f"decision(매매 보류): {result_json['reason']}")
        print("percentage:", result_json['percentage'])
        print("reason:", result_json['reason'])
    else:
        logger.error(f"알 수 없는 결정입니다: {result_json['decision']}")
        print("percentage:", result_json['percentage'])
        print("reason(알 수 없는 결정입니다):", result_json['decision'])

if __name__ == "__main__":
    while True:
        import time
        ai_trading()
        time.sleep(300)  # 5분마다 실행