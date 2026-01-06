import logging
from aiogram import BaseMiddleware
from aiogram.types import Message


class LoggingMiddleware(BaseMiddleware):
    async def __call__(self, handler, event, data):
        if isinstance(event, Message):
            user = event.from_user
            username = user.username or "NoUsername"
            user_id = user.id
            text = event.text or "<Sticker/Photo>"

            logging.info(f"Log: Пользователь: @{username} (ID: {user_id}) | Сообщение: {text}")

        return await handler(event, data)