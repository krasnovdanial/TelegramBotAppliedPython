import os

import aiohttp
from dotenv import load_dotenv

load_dotenv()
WEATHER_KEY = os.getenv('WEATHER_KEY')


async def get_weather_temp(city: str):
    if not WEATHER_KEY: return None
    url = "http://api.openweathermap.org/data/2.5/weather"

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


async def get_food_info(product_name: str):
    url = f"https://world.openfoodfacts.org/cgi/search.pl?action=process&search_terms={product_name}&json=1&page_size=5"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status == 200:
                data = await response.json()
                products = data.get('products', [])
                for product in products:
                    name = product.get('product_name', 'Неизвестно')
                    nutriments = product.get('nutriments', {})
                    kcal = nutriments.get('energy-kcal_100g') or nutriments.get('energy-kcal')
                    if kcal and float(kcal) > 0:
                        return name, float(kcal)
            return None, None
