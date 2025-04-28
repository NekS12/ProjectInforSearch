import asyncio
import os
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, BufferedInputFile
from dotenv import load_dotenv
from database import init_db, add_search
from parser_dns import search_dns
from parser_ozon import search_ozon
from parser_wb import search_wb
from parser_yandex import search_yandex
from bs4 import BeautifulSoup
import requests
import aiohttp
from io import BytesIO
from urllib.parse import urljoin
import re


load_dotenv()

bot = Bot(token=os.getenv("BOT_TOKEN"))
dp = Dispatcher()

user_choices = {}

platforms = {
    "DNS": search_dns,
    "Ozon": search_ozon,
    "Wildberries": search_wb,
    "Yandex Market": search_yandex
}


def platform_keyboard():
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🛒 Все площадки(В разработке)", callback_data="all")],
        [InlineKeyboardButton(text="💬 DNS(В разработке)", callback_data="DNS")],
        [InlineKeyboardButton(text="💬 Ozon(В разработке)", callback_data="Ozon")],
        [InlineKeyboardButton(text="💬 Wildberries", callback_data="Wildberries")],
        [InlineKeyboardButton(text="💬 Yandex Market(В разработке)", callback_data="Yandex Market")],
        [InlineKeyboardButton(text="🌐 Своя ссылка", callback_data="custom_link")]
    ])
    return kb


def back_keyboard():
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Новый поиск", callback_data="new_search")]
    ])
    return kb

#------------------------------------------------------
def clean_text(text):
    # Убираем всё в квадратных скобках: [править], [1], [2] и т.п.
    text = re.sub(r'\[[^\]]*\]', '', text)

    # Убираем ненужные служебные слова
    service_phrases = [
        "Перейти к навигации", "Перейти к поиску",
        "править", "править код",
        "Материал из Википедии — свободной энциклопедии",
        "Текущая версия страницы пока не проверялась опытными участниками"
    ]
    for phrase in service_phrases:
        text = text.replace(phrase, "")

    # Убираем повторяющиеся пустые строки
    text = re.sub(r'\n\s*\n', '\n', text)

    # Убираем одиночные буквы (H G Я O) по отдельности
    text = re.sub(r'\b[HGOЯ]\b', '', text)

    # Убираем лишние пробелы
    text = re.sub(r' +', ' ', text)

    # Убираем пробелы в начале строк
    text = re.sub(r'^\s+', '', text, flags=re.MULTILINE)

    # Убираем несколько подряд идущих переводов строк
    text = re.sub(r'\n{2,}', '\n\n', text)

    return text.strip()


def parse_custom_link(url):
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code != 200:
            return None

        soup = BeautifulSoup(response.text, "html.parser")
        title = soup.title.string.strip() if soup.title else "Без названия"

        img_tags = soup.find_all("img")
        images = []
        for img in img_tags:
            src = img.get("src")
            if src:
                full_url = urljoin(url, src)
                images.append(full_url)

        description = soup.body.get_text(strip=True) if soup.body else "Нет текста"

        return title, images, description
    except Exception as e:
        print(f"Ошибка парсинга ссылки: {e}")
        return None


async def download_image(url: str) -> BytesIO | None:
    try:
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
            async with session.get(url) as resp:
                if resp.status == 200 and resp.content_type.startswith('image'):
                    img_data = await resp.read()
                    return BytesIO(img_data)
    except Exception as e:
        print(f"Ошибка загрузки изображения: {e}")
    return None


@dp.message(CommandStart())
async def start(message: Message):
    await message.answer(
        "👋 Привет!\nВыберите площадку для поиска товара:",
        reply_markup=platform_keyboard()
    )


