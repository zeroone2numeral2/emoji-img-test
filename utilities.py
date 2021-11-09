import datetime

from telegram import Message


def now_utc():
    return datetime.datetime.utcnow()


def safe_delete(message: Message):
    # noinspection PyBroadException
    try:
        message.delete()
    except Exception:
        pass

