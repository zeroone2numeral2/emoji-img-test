import datetime
from html import escape

from telegram import Message, User


def now_utc():
    return datetime.datetime.utcnow()


def html_escape(string: str):
    return escape(string)


def mention_escaped(user: User, label="", full_name=False):
    if not label:
        label = user.first_name if not full_name else user.full_name

    return user.mention_html(html_escape(label))


def safe_delete(message: Message):
    # noinspection PyBroadException
    try:
        message.delete()
    except Exception:
        pass

