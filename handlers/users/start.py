from aiogram import types
from loader import dp, bot
from utils.misc import rate_limit
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from data.config import admins,get_access_list
from aiogram import md
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
import logging
import ast


@rate_limit(limit=60)
@dp.message_handler(text='/start')
async def command_start(message: types.Message):
    logging.info(f'🔆 Пользователь @{message.from_user.username} отправил комманду: /start.')

    if message.from_user.id in admins or message.from_user.id in get_access_list():
        await bot.send_message(
                chat_id=message.from_user.id,
                text=f"❤️ Доступ разрешен.",
                reply_markup=gen_user_kb(message.from_user.id)
            )
    else:
        await bot.send_message(
                chat_id=message.from_user.id,
                text=f"😥 У тебя нет доступа...",parse_mode="HTML",reply_markup=get_access_markup()
            )

def gen_user_kb(user_id):
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(KeyboardButton(text='⚒ Получить код'))
    if user_id in admins:
        logging.info(f'🙋')
        kb.add(KeyboardButton(text='👁‍ Забрать доступ'))
    return kb

def get_access_markup():
    markup = InlineKeyboardMarkup()
    markup.row_width = 1
    markup.add(InlineKeyboardButton(text=f'🙋 Запросить доступ.', callback_data=f'get_access'))
    return markup

def grant_deny_markup(user_data):
    markup = InlineKeyboardMarkup()
    markup.row_width = 2
    markup.add(InlineKeyboardButton(text=f'✅ Выдать доступ.', callback_data=f'grant_access_{user_data}'))
    markup.add(InlineKeyboardButton(text=f'🚫 Отклонить.', callback_data=f'deny_access_{user_data}'))
    return markup

@dp.callback_query_handler(lambda call: "get_access" in call.data)
async def get_access(callback_query: types.CallbackQuery):
    logging.info(f'🙋 Пользователь @{callback_query.from_user.username} попросил доступ.')


    text =  f'🙋 Запрос отправлен администратору.\n\n<i>Ожидай...</i>'
    await callback_query.message.edit_text(text=text,parse_mode="HTML")
    text =  f'🙋 Пользователь запросил доступ.\n\n'\
            f'🆔: {callback_query.from_user.id}\n'\
            f'👤: @{callback_query.from_user.username}\n'
    data = {'id': callback_query.from_user.id,'username': callback_query.from_user.username}
    for admin in admins:
        await bot.send_message(chat_id=admin,text=text,reply_markup=grant_deny_markup(data))

@dp.callback_query_handler(lambda call: "grant_access_" in call.data)
async def func(call: types.CallbackQuery):
    user_data = ast.literal_eval(call.data.replace('grant_access_',''))
    logging.info(f'✅ Администратор @{call.from_user.username} выдал доступ @{user_data["username"]}.')
    
    if user_data['id'] not in get_access_list():
        with open('access.txt', 'a') as access_file:
            access_file.write(f'\n{user_data["id"]}')
        
    text =  f'✅ Администратор @{call.from_user.username} выдал тебе доступ.\n\n'\
            f'<i>Теперь тебе доступны кнопки ниже.</i>'
    await bot.send_message(chat_id=user_data["id"],text=text,reply_markup=gen_user_kb(user_data["id"]))
    text =  f'✅ Доступ выдан.\n\n'\
            f'🆔: {user_data["id"]}\n'\
            f'👤: @{user_data["username"]}\n'
    await call.message.edit_text(text=text,parse_mode="HTML")


@dp.callback_query_handler(lambda call: "deny_access_" in call.data)
async def func(callback_query: types.CallbackQuery):
    user_data = ast.literal_eval(callback_query.data.replace('deny_access_',''))
    logging.info(f'🚫 Администратор @{callback_query.from_user.username} отклонил запрос @{user_data["username"]}.')

    text =  f'🚫 Администратор @{callback_query.from_user.username} отклонил твой запрос.'
    await bot.send_message(chat_id=user_data["id"],text=text,reply_markup=types.ReplyKeyboardRemove())
    text =  f'🚫 Запрос отклонён.\n\n'\
            f'🆔: {user_data["id"]}\n'\
            f'👤: @{user_data["username"]}\n'
    await callback_query.message.edit_text(text=text,parse_mode="HTML")
