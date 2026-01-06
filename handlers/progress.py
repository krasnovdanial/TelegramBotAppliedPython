import io

import matplotlib.pyplot as plt
from aiogram import Router, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import BufferedInputFile

from db.requests import get_user

router = Router()


def generate_progress_chart(user):
    water_goal = user.water_goal
    water_current = user.logged_water
    cal_goal = user.calorie_goal
    cal_current = user.logged_calories
    cal_burned = user.burned_calories

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 5))
    water_left = max(0, water_goal - water_current)

    labels = ['Выпито', 'Осталось']
    values = [water_current, water_left]

    ax1.pie(values, labels=labels, autopct='%1.1f%%', startangle=90)
    ax1.set_title(f"Вода (Всего: {int(water_goal)} мл)")

    categories = ['Еда', 'Спорт', 'Осталось']

    cal_balance = cal_current - cal_burned
    cal_left = max(0, cal_goal - cal_balance)

    values_cal = [cal_current, cal_burned, cal_left]

    ax2.bar(categories, values_cal)
    ax2.set_title(f"Калории (Цель: {int(cal_goal)})")

    ax2.grid(True, axis='y', alpha=0.5)

    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    plt.close(fig)
    return buf


@router.message(Command("check_progress"))
async def cmd_check_progress(message: types.Message, state: FSMContext):
    await state.clear()

    user = await get_user(message.from_user.id)
    if not user:
        return await message.answer("Нет данных.")

    user_name = user.name

    photo_file = generate_progress_chart(user)

    await message.answer_photo(
        photo=BufferedInputFile(photo_file.read(), filename="progress.png"),
        caption=f"Прогресс для {user_name}:\n",
        parse_mode="Markdown"
    )
    return None
