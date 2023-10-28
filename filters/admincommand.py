import logging
from aiogram import types
from aiogram.dispatcher.filters import BoundFilter
from aiogram.dispatcher.handler import CancelHandler
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from loader import bot, dp
from data.config import admins

class AdminCommand(BoundFilter):
    async def check(self, message: types.Message):
        if message.from_user.id in admins:
            return True
        else:
            logging.warning(f"[@{message.from_user.username}] is not an admin. ")
            return False