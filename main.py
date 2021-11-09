import datetime
import json
import logging
import logging.config
import os
import random
import re
from functools import wraps
from random import choice
from typing import List

from telegram import Update, TelegramError, Chat, ParseMode, Bot, BotCommandScopeAllPrivateChats, BotCommand, User, \
    InlineKeyboardButton, InlineKeyboardMarkup
from telegram.error import BadRequest
from telegram.ext import Updater, CommandHandler, CallbackContext, Filters, MessageHandler, CallbackQueryHandler
from telegram.utils import helpers

from emojis import Emojis, EmojiButton
import utilities
from mwt import MWT
from config import config

emojis = Emojis(max_codepoints=1)


def load_logging_config(file_name='logging.json'):
    with open(file_name, 'r') as f:
        logging_config = json.load(f)

    logging.config.dictConfig(logging_config)


load_logging_config("logging.json")

logger = logging.getLogger(__name__)


@MWT(timeout=60 * 60)
def get_admin_ids(bot: Bot, chat_id: int):
    return [admin.user.id for admin in bot.get_chat_administrators(chat_id)]


def administrators(func):
    @wraps(func)
    def wrapped(update: Update, context: CallbackContext, *args, **kwargs):
        if update.effective_user.id not in get_admin_ids(context.bot, update.effective_chat.id):
            logger.debug("admin check failed")
            return

        return func(update, context, *args, **kwargs)

    return wrapped


def fail_with_message(answer_to_message=True):
    def real_decorator(func):
        @wraps(func)
        def wrapped(update: Update, context: CallbackContext, *args, **kwargs):
            try:
                return func(update, context, *args, **kwargs)
            except Exception as e:
                error_str = str(e)
                logger.error('error while running callback: %s', error_str, exc_info=True)
                if answer_to_message:
                    update.message.reply_text("error")

        return wrapped
    return real_decorator


def get_captcha():
    def real_decorator(func):
        @wraps(func)
        def wrapped(update: Update, context: CallbackContext, *args, **kwargs):
            if not (update.effective_user.id in context.chat_data and "captcha" in context.chat_data[update.effective_user.id]):
                update.callback_query.answer("Captcha expired")
                utilities.safe_delete(update.callback_query.message)

                context.chat_data.pop(update.effective_user.id, None)
                return

            captcha = context.chat_data[update.effective_user.id]["captcha"]

            if captcha.user_id != update.effective_user.id:
                update.callback_query.answer("You are not supposed to solve this captcha", show_alert=True)
                return

            result_captcha = func(update, context, captcha, *args, **kwargs)
            if result_captcha:
                result_captcha.updated_on = utilities.now_utc()
                context.chat_data[update.effective_user.id]["captcha"] = result_captcha

        return wrapped
    return real_decorator


class EmojiCaptcha:
    def __init__(
            self,
            user: User,
            chat: Chat,
            number_of_correct_emojis: int,  # number of emojis in the image (that are marked as correct in the keyboard)
            number_of_buttons: int = 8,  # number of keyboard buttons
            allowed_errors: int = 2  # number of errors the user is allowed to do
    ):
        if number_of_buttons % 2 != 0:
            raise ValueError("the number of buttons must be even")

        self.user_id = user.id
        self.chat_id = chat.id
        self.number_of_correct_emojis = number_of_correct_emojis
        self.number_of_buttons = number_of_buttons
        self.errors = 0
        self.allowed_errors = allowed_errors

        now = utilities.now_utc()
        self.created_on = now
        self.updated_on = now

        self.emojis: List[EmojiButton] = []

        self.gen_emojis()

    def gen_emojis(self):
        random_emojis = emojis.random(count=self.number_of_buttons)

        self.emojis = [EmojiButton.convert(e) for e in random_emojis]

        for i in range(self.number_of_correct_emojis):
            # mark the first emojis as correct, then we will shuffle the list
            self.emojis[i].correct = True

        random.shuffle(self.emojis)

    def get_reply_markup(self, rows=2):
        if not self.emojis:
            self.gen_emojis()

        keyboard = []
        # max two lines of emojis
        buttons_per_row = int(self.number_of_buttons / rows)
        i = 0
        for row_number in range(rows):
            buttons_row = []
            for column_number in range(buttons_per_row):
                emoji = self.emojis[i]
                button = InlineKeyboardButton(emoji.unicode, callback_data=emoji.callback_data)

                buttons_row.append(button)
                i += 1

            keyboard.append(buttons_row)

        return InlineKeyboardMarkup(keyboard)

    def add_error(self, errors_to_add=1):
        self.errors += errors_to_add
        return self.errors

    def remaining_attempts(self):
        return self.allowed_errors - self.errors

    def correct_answers(self):
        return sum(e.already_selected and e.correct for e in self.emojis)

    def get_emoji(self, emoji_id):
        for emoji in self.emojis:
            if emoji.id == emoji_id:
                return emoji

        raise ValueError(f"emoji_id (hex codepoints) not found: {emoji_id}")

    def mark_as_selected(self, emoji_id):
        for i, emoji in enumerate(self.emojis):
            if emoji.id == emoji_id:
                self.emojis[i].already_selected = True
                return

        raise ValueError(f"emoji_id (hex codepoints) not found: {emoji_id}")

    def __str__(self):
        emojis_list = [f"{type(e).__name__}(id={e.id})" for e in self.emojis]
        emojis_string = "\n\t".join(emojis_list)

        return f"{type(self).__name__}(\n\t{emojis_string}\n)"


