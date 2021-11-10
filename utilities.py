import datetime
import logging
import os
import pickle
from html import escape

# noinspection PyPackageRequirements
from telegram import Message, User
# noinspection PyPackageRequirements
from telegram.ext import PicklePersistence

logger = logging.getLogger(__name__)


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
        return True
    except Exception:
        return False


def persistence_object(file_path='persistence/data.pickle'):
    logger.info('unpickling persistence: %s', file_path)
    try:
        # try to load the file
        try:
            with open(file_path, "rb") as f:
                pickle.load(f)
        except FileNotFoundError:
            pass
    except (pickle.UnpicklingError, EOFError):
        logger.warning('deserialization failed: removing persistence file and trying again')
        os.remove(file_path)

    return PicklePersistence(
        filename=file_path,
        store_chat_data=True,
        store_user_data=True,
        store_bot_data=False
    )

