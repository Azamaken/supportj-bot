from aiogram import Bot
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message
from config import SUPPORT_GROUP_ID
from database import is_banned
from aiogram.exceptions import TelegramBadRequest
import time

topics_cache: dict[int, int] = {}

def build_topic_name(username: str, user_id: int) -> str:
    if username.startswith("@"):
        return f"{username} | {user_id}"
    return f"Без username | {user_id}"

def user_info_text(user_id: int, username: str, full_name: str, banned: bool) -> str:
    from html import escape
    return (
        f"<b>👤 Новый диалог</b>\n\n"
        f"🔹 <b>ID:</b> <code>{user_id}</code>\n"
        f"🔹 <b>Username:</b> {username}\n"
        f"🔹 <b>Имя:</b> <code>{escape(full_name)}</code>\n"
        f"🔹 <b>Статус:</b> <code>{'Заблокирован' if banned else 'Активен'}</code>"
    )

def info_buttons(user_id: int, banned: bool) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="🔓 Разблокировать" if banned else "🔒 Заблокировать",
                callback_data=f"toggle_ban:{user_id}"
            ),
            InlineKeyboardButton(text="📪 Закрыть диалог", callback_data=f"close_dialog:{user_id}"),
        ],
        [
            InlineKeyboardButton(text="🔁 Обновить", callback_data=f"refresh_info:{user_id}")
        ]
    ])

async def topic_exists(bot: Bot, thread_id: int) -> bool:
    try:
        test = await bot.send_message(
            chat_id=SUPPORT_GROUP_ID,
            message_thread_id=thread_id,
            text="🕵 Проверка темы...",
            disable_notification=True
        )
        await bot.delete_message(chat_id=SUPPORT_GROUP_ID, message_id=test.message_id)
        return True
    except TelegramBadRequest:
        return False
    

async def get_or_create_topic(
    bot: Bot,
    user_id: int,
    username: str,
    full_name: str,
) -> tuple[int, bool, str]:
    from database import get_topic_by_user, upsert_topic, reopen_topic
    from html import escape

    username = escape(username or "Без username")
    full_name = escape(full_name or "—")

    ticket_id = str(int(time.time()))
    topic = get_topic_by_user(user_id)

    if topic:
        thread_id, is_open = topic[1], topic[4]
        if thread_id and await topic_exists(bot, thread_id):
            if not is_open:
                try:
                    await bot.reopen_forum_topic(chat_id=SUPPORT_GROUP_ID, message_thread_id=thread_id)
                except TelegramBadRequest:
                    pass

                reopen_topic(user_id, thread_id, username, full_name)

                banned = is_banned(user_id)
                info_msg = await bot.send_message(
                    chat_id=SUPPORT_GROUP_ID,
                    message_thread_id=thread_id,
                    text=user_info_text(user_id, username, full_name, banned) + f"\n\n🆔 <b>Обращение:</b> <code>#T{ticket_id}</code>",
                    reply_markup=info_buttons(user_id, banned)
                )

                try:
                    await bot.pin_chat_message(
                        chat_id=SUPPORT_GROUP_ID,
                        message_id=info_msg.message_id,
                        disable_notification=True
                    )
                except TelegramBadRequest:
                    pass

                topics_cache[user_id] = thread_id
                return thread_id, True, ticket_id

            else:
                if topic[2] != username or topic[3] != full_name:
                    reopen_topic(user_id, thread_id, username, full_name)

                topics_cache[user_id] = thread_id
                return thread_id, False, None

    # Создание новой темы
    forum_topic = await bot.create_forum_topic(
        chat_id=SUPPORT_GROUP_ID,
        name=build_topic_name(username, user_id)[:64]
    )
    thread_id = forum_topic.message_thread_id
    topics_cache[user_id] = thread_id

    upsert_topic(user_id, thread_id, username, full_name, 1, int(time.time()))

    banned = is_banned(user_id)
    info_msg = await bot.send_message(
        chat_id=SUPPORT_GROUP_ID,
        message_thread_id=thread_id,
        text=user_info_text(user_id, username, full_name, banned) + f"\n\n🆔 <b>Обращение:</b> <code>#T{ticket_id}</code>",
        reply_markup=info_buttons(user_id, banned)
    )

    try:
        await bot.pin_chat_message(
            chat_id=SUPPORT_GROUP_ID,
            message_id=info_msg.message_id,
            disable_notification=True
        )
    except TelegramBadRequest:
        pass

    return thread_id, True, ticket_id





async def forward_to_topic(user_msg: Message, thread_id: int):
    try:
        await user_msg.bot.copy_message(
            chat_id=SUPPORT_GROUP_ID,
            from_chat_id=user_msg.chat.id,
            message_id=user_msg.message_id,
            message_thread_id=thread_id
        )
    except Exception:
        pass

async def reply_to_user(bot: Bot, thread_id: int, admin_msg: Message):
    user_id = next((uid for uid, tid in topics_cache.items() if tid == thread_id), None)
    if not user_id or is_banned(user_id):
        return

    try:
        await bot.copy_message(
            chat_id=user_id,
            from_chat_id=admin_msg.chat.id,
            message_id=admin_msg.message_id
        )
    except Exception:
        pass

async def close_topic(bot: Bot, thread_id: int, notify_text: str = "📪 Диалог успешно закрыт пользователем."):
    from database import clear_thread, mark_topic_closed
    user_id = next((uid for uid, tid in topics_cache.items() if tid == thread_id), None)
    if user_id:
        try:
            await bot.send_message(
                chat_id=SUPPORT_GROUP_ID,
                message_thread_id=thread_id,
                text=notify_text
            )
        except:
            pass

        topics_cache.pop(user_id, None)
        clear_thread(user_id)
        mark_topic_closed(user_id)

    try:
        await bot.close_forum_topic(chat_id=SUPPORT_GROUP_ID, message_thread_id=thread_id)
    except TelegramBadRequest:
        pass
