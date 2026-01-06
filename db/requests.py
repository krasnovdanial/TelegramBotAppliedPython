from sqlalchemy import select, update

from db.base import async_session
from db.models import User


async def set_user(user_id, data):
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.user_id == user_id))

        if not user:
            user = User(user_id=user_id, **data)
            session.add(user)
        else:
            for key, value in data.items():
                setattr(user, key, value)
        await session.commit()


async def get_user(user_id):
    async with async_session() as session:
        return await session.scalar(select(User).where(User.user_id == user_id))


async def log_water(user_id, amount):
    async with async_session() as session:
        await session.execute(
            update(User).where(User.user_id == user_id)
            .values(logged_water=User.logged_water + amount)
        )
        await session.commit()


async def log_food(user_id, calories):
    async with async_session() as session:
        await session.execute(
            update(User).where(User.user_id == user_id)
            .values(logged_calories=User.logged_calories + calories)
        )
        await session.commit()


async def log_workout(user_id, burned_kcal, water_needed):
    async with async_session() as session:
        await session.execute(
            update(User).where(User.user_id == user_id)
            .values(
                burned_calories=User.burned_calories + burned_kcal,
                water_goal=User.water_goal + water_needed
            )
        )
        await session.commit()
