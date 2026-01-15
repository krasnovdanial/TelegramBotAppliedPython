from sqlalchemy import BigInteger, String, Float, Integer
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(AsyncAttrs, DeclarativeBase):
    pass


class User(Base):
    __tablename__ = 'users'

    user_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=True)

    weight: Mapped[float] = mapped_column(Float)
    height: Mapped[float] = mapped_column(Float)
    age: Mapped[int] = mapped_column(Integer)
    gender: Mapped[str] = mapped_column(String)
    activity: Mapped[int] = mapped_column(Integer)
    city: Mapped[str] = mapped_column(String)

    water_goal: Mapped[float] = mapped_column(Float)
    calorie_goal: Mapped[float] = mapped_column(Float)

    logged_water: Mapped[float] = mapped_column(Float, default=0.0)
    logged_calories: Mapped[float] = mapped_column(Float, default=0.0)
    burned_calories: Mapped[float] = mapped_column(Float, default=0.0)
