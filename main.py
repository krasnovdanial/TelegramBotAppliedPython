import asyncio
import logging
import os

from aiogram import Bot, Dispatcher
from aiogram.types import BotCommand
from aiohttp import web
from dotenv import load_dotenv

from db.base import init_db
from handlers import start, tracking, progress
from utils.middlewares import LoggingMiddleware

load_dotenv()


async def keep_alive():
    app = web.Application()
    app.router.add_get('/', lambda r: web.Response(text="I'm alive"))

    runner = web.AppRunner(app)
    await runner.setup()

    port = int(os.getenv("PORT", 8080))
    print(f"Запускаю keep-alive сервер на порту {port}")

    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()


async def setup_bot_commands(bot: Bot):
    bot_commands = [
        BotCommand(command="/start", description="Запустить бота"),
        BotCommand(command="/set_profile", description="Настроить профиль"),
        BotCommand(command="/log_water", description="Записать воду"),
        BotCommand(command="/log_food", description="Записать еду"),
        BotCommand(command="/log_workout", description="Записать тренировку"),
        BotCommand(command="/check_progress", description="Посмотреть прогресс"),
    ]
    await bot.set_my_commands(bot_commands)


async def main():
    logging.basicConfig(level=logging.INFO)
    await init_db()

    bot = Bot(token=os.getenv('TOKEN'))
    dp = Dispatcher()

    dp.message.middleware(LoggingMiddleware())

    dp.include_routers(
        start.router,
        tracking.router,
        progress.router
    )

    await setup_bot_commands(bot)
    asyncio.create_task(keep_alive())
    print("Бот запущен!")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Бот выключен")
