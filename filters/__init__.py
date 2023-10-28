from aiogram import Dispatcher
from .admincommand import AdminCommand


def setup(dp: Dispatcher):
    dp.filters_factory.bind(AdminCommand)