
import os

from aiogram import Bot
from aiogram import types
from aiogram import Dispatcher
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from dotenv import load_dotenv
load_dotenv()

BOT_TOKEN = os.getenv("token")

bot = Bot(token=BOT_TOKEN, parse_mode=types.ParseMode.HTML)

storage = MemoryStorage()

dp = Dispatcher(bot, storage=storage)