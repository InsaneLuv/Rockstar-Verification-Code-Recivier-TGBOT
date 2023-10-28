import logging
from threading import Thread

from flask import Flask

app = Flask('')


@app.route('/')
def home():
    return "Bot is online now."


def run():
    app.run(host='0.0.0.0', port=80)


def create_host():
    logging.info("Creating host...")
    t = Thread(target=run)
    t.start()