@dp.callback_query()
async def callbacks(callback: types.CallbackQuery):
    await callback.message.delete()

    if callback.data == "new_search":
        await callback.message.answer(
            "👋 Выберите площадку для поиска товара:",
            reply_markup=platform_keyboard()
        )
    else:
        user_choices[callback.from_user.id] = callback.data
        if callback.data == "custom_link":
            await callback.message.answer("🌐 Отправьте ссылку для парсинга сайта:")
        else:
            await callback.message.answer("💬 Теперь введите название товара:")


@dp.message()
async def search(message: Message):
    user_id = message.from_user.id
    platform = user_choices.get(user_id)

    if not platform:
        await message.answer("💬 Сначала выберите площадку через /start.")
        return

    query = message.text
    await message.answer("⏳ Ищу товар...")

    if platform == "custom_link":
        result = parse_custom_link(query)
        if result:
            title, images, description = result
            text = f"🛒 {title}\n\n{description[:4000]}"  # Без ссылки, только текст

            # Сначала отправляем текст
            cleaned_text = clean_text(text)
            await message.answer(cleaned_text)

            # Потом картинки (если есть)
            if images:
                for image_url in images[:5]:  # максимум 5 картинок
                    image_file = await download_image(image_url)
                    if image_file:
                        image_file.seek(0)
                        await message.answer_photo(
                            photo=BufferedInputFile(image_file.read(), filename="site_image.jpg")
                        )

                    await asyncio.sleep(0.2)
            else:
                await message.answer("📄 На сайте не найдено изображений.")
        else:
            await message.answer("😕 Не удалось спарсить сайт. Проверьте ссылку.", reply_markup=back_keyboard())

        await message.answer("🔍 Хотите начать новый поиск?", reply_markup=back_keyboard())
        return

    all_results = []

    if platform == "all":
        for func in platforms.values():
            try:
                data = func(query)
                if data:
                    all_results.extend(data)
            except Exception as e:
                print(f"Ошибка парсинга: {e}")
    else:
        try:
            func = platforms.get(platform)
            if func:
                data = func(query)
                if data:
                    all_results.extend(data)
        except Exception as e:
            print(f"Ошибка парсинга: {e}")

    if all_results:
        all_results.sort(key=lambda x: x[1])

        await message.answer(f"🛒 Найдено {len(all_results)} товаров!\n🔥 Вывожу отсортировано по цене:")

        for idx, product in enumerate(all_results, start=1):
            if len(product) == 6:
                name, price, rating, link, source, image = product
            else:
                name, price, link, source, image = product
                rating = 0  # если парсер не передал рейтинг

            kb = InlineKeyboardMarkup(
                inline_keyboard=[[InlineKeyboardButton(text="🔗 Перейти к товару", url=link)]]
            )

            rating_text = f"⭐ Оценка: {rating}" if rating else "⭐ Оценка: Нет отзывов"
            text = (
                f"{idx}. 🛒 {name}\n"
                f"🔥 Цена: {price} ₽\n"
                f"{rating_text}\n"
                f"💬 Площадка: {source}"
            )

            if image:
                image_file = await download_image(image)
                if image_file:
                    image_file.seek(0)
                    await message.answer_photo(
                        photo=BufferedInputFile(image_file.read(), filename="site_image.jpg"),
                        caption=text,
                        reply_markup=kb
                    )
                else:
                    cleaned_text = clean_text(text)
                    await message.answer(cleaned_text, reply_markup=kb)
            else:
                cleaned_text = clean_text(text)
                await message.answer(cleaned_text, reply_markup=kb)

            await asyncio.sleep(0.3)
        # 💤 Небольшая задержка между отправками для стабильности

        add_search(query, all_results[0][0], all_results[0][1])
        await message.answer("🔍 Хотите начать новый поиск?", reply_markup=back_keyboard())
    else:
        await message.answer("😕 Не удалось найти товар.\nПопробуйте другое название.", reply_markup=back_keyboard())


async def main():
    init_db()
    await dp.start_polling(bot, polling_timeout=60)


if __name__ == "__main__":
    asyncio.run(main())
