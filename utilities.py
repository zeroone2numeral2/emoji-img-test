import datetime
from html import escape

from telegram import Message


def now_utc():
    return datetime.datetime.utcnow()


def html_escape(string: str):
    return escape(string)


def safe_delete(message: Message):
    # noinspection PyBroadException
    try:
        message.delete()
    except Exception:
        pass

