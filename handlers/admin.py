from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from config import ADMINS, bot, dp
from database import ban_user, unban_user, get_user, is_banned
from services.support import close_topic, info_buttons, user_info_text, reply_to_user
import re

router = Router()


def extract_user_id_from_topic(message: Message) -> int | None:
    if not message.is_topic_message or not message.message_thread_id:
        return None
    match = re.search(r"\|\s*(\d+)", message.chat.title or "")
    if match:
        return int(match.group(1))
    return None


@router.callback_query(F.data.startswith("toggle_ban:"))
async def toggle_ban_button(call: CallbackQuery):
    user_id = int(call.data.split(":")[1])
    if call.from_user.id not in ADMINS:
        return await call.answer("⛔ Недостаточно прав.")

    if is_banned(user_id):
        unban_user(user_id)
        await call.answer("✅ Пользователь разблокирован.")
    else:
        ban_user(user_id)
        await call.answer("🚫 Пользователь заблокирован.")

    user = get_user(user_id)
    if user:
        text = user_info_text(user_id, f"@{user[1]}" if user[1] else "Без username", user[2], is_banned(user_id))
        await call.message.edit_text(
            text=text,
            reply_markup=info_buttons(user_id, is_banned(user_id))
        )


@router.callback_query(F.data.startswith("close_dialog:"))
async def close_dialog_button(call: CallbackQuery):
    user_id = int(call.data.split(":")[1])
    if call.from_user.id not in ADMINS:
        return await call.answer("⛔ Недостаточно прав.")

    user = get_user(user_id)
    if user and user[4]:
        await close_topic(bot, user[4])

        # Завершить FSM пользователя
        try:
            context = dp.fsm.get_context(bot=bot, chat_id=user_id, user_id=user_id)
            await context.clear()
        except Exception:
            pass

        await call.answer("📪 Диалог закрыт.")
        await bot.send_message(chat_id=user_id, text="📪 Диалог был закрыт администратором.")


@router.callback_query(F.data.startswith("refresh_info:"))
async def refresh_info_button(call: CallbackQuery):
    user_id = int(call.data.split(":")[1])
    if call.from_user.id not in ADMINS:
        return await call.answer("⛔ Недостаточно прав.")

    user = get_user(user_id)
    if not user:
        return await call.answer("❌ Пользователь не найден.")

    text = user_info_text(user_id, f"@{user[1]}" if user[1] else "Без username", user[2], is_banned(user_id))

    try:
        await call.message.edit_text(text=text,
            reply_markup=info_buttons(user_id, is_banned(user_id))
        )
    except:
        pass
    await call.answer("🔁 Информация обновлена.")

@router.message(F.text, lambda msg: msg.chat.type == 'supergroup' and msg.message_thread_id)
async def handle_admin_reply(message: Message):
    if message.from_user.id not in ADMINS:
        return
    
    thread_id = message.message_thread_id
    await reply_to_user(message.bot, thread_id, message)

