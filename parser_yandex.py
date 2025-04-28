from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup

def create_driver():
    chrome_options = Options()
    #chrome_options.add_argument("--headless=new")  # Новый режим headless
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")  # Важно для некоторых сайтов!
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=chrome_options)


def search_yandex(query):
    driver = create_driver()
    try:
        driver.get(f"https://market.yandex.ru/search?text={query.replace(' ', '+')}")

        # Ждём максимум 10 секунд, пока появится хотя бы один товар
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "article"))
        )

        soup = BeautifulSoup(driver.page_source, "html.parser")
        products = soup.find_all("article", limit=5)

        if not products:
            return []

        results = []
        for product in products:
            name_tag = product.find("h3")
            price_tag = product.find("span", {"data-auto": "price-value"})
            link_tag = product.find("a", href=True)
            image_tag = product.find("img")

            if name_tag and price_tag and link_tag:
                name = name_tag.text.strip()
                price = price_tag.text.strip().replace(' ', '').replace('₽', '')
                link = "https://market.yandex.ru" + link_tag['href']
                image_url = image_tag['src'] if image_tag else None

                results.append((name, int(price), link, "Yandex Market", image_url))

        return results
    finally:
        driver.quit()
