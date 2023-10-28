from aiogram import types
from loader import dp
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import re
from imaplib import IMAP4_SSL
import email
from email.utils import parsedate_to_datetime
from aiogram import md
from data.config import admins, get_access_list
import logging
from utils.misc import rate_limit
from .start import get_access_markup

@rate_limit(limit=2)
@dp.message_handler(lambda message: "⚒" in message.text)
async def show_inline_menu(message: types.Message):
    logging.info(f'⚒ Пользователь @{message.from_user.username} ввел комманду: {message.text}.')
    if message.from_user.id not in admins:
        if message.from_user.id not in get_access_list():
            await message.reply(text='🖕🏻 Нет доступа.',reply_markup=get_access_markup())
            return
        
    text =  f'📫 Выбери почту:\n\n'\
            f'<i>Читаются последние письма на почте, иногда отображаются старые письма(Проверяйте время).</i>'
    await message.reply(text=text,reply_markup=genmarkup())


@dp.callback_query_handler(lambda call: "get_code_" in call.data)
async def get_code(callback_query: types.CallbackQuery):
    text = '👨🏻‍💻 Читаю почту...'
    await callback_query.message.edit_text(text=text)
    if callback_query.from_user.id not in admins:
        if callback_query.from_user.id not in get_access_list():
            await callback_query.message.edit_text(text='🖕🏻 Нет доступа.',reply_markup=get_access_markup())
            return

    mail = callback_query.data.replace('get_code_','')

    for account in get_mail_list():
        if account.login == mail:
            logging.info(f'| Запрошен код с почты: [{account.login}] от: [{callback_query.from_user.username}]')
            logging.info(f'| Подключение: [{account.login}]')
            account.connect()
            logging.info(f'| Запрос кода: [{account.login}]')
            data = account.get_rgl_code()
            logging.info(f'| Получен ответ: [{data}]')
            await dp.bot.answer_callback_query(callback_query.id)
            if data:
                code = '{:,}'.format(int(data['code'])).replace(',', ' ')
                time = data["time"].strftime('%H:%M')
                text =  f'Код: <code>{md.quote_html(code)}</code>\n'\
                        f'Время: <code>{md.quote_html(time)}</code>\n'\
                        f'Почта: <code>{md.quote_html(data["mail"])}</code>'
            else:
                text =  f'🤷 Код пока не пришёл.\n\n<i>Подожди и попробуй ещё раз.</i>'
            
            await callback_query.message.edit_text(text=text,reply_markup=refresh_markup(account),parse_mode="HTML")
            logging.info(f'| Отключение: [{account.login}]')
            account.disconnect()


def genmarkup():
    markup = InlineKeyboardMarkup()
    markup.row_width = 1
    for account in get_mail_list():
        username, domain = account.login.split('@')
        markup.add(InlineKeyboardButton(text=f'{username}', callback_data=f'get_code_{account.login}'))
    return markup

def refresh_markup(account):
    markup = InlineKeyboardMarkup()
    markup.row_width = 1
    markup.add(InlineKeyboardButton(text=f'♻️ Обновить', callback_data=f'get_code_{account.login}'))
    return markup

