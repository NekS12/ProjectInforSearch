import requests


def search_wb(query):
    url = "https://search.wb.ru/exactmatch/ru/common/v5/search"
    params = {
        "ab_testing": "false",
        "appType": 1,
        "curr": "rub",
        "dest": "-1257786",
        "query": query,
        "resultset": "catalog",
        "sort": "popular",
        "spp": "30",
        "suppressSpellcheck": "false"
    }
    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    try:
        response = requests.get(url, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()

        products = []
        if 'data' in data and 'products' in data['data']:
            for product in data['data']['products'][:10]:  # первые 10 товаров
                name = product.get('name', 'Без названия')

                # Логируем, что приходит в sizes
                sizes = product.get('sizes', [])
                if sizes:
                    size = sizes[0]
                    price = size.get('price', {}).get('total', 0) / 100  # получаем полную цену и делим на 100
                else:
                    price = 0

                # Получаем рейтинг товара
                rating = product.get('reviewRating') or product.get('rating') or 0

                print(f"Товар '{name}': Цена — {price} ₽, Рейтинг — {rating} ⭐")  # Логируем цену и рейтинг

                link = f"https://www.wildberries.ru/catalog/{product['id']}/detail.aspx"
                image = f"https://images.wbstatic.net/c516x688/{product['id']}.jpg"

                # Добавляем продукт в список
                products.append((name, price, rating, link, "Wildberries", image))

        return products

    except Exception as e:
        print(f"Ошибка поиска на Wildberries: {e}")
        return []
