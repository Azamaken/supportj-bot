from aiogram import Router, F
from aiogram.enums import ButtonStyle
from aiogram.types import (
    Message, CallbackQuery,
    InlineKeyboardButton, InlineKeyboardMarkup,
    ReplyKeyboardRemove
)
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

from config import (
    bot, SUPPORT_CHANNEL_URL, SUPPORT_CHANNEL_NAME,
    CUSTOM_EMOJI_ID_CHANNEL_BUTTON, CUSTOM_EMOJI_ID_START_BUTTON,
    CUSTOM_EMOJI_ID_CLOSE_BUTTON
)
from database import (
    upsert_user, get_user,
    is_banned, update_last_activity
)
from services.support import (
    get_or_create_topic, forward_to_topic, close_topic
)
import time

router = Router()


class DialogState(StatesGroup):
    active = State()


@router.message(F.text == "/start")
async def cmd_start(message: Message, state: FSMContext):
    if state: await state.clear()
    await state.clear()
    await message.answer(
        "<tg-emoji emoji-id='5222117260507782317'>⚜️</tg-emoji> "
        "<b><i>Привет! Это предложка Жесть Ташкента</i></b>\n"
        "<tg-emoji emoji-id='5334882760735598374'>📝</tg-emoji> "
        "<b><i>Отправь свою историю, новость или ситуацию</i></b>\n"
        "<tg-emoji emoji-id='5231102735817918643'>👇</tg-emoji> "
        "<b><i>Нажми кнопку ниже, чтобы начать</i></b>",
        reply_markup=start_keyboard(),
        parse_mode="HTML"
    )

@router.message(lambda msg: msg.text and msg.text.lower() in ("закрыть диалог", "/close"))
async def close_dialog_by_user(message: Message, state: FSMContext):
    user = get_user(message.from_user.id)

    if not user or not user[4]:
        await state.clear()
        await message.answer("<tg-emoji emoji-id='5258503720928288433'>ℹ️</tg-emoji> <b><i>Диалог уже был закрыт ранее.</i></b>", reply_markup=ReplyKeyboardRemove(), parse_mode="HTML")
        await message.answer("<tg-emoji emoji-id='5231102735817918643'>👇</tg-emoji> <b><i>Нажмите кнопку ниже, чтобы начать новый диалог.</i></b>", reply_markup=new_kb(), parse_mode="HTML")
        return

    thread_id = user[4]
    await close_topic(bot, thread_id)
    await state.clear()

    await message.answer("<tg-emoji emoji-id='5350310124349053625'>📪</tg-emoji> <b><i>Диалог закрыт успешно.</i></b>", reply_markup=ReplyKeyboardRemove(), parse_mode="HTML")
    await message.answer("<tg-emoji emoji-id='5231102735817918643'>👇</tg-emoji> <b><i>Нажмите кнопку ниже, чтобы создать новый диалог.</i></b>", reply_markup=new_kb(), parse_mode="HTML")

@router.callback_query(F.data == "dialogclose")
async def close_dialog_by_user(call: CallbackQuery, state: FSMContext):
    user = get_user(call.from_user.id)

    if not user or not user[4]:
        await state.clear()
        try:
            await call.message.edit_text(
                "<tg-emoji emoji-id='5258503720928288433'>ℹ️</tg-emoji> <b><i>Диалог уже был закрыт ранее.</i></b>",
                reply_markup=new_kb(),
                parse_mode="HTML"
            )
        except:
            try:
                await call.message.delete()
            except:
                pass
            await call.message.answer("<tg-emoji emoji-id='5258503720928288433'>ℹ️</tg-emoji> <b><i>Диалог уже был закрыт ранее.</i></b>", reply_markup=ReplyKeyboardRemove(), parse_mode="HTML")
            await call.message.answer("<tg-emoji emoji-id='5231102735817918643'>👇</tg-emoji> <b><i>Нажмите кнопку ниже, чтобы начать новый диалог.</i></b>", reply_markup=new_kb(), parse_mode="HTML")
        return

    thread_id = user[4]
    await close_topic(bot, thread_id)
    await state.clear()

    try:
        await call.message.edit_text("<tg-emoji emoji-id='5350310124349053625'>📪</tg-emoji> <b><i>Диалог закрыт успешно.</i></b>", reply_markup=new_kb(), parse_mode="HTML")
    except:
        try:
            await call.message.delete()
        except:
            pass
        await call.message.answer("<tg-emoji emoji-id='5350310124349053625'>📪</tg-emoji> <b><i>Диалог закрыт успешно.</i></b>", reply_markup=ReplyKeyboardRemove(), parse_mode="HTML")
        await call.message.answer("<tg-emoji emoji-id='5231102735817918643'>👇</tg-emoji> <b><i>Нажмите кнопку ниже, чтобы создать новый диалог.</i></b>", reply_markup=new_kb(), parse_mode="HTML")


