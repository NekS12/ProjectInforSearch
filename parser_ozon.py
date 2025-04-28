from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import random
import time


def create_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Запуск без графического интерфейса
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")  # Важно для некоторых сайтов!
    return webdriver.Chrome(service=ChromeDriverManager().install(), options=chrome_options)


def search_ozon(query):
    driver = create_driver()
    try:
        # Сформировать URL для поиска на Озоне
        search_url = f"https://www.ozon.ru/search/?text={query.replace(' ', '+')}"
        driver.get(search_url)

        # Добавляем случайную задержку перед загрузкой страницы
        time.sleep(random.uniform(1, 3))  # Задержка от 1 до 3 секунд

        # Даем странице время для загрузки контента
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "tile-hover-target"))
        )

        # Парсим страницу
        soup = BeautifulSoup(driver.page_source, "html.parser")
        products = soup.find_all("div", class_="tile-hover-target", limit=5)

        if not products:
            return []

        results = []

        # Обрабатываем найденные товары
        for product in products:
            name_tag = product.find("span", {"data-test-id": "tile-name"})
            price_tag = product.find("span", {"data-test-id": "tile-price"})
            link_tag = product.find("a", href=True)
            image_tag = product.find("img")

            if name_tag and price_tag and link_tag:
                name = name_tag.text.strip()
                price_text = price_tag.text.strip().replace(' ', '').replace('₽', '')
                try:
                    price = int(price_text)
                except ValueError:
                    price = 0
                link = "https://ozon.ru" + link_tag['href']
                image_url = image_tag['src'] if image_tag else None

                results.append((name, price, link, "Ozon", image_url))

        return results
    except (TimeoutException, WebDriverException) as e:
        print(f"Ошибка при парсинге Озона: {e}")
        return []
    finally:
        driver.quit()
