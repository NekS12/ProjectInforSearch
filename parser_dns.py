import requests

def search_dns(query):
    try:
        # 1. Формируем ссылку на API поиска товаров
        url = f"https://search.api.dns-shop.ru/search/v1/api/search?text={query}&cityId=239"

        headers = {
            "User-Agent": "Mozilla/5.0",
            "Accept": "application/json",
        }

        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code != 200:
            return []

        data = response.json()

        results = []

        # 2. Проходим по найденным товарам
        for product in data.get("data", {}).get("products", []):
            name = product.get("name")
            price = product.get("price")
            product_link = f"https://www.dns-shop.ru{product.get('link', '')}"
            image_url = product.get("imageUrl")  # это относительный путь

            # Делаем полный URL картинки
            if image_url:
                image_url = f"https://cdn.dns-shop.ru{image_url}"

            results.append((name, price, product_link, "DNS", image_url))

        return results
    except Exception as e:
        print(f"Ошибка поиска на DNS: {e}")
        return []
