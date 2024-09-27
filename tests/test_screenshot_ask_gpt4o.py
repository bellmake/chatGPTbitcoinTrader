from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
import time
from PIL import Image
import io

# 크롬 옵션 설정
chrome_options = Options()
chrome_options.add_argument("--start-maximized")  # 브라우저 최대화

# 웹 드라이버 실행 (자동으로 최신 chromedriver 다운로드 및 설정)
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

# 원하는 웹사이트로 이동
url = "https://upbit.com/full_chart?code=CRIX.UPBIT.KRW-BTC"
driver.get(url)

# 페이지가 로딩될 시간을 기다림
time.sleep(5)

# 현재 화면에 보이는 영역을 캡처
screenshot = driver.get_screenshot_as_png()

# 스크린샷 이미지를 파일로 저장
screenshot_image = Image.open(io.BytesIO(screenshot))
screenshot_image.save("upbit_visible_page_screenshot.png")

# 브라우저 종료
driver.quit()
