from aiogram import types
from loader import dp
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from data.config import admins, get_access_list, remove_from_access_list
import logging
from utils.misc import rate_limit
from .start import get_access_markup

@rate_limit(limit=2)
@dp.message_handler(lambda message: "👁‍" in message.text)
async def func(message: types.Message):
    logging.info(f'👁‍ Пользователь @{message.from_user.username} ввел комманду: {message.text}.')
    if message.from_user.id not in admins:
        await message.reply(text='🖕🏻 Нет доступа.',reply_markup=get_access_markup())
        return
    
    text =  f'👁‍ У кого отнимем доступ?'
    await message.reply(text=text,reply_markup=genmarkup())


def genmarkup():
    markup = InlineKeyboardMarkup()
    markup.row_width = 2
    users = []
    for id in get_access_list():
        users.append(id)
    if len(users) != 0:
        for id in users:
            if id not in admins:
                markup.add(InlineKeyboardButton(text=f'{id}', callback_data=f'take_away_access_{id}'))
    if len(markup.inline_keyboard) == 0:
        markup.add(InlineKeyboardButton(text=f'🤷‍♂️ Пусто 🤷‍♂️', callback_data=f'ZZZZ'))
    return markup

@dp.callback_query_handler(lambda call: "take_away_access_" in call.data)
async def get_code(callback_query: types.CallbackQuery):
    if callback_query.from_user.id not in admins:
        if callback_query.from_user.id not in get_access_list():
            await callback_query.message.edit_text(text='🖕🏻 Нет доступа.',reply_markup=get_access_markup())
            return

    user_id = callback_query.data.replace('take_away_access_','')
    remove_from_access_list(user_id)
    await callback_query.message.edit_text(text=f'👁‍ Пользователь {user_id} теперь не имеет доступа к боту.')