@fail_with_message()
def on_private_chat_message(update: Update, context: CallbackContext):
    logger.debug("new captcha for %d", update.effective_user.id)

    captcha = EmojiCaptcha(
        update.effective_user,
        update.effective_chat,
        number_of_correct_emojis=3,
        number_of_buttons=10,
    )
    update.message.reply_text(f"You are allowed {captcha.remaining_attempts()} error(s) and 10 minutes to solve the test", reply_markup=captcha.get_reply_markup())

    context.chat_data[update.effective_user.id] = {"captcha": captcha}


@fail_with_message(answer_to_message=False)
@get_captcha()
def on_already_selected_button(update: Update, context: CallbackContext, captcha: EmojiCaptcha):
    update.callback_query.answer("You already selected this emoji", cache_time=60*60*24)


@fail_with_message(answer_to_message=False)
@get_captcha()
def on_button(update: Update, context: CallbackContext, captcha: EmojiCaptcha):
    emoji_id = context.match[1]
    logger.info("user selected emoji: %s", emoji_id)

    emoji = captcha.get_emoji(emoji_id)
    logger.debug("emoji: %s (correct: %s)", emoji.codepoints_hex, emoji.correct)

    captcha.mark_as_selected(emoji.id)

    new_text = ""
    if emoji.correct:
        update.callback_query.answer(f"Good job! {captcha.number_of_correct_emojis - captcha.correct_answers()} to go")
    else:
        errors = captcha.add_error()
        if errors > captcha.allowed_errors:
            update.callback_query.edit_message_text(f"Too many errors ({errors})", reply_markup=None)
            return captcha
        elif captcha.remaining_attempts() == 0:
            new_text = "You are no longer allowed to make mistakes"
            update.callback_query.answer(f"Error!")
        else:
            s_or_not = "s" if captcha.remaining_attempts() > 1 else ""
            new_text = f"You are still allowed {captcha.remaining_attempts()} error{s_or_not}"
            update.callback_query.answer(f"Error!")

    reply_markup = captcha.get_reply_markup()
    if new_text:
        update.callback_query.edit_message_text(new_text, reply_markup=reply_markup)
    else:
        update.callback_query.edit_message_reply_markup(reply_markup=reply_markup)

    return captcha


def main():
    updater = Updater(config.telegram.token, workers=1)
    dispatcher = updater.dispatcher

    dispatcher.add_handler(MessageHandler(Filters.chat_type.private, on_private_chat_message))

    dispatcher.add_handler(CallbackQueryHandler(on_already_selected_button, pattern=r'^button:already_(?:solved|error)$'))
    dispatcher.add_handler(CallbackQueryHandler(on_button, pattern=r'^button:(.*)$'))

    updater.bot.set_my_commands([])  # make sure the bot doesn't have any command set...
    updater.bot.set_my_commands(  # ...then set the scope for private chats
        [
            BotCommand("start", "get the welcome message"),
            BotCommand("help", "get the help message")
        ],
        scope=BotCommandScopeAllPrivateChats()
    )

    allowed_updates = ["message", "callback_query"]  # https://core.telegram.org/bots/api#getupdates

    logger.info("running as @%s, allowed updates: %s", updater.bot.username, allowed_updates)
    updater.start_polling(drop_pending_updates=True, allowed_updates=allowed_updates)


if __name__ == '__main__':
    main()
