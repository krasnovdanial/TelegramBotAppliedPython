from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove

from db.requests import set_user
from utils.api import get_weather_temp
from utils.states import ProfileSetup

router = Router()


def make_row_keyboard(items = None):
    row = [KeyboardButton(text=item) for item in items] if items else []
    kb = ReplyKeyboardMarkup(
        keyboard=[row, [KeyboardButton(text="Назад"), KeyboardButton(text="Отмена")]],
        resize_keyboard=True
    )
    return kb


@router.message(F.text.lower() == "назад")
async def process_back(message: types.Message, state: FSMContext):
    current_state = await state.get_state()

    if current_state == ProfileSetup.weight:
        await state.set_state(ProfileSetup.name)
        await message.answer("Введите ваше имя:", reply_markup=make_row_keyboard())

    elif current_state == ProfileSetup.height:
        await state.set_state(ProfileSetup.weight)
        await message.answer("Введите ваш вес в кг:", reply_markup=make_row_keyboard())

    elif current_state == ProfileSetup.age:
        await state.set_state(ProfileSetup.height)
        await message.answer("Введите ваш рост в см:", reply_markup=make_row_keyboard())

    elif current_state == ProfileSetup.gender:
        await state.set_state(ProfileSetup.age)
        await message.answer("Введите ваш возраст:", reply_markup=make_row_keyboard())

    elif current_state == ProfileSetup.activity:
        await state.set_state(ProfileSetup.gender)
        await message.answer("Укажите ваш пол:", reply_markup=make_row_keyboard(["Мужской", "Женский"]))

    elif current_state == ProfileSetup.city:
        await state.set_state(ProfileSetup.activity)
        await message.answer("Сколько минут в день вы активны?", reply_markup=make_row_keyboard())

    else:
        await message.answer("Назад идти некуда. Напишите /cancel для отмены.")


@router.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        "Привет! Я помогу вам следить за здоровьем.\n"
        "Начни с настройки своего профиля: /set_profile"
    )


@router.message(Command("cancel"))
@router.message(F.text.lower() == "отмена")
async def cmd_cancel(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "Действие отменено. Возвращаю вас в главное меню.",
        reply_markup=ReplyKeyboardRemove()
    )


@router.message(Command("set_profile"))
async def cmd_set_profile(message: types.Message, state: FSMContext):
    await state.clear()
    kb = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="Отмена")]], resize_keyboard=True)
    await message.answer("Как к вам обращаться?", reply_markup=kb)
    await state.set_state(ProfileSetup.name)


@router.message(ProfileSetup.name)
async def process_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer(
        f"Приятно познакомиться, {message.text}! Введите ваш вес в кг:",
        reply_markup=make_row_keyboard()
    )
    await state.set_state(ProfileSetup.weight)


@router.message(ProfileSetup.weight)
async def process_weight(message: types.Message, state: FSMContext):
    try:
        raw_weight = message.text.replace(',', '.').strip()
        weight = float(raw_weight)

        if weight <= 0:
            await message.answer("Вес должен быть положительным числом.", reply_markup=make_row_keyboard())
            return

        await state.update_data(weight=weight)
        await message.answer(
            "Введите ваш рост в см:",
            reply_markup=make_row_keyboard()
        )
        await state.set_state(ProfileSetup.height)
    except ValueError:
        await message.answer("Пожалуйста, введите корректное число, например: 75.5", reply_markup=make_row_keyboard())


@router.message(ProfileSetup.height)
async def process_height(message: types.Message, state: FSMContext):
    try:
        height = float(message.text.replace(',', '.').strip())
        await state.update_data(height=height)
        await message.answer(
            "Введите ваш возраст:",
            reply_markup=make_row_keyboard()
        )
        await state.set_state(ProfileSetup.age)
    except ValueError:
        await message.answer("Пожалуйста, введите корректное число; рост в см.", reply_markup=make_row_keyboard())


@router.message(ProfileSetup.age)
async def process_age(message: types.Message, state: FSMContext):
    try:
        clean_text = message.text.strip()
        if '.' in clean_text or ',' in clean_text:
            await message.answer("Пожалуйста, введите полных лет - целое число.", reply_markup=make_row_keyboard())
            return

        age = int(clean_text)
        if age < 10 or age > 100:
            await message.answer("Введите реальный возраст от 10 до 100 лет.", reply_markup=make_row_keyboard())
            return

        await state.update_data(age=age)

        await message.answer(
            "Укажите ваш пол:",
            reply_markup=make_row_keyboard(["Мужской", "Женский"])
        )
        await state.set_state(ProfileSetup.gender)

    except ValueError:
        await message.answer("Пожалуйста, введите возраст числом.", reply_markup=make_row_keyboard())


@router.message(ProfileSetup.gender)
async def process_gender(message: types.Message, state: FSMContext):
    gender = message.text.strip()
    if gender not in ["Мужской", "Женский"]:
        await message.answer("Пожалуйста, выберите пол кнопкой ниже.",
                             reply_markup=make_row_keyboard(["Мужской", "Женский"]))
        return

    await state.update_data(gender=gender)

    await message.answer(
        "Сколько минут в день вы активны? Например: 30",
        reply_markup=make_row_keyboard()
    )
    await state.set_state(ProfileSetup.activity)


@router.message(ProfileSetup.activity)
async def process_activity(message: types.Message, state: FSMContext):
    try:
        raw_act = message.text.replace(',', '.').strip()
        activity = int(float(raw_act))

        await state.update_data(activity=activity)
        await message.answer(
            "В каком городе вы находитесь?",
            reply_markup=make_row_keyboard()
        )
        await state.set_state(ProfileSetup.city)
    except ValueError:
        await message.answer("Пожалуйста, введите количество минут числом.", reply_markup=make_row_keyboard())


@router.message(ProfileSetup.city)
async def process_city(message: types.Message, state: FSMContext):
    city = message.text.strip().title()
    checking_msg = await message.answer(f"Проверяю погоду в городе {city}...")

    temp = await get_weather_temp(city)

    if temp is None:
        await checking_msg.delete()
        await message.answer(
            "Не удалось найти такой город. Проверьте название и попробуйте еще раз.",
            reply_markup=make_row_keyboard()
        )
        return

    data = await state.get_data()
    name = data.get('name', 'Пользователь')
    weight = data['weight']
    height = data['height']
    age = data['age']
    act = data['activity']
    gender = data['gender']

    water_goal = weight * 30 + (act // 30) * 500

    weather_info = ""
    if temp > 25:
        water_goal += 500
        weather_info = f"В городе {city} сейчас жарко ({temp}°C). Добавлено +500 мл воды."
    else:
        weather_info = f"В городе {city} сейчас {temp}°C. Норма воды стандартная."

    await checking_msg.delete()

    base_bmr = 10 * weight + 6.25 * height - 5 * age
    if gender == "Мужской":
        base_bmr += 5
    else:
        base_bmr -= 161

    calorie_goal = base_bmr + (act * 5)

    await set_user(message.from_user.id, {
        "name": name,
        "weight": weight,
        "height": height,
        "age": age,
        "gender": gender,
        "activity": act,
        "city": city,
        "water_goal": water_goal,
        "calorie_goal": calorie_goal
    })

    await message.answer(
        f"Ваш профиль настроен, {name}!\n\n"
        f"Пол: {gender}\n"
        f"{weather_info}\n\n"
        f"Цель по воде: {int(water_goal)} мл\n"
        f"Цель по калориям: {int(calorie_goal)} ккал\n\n"
        f"Используйте меню или команды для записи приемов пищи.",
        reply_markup=ReplyKeyboardRemove()
    )
    await state.clear()
