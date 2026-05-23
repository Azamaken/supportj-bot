import asyncio
import time
from database import get_all_active_threads, is_banned
from services.support import close_topic
from aiogram import Bot
from config import dp

INACTIVITY_TIMEOUT = 86400

async def auto_close_loop(bot: Bot):
    while True:
        await asyncio.sleep(3600)
        now = int(time.time())
        users = get_all_active_threads()

        for user_id, thread_id, last_activity in users:
            if not thread_id or is_banned(user_id):
                continue

            if now - last_activity >= INACTIVITY_TIMEOUT:
                try:
                    await close_topic(
                        bot,
                        thread_id,
                        notify_text="⏳ Диалог автоматически закрыт из-за неактивности (24ч)."
                    )

                    try:
                        await bot.send_message(
                            chat_id=user_id,
                            text="📪 Ваш диалог с поддержкой был закрыт из-за неактивности."
                        )
                    except:
                        pass

                    try:
                        context = dp.fsm.get_context(bot=bot, user_id=user_id, chat_id=user_id)
                        await context.clear()
                    except Exception:
                        pass

                except Exception:
                    pass
