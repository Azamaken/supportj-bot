import asyncio

from config import bot, dp
from handlers import user, admin
from utils.scheduler import auto_close_loop


dp.include_routers(user.router, admin.router)

async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    asyncio.create_task(auto_close_loop(bot))
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
