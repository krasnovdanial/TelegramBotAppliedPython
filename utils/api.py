import os

import aiohttp
from deep_translator import GoogleTranslator
from dotenv import load_dotenv

load_dotenv()
WEATHER_KEY = os.getenv('WEATHER_KEY')
NINJA_KEY = os.getenv('CALORIE_NINJA')


async def get_weather_temp(city: str):
    if not WEATHER_KEY: return None
    url = "https://api.openweathermap.org/data/2.5/weather"

    params = {
        'q': city,
        'appid': WEATHER_KEY,
        'units': 'metric',
        'lang': 'ru'
    }

    async with aiohttp.ClientSession() as session:
        async with session.get(url, params=params) as response:
            if response.status == 200:
                data = await response.json()
                return data['main']['temp']
            return None


async def get_food_info(product_input: str):
    if not NINJA_KEY:
        print("Ошибка: Нет NINJA_KEY")
        return None, None, None

    try:
        translator = GoogleTranslator(source='auto', target='en')
        translated_query = translator.translate(product_input)
    except Exception:
        translated_query = product_input

    url = f"https://api.calorieninjas.com/v1/nutrition?query={translated_query}"
    headers = {'X-Api-Key': NINJA_KEY}

    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            if response.status == 200:
                data = await response.json()
                items = data.get('items', [])

                if items:
                    total_cals = 0
                    total_grams = 0
                    names = []

                    for item in items:
                        total_cals += item['calories']
                        total_grams += item['serving_size_g']
                        names.append(item['name'])

                    product_name = ", ".join(names)

                    if total_grams == 0: total_grams = 100

                    kcal_per_100g = (total_cals / total_grams) * 100

                    return product_name, kcal_per_100g, True

            return None, None, None
