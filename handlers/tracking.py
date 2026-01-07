import random

from aiogram import Router, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from db.requests import get_user, log_water, log_food, log_workout
from utils.api import get_food_info
from utils.states import FoodLog

router = Router()

AVERAGE_WEIGHTS = {
    "банан": 120,
    "яблоко": 180,
    "груша": 170,
    "апельсин": 150,
    "мандарин": 80,
    "яйцо": 55,
    "киви": 70,
    "огурец": 100,
    "помидор": 120,
    "кусок хлеба": 30,
    "стакан молока": 200,
    "бургер": 237,
}

ACTIVITY_RATES = {
    "бег": 10,
    "ходьба": 5,
    "велосипед": 8,
    "плавание": 8,
    "зал": 6,
    "йога": 4,
    "бокс": 12,
    "уборка": 3
}



@router.message(Command("log_water"))
async def cmd_log_water(message: types.Message, state: FSMContext):
    await state.clear()
    user = await get_user(message.from_user.id)
    if not user:
        return await message.answer("Такого пользователя пока нет. Сначала настройте профиль: /set_profile")

    try:
        amount = int(message.text.split()[1])
        await log_water(message.from_user.id, amount)
        updated_user = await get_user(message.from_user.id)
        rem = updated_user.water_goal - updated_user.logged_water
        await message.answer(f"Записано {amount} мл. Осталось: {max(0, int(rem))} мл.")
    except (IndexError, ValueError):
        await message.answer("Пример использования: /log_water 250")


@router.message(Command("log_food"))
async def cmd_log_food(message: types.Message, state: FSMContext):
    await state.clear()

    if not await get_user(message.from_user.id):
        return await message.answer("Такого пользователя пока нет. Сначала настройте профиль: /set_profile")

    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        return await message.answer("Пример: /log_food банан")

    product_name = parts[1].lower()

    name, kcal_100, _ = await get_food_info(product_name)

    if kcal_100:
        await message.answer(
            f"Продукт найден: {name}\n"
            f"Калорийность: {int(kcal_100)} ккал."
        )

    if not name:
        await message.answer(f"Не нашел '{product_name}'. Введите калорийность на 100г вручную:")
        await state.update_data(food_name=product_name)
        await state.set_state(FoodLog.food_calories_per_100)
        return None
    else:
        await state.update_data(food_name=name, food_calories_per_100=kcal_100)
        found_unit_weight = None
        for key, weight in AVERAGE_WEIGHTS.items():
            if key in product_name:
                found_unit_weight = weight
                break

        if found_unit_weight:
            await state.update_data(unit_weight=found_unit_weight)
            await message.answer(
                f"{name} — {kcal_100} ккал/100г.\n"
                f"Обычно одна штука весит около {found_unit_weight} г.\n"
                f"Сколько штук вы съели?"
            )
        else:
            await state.update_data(unit_weight=None)
            await message.answer(f"{name} — {kcal_100} ккал/100г.\nСколько грамм вы съели?")

        await state.set_state(FoodLog.grams)
        return None


@router.message(FoodLog.food_calories_per_100)
async def manual_calories(message: types.Message, state: FSMContext):
    try:
        kcal = float(message.text.replace(',', '.'))
        await state.update_data(food_calories_per_100=kcal, unit_weight=None)
        await message.answer("Сколько грамм вы съели?")
        await state.set_state(FoodLog.grams)

    except ValueError:
        user_text = message.text
        loading_msg = await message.answer(f"Ищу калорийность для {user_text}...")

        product_name, kcal, _ = await get_food_info(user_text)

        await loading_msg.delete()

        if kcal:
            await state.update_data(food_name=product_name, food_calories_per_100=kcal, unit_weight=None)
            await message.answer(
                f"Найдено: {product_name}\n"
                f"Калорийность: {int(kcal)} ккал на 100г.\n\n"
                f"Сколько грамм вы съели?",
            )
            await state.set_state(FoodLog.grams)
        else:
            await message.answer("Не удалось определить продукт. Введите число (ккал на 100г).")


@router.message(FoodLog.grams)
async def process_grams(message: types.Message, state: FSMContext):
    try:
        amount = float(message.text.replace(',', '.'))
        if amount <= 0: raise ValueError

        data = await state.get_data()

        kcal_100 = data.get('food_calories_per_100')
        unit_weight = data.get('unit_weight')
        food_name = data.get('food_name', 'Продукт')

        if unit_weight:
            grams = amount * unit_weight
            quantity_text = f"{amount:g} шт. ({int(grams)} г)"
        else:
            grams = amount
            quantity_text = f"{int(grams)} г"

        total_kcal = (grams * kcal_100) / 100

        await log_food(message.from_user.id, calories=total_kcal)
        advice = ""
        if total_kcal > 500:
            workouts = [
                "поприседать 20 раз",
                "прогуляться 30 минут",
                "сделать планку на 1 минуту",
                "отказаться от лифта сегодня"
            ]
            random_workout = random.choice(workouts)
            advice = (
                f"/nЧтобы калории не ушли в жир, рекомендую {random_workout}!"
            )
        elif total_kcal > 300:
            advice = "\nПлотный перекус. Не забудьте пить воду!"

        await message.answer(
            f"Добавлено: {food_name}\n"
            f"Порция: {quantity_text}\n"
            f"Итог: +{int(total_kcal)} ккал"
            f"{advice}",
        )
        await state.clear()

    except ValueError:
        await message.answer("Пожалуйста, введите корректное число.")


@router.message(Command("log_workout"))
async def cmd_log_workout(message: types.Message, state: FSMContext):
    await state.clear()
    user = await get_user(message.from_user.id)
    if not user:
        return await message.answer("Сначала настройте профиль: /set_profile")

    parts = message.text.split()
    if len(parts) < 3:
        return await message.answer(
            "Пример ввода: /log_workout бег 30\n\n"
            "Доступные виды: бег, ходьба, велосипед, плавание, зал, йога, бокс."
        )

    workout_type = parts[1].lower()

    try:
        minutes = int(parts[2])
        if minutes <= 0: raise ValueError

        kcal_per_min = ACTIVITY_RATES.get(workout_type, 7)

        note = ""
        if workout_type not in ACTIVITY_RATES:
            note = f"\n(Такой активности нет в базе, посчитал по среднему: 7 ккал/мин)"

        burned = minutes * kcal_per_min

        water_bonus = (minutes // 30) * 200

        await log_workout(message.from_user.id, burned_kcal=burned, water_needed=water_bonus)

        await message.answer(
            f"Тренировка: {workout_type.capitalize()}\n"
            f"Время: {minutes} мин\n"
            f"Сожжено: {int(burned)} ккал{note}\n"
            f"Доп. вода: +{water_bonus} мл",
        )

    except ValueError:
        await message.answer("Время должно быть числом (минуты).")
