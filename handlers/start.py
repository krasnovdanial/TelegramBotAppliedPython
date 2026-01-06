from aiogram import Router, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from db.requests import set_user
from utils.api import get_weather_temp
from utils.states import ProfileSetup

router = Router()


@router.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer("Привет! Я помогу вам следить за здоровьем.\nНачни с настройки своего профиля: /set_profile")


@router.message(Command("set_profile"))
async def cmd_set_profile(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("Как к вам обращаться?")
    await state.set_state(ProfileSetup.name)


@router.message(ProfileSetup.name)
async def process_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)

    await message.answer(f"Приятно познакомиться, {message.text}! Введите ваш вес (в кг):")
    await state.set_state(ProfileSetup.weight)


@router.message(ProfileSetup.weight)
async def process_weight(message: types.Message, state: FSMContext):
    try:
        await state.update_data(weight=float(message.text))
        await message.answer("Введите ваш рост (в см):")
        await state.set_state(ProfileSetup.height)
    except ValueError:
        await message.answer("Введите число.")


@router.message(ProfileSetup.height)
async def process_height(message: types.Message, state: FSMContext):
    try:
        await state.update_data(height=float(message.text))
        await message.answer("Введите ваш возраст:")
        await state.set_state(ProfileSetup.age)
    except ValueError:
        await message.answer("Введите число.")


@router.message(ProfileSetup.age)
async def process_age(message: types.Message, state: FSMContext):
    try:
        await state.update_data(age=int(message.text))
        await message.answer("Сколько минут активности в день?")
        await state.set_state(ProfileSetup.activity)
    except ValueError:
        await message.answer("Введите число.")


@router.message(ProfileSetup.activity)
async def process_activity(message: types.Message, state: FSMContext):
    try:
        await state.update_data(activity=int(message.text))
        await message.answer("В каком городе вы находитесь?")
        await state.set_state(ProfileSetup.city)
    except ValueError:
        await message.answer("Введите число.")


@router.message(ProfileSetup.city)
async def process_city(message: types.Message, state: FSMContext):
    city = message.text.strip().title()
    data = await state.get_data()
    name = data.get('name', 'Пользователь')

    weight = data['weight']
    height = data['height']
    age = data['age']
    act = data['activity']

    checking_msg = await message.answer(f"Проверяю погоду в городе {city}...")
    temp = await get_weather_temp(city)

    water_goal = weight * 30 + (act // 30) * 500

    weather_info = ""
    if temp is not None:
        if temp > 25:
            water_goal += 500
            weather_info = f"В городе {city} сейчас жарко ({temp}°C). Добавлено +500 мл воды."
        else:
            weather_info = f"В городе {city} сейчас {temp}°C. Норма воды стандартная."
    else:
        weather_info = "Не удалось получить данные о погоде. Норма воды стандартная."

    await checking_msg.delete()

    calorie_goal = 10 * weight + 6.25 * height - 5 * age + (act * 5)

    await set_user(message.from_user.id, {
        "name": name, "weight": weight, "height": height, "age": age, "activity": act, "city": city,
        "water_goal": water_goal, "calorie_goal": calorie_goal
    })

    await message.answer(
        f"Ваш профиль настроен, {name}!\n"
        f"{weather_info}\n"
        f"Цель по воде: {int(water_goal)} мл\n"
        f"Цель по калориям: {int(calorie_goal)} ккал"
    )
    await state.clear()
