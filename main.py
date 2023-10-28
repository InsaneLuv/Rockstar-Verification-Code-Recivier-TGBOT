

from aiogram.utils import executor

from utils import create_host

import logging
from rich.logging import RichHandler

FORMAT = "%(message)s"
logging.basicConfig(
    level="INFO", format=FORMAT, datefmt="[%X]", handlers=[RichHandler()]
) 
logger = logging.getLogger("rich")

async def on_startup(dp):

  logging.info("Bot default commands setting up...")
  from utils.set_bot_commands import set_default_commands
  await set_default_commands(dp)
  
  logging.info("Middlewares setting up...")
  import middlewares
  middlewares.setup(dp)

async def on_shutdown(dp):
  await dp.storage.close()
  await dp.storage.wait_closed()


if __name__ == "__main__":
  from handlers import dp
  create_host()
  executor.start_polling(dp, on_startup=on_startup, on_shutdown=on_shutdown,skip_updates=True)

