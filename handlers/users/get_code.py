from aiogram import types
from loader import dp
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import re
from imaplib import IMAP4_SSL
import email
from email.utils import parsedate_to_datetime
from aiogram import md
from data.config import admins, get_access_list,mail_list
import logging
from utils.misc import rate_limit
from .start import get_access_markup

class MailAcc:

    def __init__(self, login, pswd, imap_domain) -> None:
        self.login = login
        self.pswd = pswd
        self.imap_domain = imap_domain
        self.connection = None
        self.connected = False
    
    def _connect(self) -> IMAP4_SSL:
        logging.info(f'| Подключение: [{self.login}]')
        if not self.connection:
            connection = IMAP4_SSL(self.imap_domain)
            try:
                connection_status = connection.login(self.login, self.pswd)
                logging.info(f'| Статус: [{connection_status[0]}]')
                if connection_status[0] == 'OK':
                    self.connection = connection
                    self.connected = True
            except Exception as e:
                self.connected = False
                return e
        else:
            logging.info(f'| Уже подключен: [{self.login}]')
        
    def disconnect(self):
        logging.info(f'| Отключение: [{self.login}]')
        if self.connection:
            disconnect_status = self.connection.logout()
            logging.info(f'| Статус: [{disconnect_status[0]}]')
            self.connection = None

    def get_last_email_subject(self, sender_email, target_subject):
        if self.connection:
            logging.info(f'| Поиск писем от: [{sender_email}]')
            self.connection.select("INBOX")
            res_code, data = self.connection.search(None, "ALL")
            id_list = data[0].split()
            tries = 0
            for id in reversed(id_list):
                if tries > 3: break
                tries +=1
                res_code, msg = self.connection.fetch(id, "(RFC822)")
                raw_email = msg[0][1]
                raw_email_string = raw_email.decode('utf-8')
                email_message = email.message_from_string(raw_email_string)
                message_from = email.utils.parseaddr(email_message['From'])[1]
                if message_from == sender_email and email_message['Subject'] == target_subject:
                    logging.info(f'| Письмо найдено: [{sender_email}]')
                    return email_message
            return None
    
    def extract_verification_code(self, email_message):
        code = None
        if email_message:
            for part in email_message.walk():
                if part.get_content_type() == "text/plain":
                    body = part.get_payload(decode=True).decode("utf-8")
                    logging.info(f'| body: [{body}]')
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
            status = account._connect()
            if account.connected:
                data = account.get_rgl_code()
                logging.info(f'| Получен ответ: [{data}]')
                if data:
                    time = data["time"].strftime('%H:%M')
                    text =  f'Код: <b>{md.quote_html(data["code"])}</b>\n'\
                            f'Время: <code>{md.quote_html(time)}</code>\n'\
                            f'Почта: <code>{md.quote_html(data["mail"])}</code>'
                else:
                    text =  f'🤷 Код пока не пришёл.\n\n<i>Подожди и попробуй ещё раз.</i>'
            else:
                text =  f'🤷 Не получилось подключится к аккаунту.\n {status}'
            await callback_query.message.edit_text(text=text,reply_markup=refresh_markup(account),parse_mode="HTML")
            account.disconnect()

    await dp.bot.answer_callback_query(callback_query.id)



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


def get_mail_list():
    accounts = []
    for account in mail_list:
        parts = account.split(';')
        if len(parts) == 3:
            imap_domain, login, pswd = parts
            account = MailAcc(imap_domain=imap_domain, login=login, pswd=pswd)
            accounts.append(account)
    return accounts


def refresh_markup(account):
    markup = InlineKeyboardMarkup()
    markup.row_width = 1
    markup.add(InlineKeyboardButton(text=f'♻️ Обновить', callback_data=f'get_code_{account.login}'))
    return markup