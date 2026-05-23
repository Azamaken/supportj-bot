from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.default import DefaultBotProperties

BOT_TOKEN = "8835912432:AAGAOCIw_z0fJlzscYht8TeeDK-dpqNibVg"
SUPPORT_GROUP_ID = -1003751481942 # ID Супер группы с Темами
ADMINS = [7528568061, 8208471171, 61238209, 6290302179] # ID Админов, которые могут отвечать в темах [1, 2, 3, 4...]

SUPPORT_CHANNEL_URL = "https://t.me/+ZW02FpgunbJiNzc0"
SUPPORT_CHANNEL_NAME = "Жесть Ташкента"
CUSTOM_EMOJI_ID_CHANNEL_BUTTON = 5222117260507782317  # Вставьте ваш premium emoji ID для кнопки канала
CUSTOM_EMOJI_ID_START_BUTTON = 5199467479889370091    # Вставьте ваш premium emoji ID для кнопки начала диалога
CUSTOM_EMOJI_ID_CLOSE_BUTTON = 5213460324425935151    # Вставьте ваш premium emoji ID для кнопки закрытия диалога

storage = MemoryStorage()
bot = Bot(BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher(storage=storage)

# БОТ Создан для личного использования, но так как я, @nutrok, не жадный -> Слил скриптик
# Если не жалко, можете накинуть старсиков по тегу :3