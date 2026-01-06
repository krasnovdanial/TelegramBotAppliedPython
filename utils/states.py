from aiogram.fsm.state import State, StatesGroup


class ProfileSetup(StatesGroup):
    name = State()
    weight = State()
    height = State()
    age = State()
    activity = State()
    city = State()


class FoodLog(StatesGroup):
    food_name = State()
    food_calories_per_100 = State()
    grams = State()