@router.message(DialogState.active)
async def relay_message_to_support(message: Message, state: FSMContext):
    from database import upsert_user

    user_id = message.from_user.id
    if is_banned(user_id):
        return

    username = f"@{message.from_user.username}" if message.from_user.username else "Без username"
    full_name = (message.from_user.full_name or "").strip()[:64] or "—"
    unique = str(int(time.time()))
    thread_id, is_new, ticket_id = await get_or_create_topic(message.bot, user_id, username, full_name)
    
    upsert_user(user_id, message.from_user.username, full_name, thread_id, int(time.time()))
    update_last_activity(user_id, int(time.time()))

    if is_new and ticket_id:
        await message.answer(
            f"<tg-emoji emoji-id='5260416304224936047'>✅</tg-emoji> <b><i>Ваше обращение получено. Чат создан.</i></b>\n\n🆔 Номер: <code>#T{ticket_id}</code>", reply_markup=close_kb(), parse_mode="HTML"
        )

    await forward_to_topic(message, thread_id)



@router.callback_query(F.data == "start_dialog")
async def start_dialog_callback(call: CallbackQuery, state: FSMContext):
    user_id = call.from_user.id

    if is_banned(user_id):
        return await call.message.edit_text("<b><i>🚫 Вы заблокированы и не можете писать в поддержку.</i></b>", parse_mode="HTML")

    current_state = await state.get_state()
    if current_state == DialogState.active.state:
        # Диалог уже активен
        await call.answer("💬 Диалог уже запущен.", show_alert=False)
        return await call.message.edit_text(
            "<b><i>💬 Диалог уже запущен. Вы можете продолжить писать сообщение или закрыть диалог кнопкой ниже.</i></b>",
            reply_markup=close_kb(),
            parse_mode="HTML"
        )

    # Установка state и обновление данных
    full_name = (call.from_user.full_name or "").strip()[:64] or "—"
    username = call.from_user.username
    upsert_user(user_id, username, full_name, None, int(time.time()))
    await state.set_state(DialogState.active)

    try:
        await call.message.delete()
    except:
        pass

    await call.message.answer(
        "<tg-emoji emoji-id='5458382591121964689'>✍️</tg-emoji> <b><i>Диалог активирован! Напишите любое сообщение, и оно пойдёт в поддержку.</i></b>\n\n"
        "<b><i>Чтобы закрыть диалог, нажмите кнопку ниже или отправьте 'Закрыть диалог'.</i></b>",
        reply_markup=close_kb(),
        parse_mode="HTML"
    )


# Главное меню с двумя inline кнопками
def start_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text=f"{SUPPORT_CHANNEL_NAME}",
                url=SUPPORT_CHANNEL_URL,
                style=ButtonStyle.DANGER,
                icon_custom_emoji_id=str(CUSTOM_EMOJI_ID_CHANNEL_BUTTON)
            )
        ],
        [
            InlineKeyboardButton(
                text="Начать диалог",
                callback_data="start_dialog",
                style=ButtonStyle.DANGER,
                icon_custom_emoji_id=str(CUSTOM_EMOJI_ID_START_BUTTON)
            )
        ]
    ])


def new_kb() -> InlineKeyboardMarkup:
    return start_keyboard()


def close_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="Закрыть диалог",
                callback_data="dialogclose",
                style=ButtonStyle.DANGER,
                icon_custom_emoji_id=str(CUSTOM_EMOJI_ID_CLOSE_BUTTON)
            )
        ]
    ])
