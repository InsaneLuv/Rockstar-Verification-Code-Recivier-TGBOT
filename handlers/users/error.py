import logging
from aiogram import types
from utils.misc import rate_limit
from loader import dp

@rate_limit(limit=5)
@dp.message_handler()
async def command_any_unknown(message: types.Message):
    logging.info(f'❓ Пользователь @{message.from_user.username} ввел неизвестную комманду: {message.text}.')

    await message.reply(
        '🤷🏻 Команда "{message}" вам недоступна.'.format(message=message.text)
    )
