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

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 크롬 옵션 설정
chrome_options = Options()
chrome_options.add_argument("--start-maximized")  # 브라우저 최대화

# 웹 드라이버 실행 (자동으로 최신 chromedriver 다운로드 및 설정)
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

# 원하는 웹사이트로 이동
url = "https://upbit.com/full_chart?code=CRIX.UPBIT.KRW-BTC"
driver.get(url)

# 페이지가 로딩될 시간을 3초로 설정
time.sleep(3)

# 1. 첫 페이지의 전체 스크린샷 촬영 및 저장
try:
    logger.info("첫 페이지 전체 스크린샷 촬영 중...")
    screenshot = driver.get_screenshot_as_png()

    # 스크린샷 이미지를 파일로 저장
    screenshot_image = Image.open(io.BytesIO(screenshot))
    first_screenshot_path = "upbit_btc_full_chart_original.png"
    screenshot_image.save(first_screenshot_path)
    logger.info("첫 페이지 스크린샷이 성공적으로 저장되었습니다: %s", first_screenshot_path)
except Exception as e:
    logger.error("첫 페이지 스크린샷 저장 중 오류가 발생했습니다: %s", e)

# 2. '1시간' 옵션 선택 및 스크린샷 촬영
try:
    # 메뉴 버튼 클릭
    logger.info("메뉴 버튼 클릭 중...")
    menu_button_xpath = '/html/body/div[1]/div[3]/div[3]/span/div/div/div[1]/div/div/cq-menu[1]'
    menu_button = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, menu_button_xpath))
    )
    menu_button.click()
    logger.info("메뉴 버튼 클릭 완료")

    # '1시간' 옵션 선택
    logger.info("'1시간' 옵션 선택 중...")
    one_hour_option_xpath = '/html/body/div[1]/div[3]/div[3]/span/div/div/div[1]/div/div/cq-menu[1]/cq-menu-dropdown/cq-item[8]'
    one_hour_option = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, one_hour_option_xpath))
    )
    one_hour_option.click()
    logger.info("1시간 옵션 선택 완료")

    # '1시간' 옵션 선택 후의 스크린샷 촬영 및 저장
    logger.info("1시간 옵션 선택 후 스크린샷 촬영 중...")
    screenshot = driver.get_screenshot_as_png()

    # 스크린샷 이미지를 파일로 저장
    screenshot_image = Image.open(io.BytesIO(screenshot))
    one_hour_screenshot_path = "upbit_btc_full_chart_1hour.png"
    screenshot_image.save(one_hour_screenshot_path)
    logger.info("1시간 옵션 선택 후 스크린샷이 성공적으로 저장되었습니다: %s", one_hour_screenshot_path)
except Exception as e:
    logger.error("1시간 옵션 선택 후 스크린샷 저장 중 오류가 발생했습니다: %s", e)

# 3. '지표' 메뉴 클릭 및 '볼린저 밴드' 선택 후 스크린샷 촬영
try:
    # '지표' 메뉴 클릭
    logger.info("지표 메뉴 클릭 중...")
    indicator_menu_xpath = '/html/body/div[1]/div[3]/div[3]/span/div/div/div[1]/div/div/cq-menu[3]'
    indicator_menu = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, indicator_menu_xpath))
    )
    indicator_menu.click()
    logger.info("지표 메뉴 클릭 완료")

    # '볼린저 밴드' 옵션 선택
    logger.info("'볼린저 밴드' 옵션 선택 중...")
    bollinger_band_option_xpath = '/html/body/div[1]/div[3]/div[3]/span/div/div/div[1]/div/div/cq-menu[3]/cq-menu-dropdown/cq-scroll/cq-studies/cq-studies-content/cq-item[15]'
    bollinger_band_option = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, bollinger_band_option_xpath))
    )
    bollinger_band_option.click()
    logger.info("볼린저 밴드 옵션 선택 완료")

    # '볼린저 밴드' 옵션 선택 후의 스크린샷 촬영 및 저장
    logger.info("볼린저 밴드 옵션 선택 후 스크린샷 촬영 중...")
    screenshot = driver.get_screenshot_as_png()

    # 스크린샷 이미지를 파일로 저장
    screenshot_image = Image.open(io.BytesIO(screenshot))
    bollinger_screenshot_path = "upbit_btc_full_chart_1hour_bollinger.png"
    screenshot_image.save(bollinger_screenshot_path)
    logger.info("볼린저 밴드 옵션 선택 후 스크린샷이 성공적으로 저장되었습니다: %s", bollinger_screenshot_path)
except Exception as e:
    logger.error("볼린저 밴드 옵션 선택 후 스크린샷 저장 중 오류가 발생했습니다: %s", e)

# 브라우저 종료
driver.quit()

def capture_chart_screenshots():
    # 크롬 옵션 설정
    chrome_options = Options()
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")

    # 웹 드라이버 실행
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

    # 업비트 차트 페이지로 이동
    url = "https://upbit.com/full_chart?code=CRIX.UPBIT.KRW-BTC"
    driver.get(url)

    # 페이지 로딩 대기
    time.sleep(3)

    screenshots = {}

    try:
        # 1시간 옵션 선택 및 스크린샷
        menu_button_xpath = '/html/body/div[1]/div[3]/div[3]/span/div/div/div[1]/div/div/cq-menu[1]'
        menu_button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, menu_button_xpath)))
        menu_button.click()

        one_hour_option_xpath = '/html/body/div[1]/div[3]/div[3]/span/div/div/div[1]/div/div/cq-menu[1]/cq-menu-dropdown/cq-item[8]'
        one_hour_option = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, one_hour_option_xpath)))
        one_hour_option.click()

        time.sleep(2)
        screenshot = driver.get_screenshot_as_png()
        screenshots['1hour'] = base64.b64encode(screenshot).decode('utf-8')

        # 30분 옵션 선택 및 스크린샷
        menu_button.click()
        thirty_min_option_xpath = '/html/body/div[1]/div[3]/div[3]/span/div/div/div[1]/div/div/cq-menu[1]/cq-menu-dropdown/cq-item[7]'
        thirty_min_option = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, thirty_min_option_xpath)))
        thirty_min_option.click()

        time.sleep(2)
        screenshot = driver.get_screenshot_as_png()
        screenshots['30min'] = base64.b64encode(screenshot).decode('utf-8')

        # 볼린저 밴드 옵션 선택 및 스크린샷
        indicator_menu_xpath = '/html/body/div[1]/div[3]/div[3]/span/div/div/div[1]/div/div/cq-menu[3]'
        indicator_menu = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, indicator_menu_xpath)))
        indicator_menu.click()

        bollinger_band_option_xpath = '/html/body/div[1]/div[3]/div[3]/span/div/div/div[1]/div/div/cq-menu[3]/cq-menu-dropdown/cq-scroll/cq-studies/cq-studies-content/cq-item[15]'
        bollinger_band_option = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, bollinger_band_option_xpath)))
        bollinger_band_option.click()

        time.sleep(2)
        screenshot = driver.get_screenshot_as_png()
        screenshots['bollinger'] = base64.b64encode(screenshot).decode('utf-8')

    except Exception as e:
        logger.error("차트 스크린샷 캡처 중 오류 발생: %s", e)

    # 브라우저 종료
    driver.quit()

    return screenshots