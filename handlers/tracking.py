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

    name, kcal_100 = await get_food_info(product_name)

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
        kcal = float(message.text)
        await state.update_data(food_calories_per_100=kcal, unit_weight=None)
        await message.answer("Сколько грамм вы съели?")
        await state.set_state(FoodLog.grams)
    except ValueError:
        await message.answer("Введите число (ккал).")


@router.message(FoodLog.grams)
async def process_grams(message: types.Message, state: FSMContext):
    try:
        input_value = float(message.text)
        data = await state.get_data()

        unit_weight = data.get('unit_weight')

        if unit_weight:
            grams = input_value * unit_weight
            quantity_text = f"{int(input_value)} шт. ({int(grams)} г)"
        else:
            grams = input_value
            quantity_text = f"{int(grams)} г"

        total_kcal = (data['food_calories_per_100'] * grams) / 100

        await log_food(message.from_user.id, total_kcal)

        food_name = data.get('food_name', 'Продукт')
        await message.answer(f"{food_name}: {quantity_text} — {int(total_kcal)} ккал.")
        await state.clear()

    except ValueError:
        await message.answer("Введите число.")


@router.message(Command("log_workout"))
async def cmd_log_workout(message: types.Message, state: FSMContext):
    await state.clear()
    user = await get_user(message.from_user.id)
    if not user: return await message.answer("Такого пользователя пока нет. Сначала настройте профиль: /set_profile")

    parts = message.text.split()
    if len(parts) < 3: return await message.answer("Пример: /log_workout бег 30")

    try:
        w_type = parts[1]
        minutes = int(parts[2])
        burned = minutes * 10
        water_bonus = (minutes // 30) * 200

        await log_workout(message.from_user.id, burned, water_bonus)
        await message.answer(f"{w_type} {minutes} мин: {burned} ккал.\n Доп. вода: {water_bonus} мл.")
    except ValueError:
        await message.answer("Время должно быть числом.")
