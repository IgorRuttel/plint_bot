import asyncio

from create_bot import bot, dp
from handlers.start import start_router
from handlers.logic import address_router
from handlers.admin import admin_router
from db_handler.models import async_main


async def main():
    await async_main()
    dp.include_router(start_router)
    dp.include_router(address_router)
    dp.include_router(admin_router)
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