class Mail:

    def __init__(self, login, pswd, imap_domain) -> None:
        self.login = login
        self.pswd = pswd
        self.imap_domain = imap_domain
        self.connection = None
    
    def connect(self) -> IMAP4_SSL:
        try:
            self.connection = IMAP4_SSL(self.imap_domain)
            self.connection.login(self.login, self.pswd)
        except Exception as e:
            return e
        
    def disconnect(self):
        try:
            self.connection.logout(self.login, self.pswd)
        except Exception as e:
            return e

    def get_last_email_subject(self, sender_email, target_subject):
        try:
            self.connection.select("INBOX")
            res_code, data = self.connection.search(None, "ALL")
            id_list = data[0].split()
            for id in reversed(id_list[-3:]):
                res_code, msg = self.connection.fetch(id, "(RFC822)")
                raw_email = msg[0][1]
                raw_email_string = raw_email.decode('utf-8')
                email_message = email.message_from_string(raw_email_string)
                message_from = email.utils.parseaddr(email_message['From'])[1]
                if message_from == sender_email and email_message['Subject'] == target_subject:
                    return email_message
            return None
        except Exception as E:
            logging.info(E)
            return None

    def extract_verification_code(self, email_message):
        code = None
        for part in email_message.walk():
            if part.get_content_type() == "text/plain":
                body = part.get_payload(decode=True).decode("utf-8")
                match = re.search(r'\d{6}', body)
                if match:
                    code = match.group()
        return code
    
    def get_rgl_code(self):
        sender_email = "noreply@rockstargames.com"
        target_subject = "Your Rockstar Games verification code"
        email_message = self.get_last_email_subject(sender_email, target_subject)
        if email_message:
            verification_code = self.extract_verification_code(email_message)
            if verification_code:
                email_date = parsedate_to_datetime(email_message['Date'])
                dict = {
                    'mail': self.login,
                    'code': verification_code,
                    'time': email_date
                }
                return dict


def get_mail_list():
    with open('mail.txt', 'r') as file:
        lines = file.read().splitlines()
        accounts = []
        for line in lines:
            parts = line.split(';')
            if len(parts) == 3:
                imap_domain, login, pswd = parts
                account = Mail(imap_domain=imap_domain, login=login, pswd=pswd)
                accounts.append(account)
    return accounts


def genmarkup():
    markup = InlineKeyboardMarkup()
    markup.row_width = 1
    for account in get_mail_list():
        username, domain = account.login.split('@')
        markup.add(InlineKeyboardButton(text=f'{username}', callback_data=f'get_code_{account.login}'))
    return markup

def refresh_markup(account):
    markup = InlineKeyboardMarkup()
    markup.row_width = 1
    markup.add(InlineKeyboardButton(text=f'♻️ Обновить', callback_data=f'get_code_{account.login}'))
    return markup

class Mail:

    def __init__(self, login, pswd, imap_domain) -> None:
        self.login = login
        self.pswd = pswd
        self.imap_domain = imap_domain
        self.connection = None
    
    def connect(self) -> IMAP4_SSL:
        try:
            self.connection = IMAP4_SSL(self.imap_domain)
            self.connection.login(self.login, self.pswd)
        except Exception as e:
            return e
        
    def disconnect(self):
        try:
            self.connection.logout(self.login, self.pswd)
        except Exception as e:
            return e

    def get_last_email_subject(self, sender_email, target_subject):
        try:
            self.connection.select("INBOX")
            res_code, data = self.connection.search(None, "ALL")
            id_list = data[0].split()
            for id in reversed(id_list[-3:]):
                res_code, msg = self.connection.fetch(id, "(RFC822)")
                raw_email = msg[0][1]
                raw_email_string = raw_email.decode('utf-8')
                email_message = email.message_from_string(raw_email_string)
                message_from = email.utils.parseaddr(email_message['From'])[1]
                if message_from == sender_email and email_message['Subject'] == target_subject:
                    return email_message
            return None
        except Exception as E:
            logging.info(E)
            return None

    def extract_verification_code(self, email_message):
        code = None
        for part in email_message.walk():
            if part.get_content_type() == "text/plain":
                body = part.get_payload(decode=True).decode("utf-8")
                match = re.search(r'\d{6}', body)
                if match:
                    code = match.group()
        return code
    
    def get_rgl_code(self):
        sender_email = "noreply@rockstargames.com"
        target_subject = "Your Rockstar Games verification code"
        email_message = self.get_last_email_subject(sender_email, target_subject)
        if email_message:
            verification_code = self.extract_verification_code(email_message)
            if verification_code:
                email_date = parsedate_to_datetime(email_message['Date'])
                dict = {
                    'mail': self.login,
                    'code': verification_code,
                    'time': email_date
                }
                return dict


def get_mail_list():
    with open('mail.txt', 'r') as file:
        lines = file.read().splitlines()
        accounts = [
            Mail(imap_domain=parts[0], login=parts[1], pswd=parts[2])
            for parts in (line.split(';') for line in lines)
            if len(parts) == 3
        ]
    return accounts