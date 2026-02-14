import logging

import telegram
from asgiref.sync import async_to_sync
from django.conf import settings

logger = logging.getLogger(__name__)


async def _send_message(chat_id, text, **kwargs):
    async with telegram.Bot(token=settings.TELEGRAM_BOT_TOKEN) as bot:
        return await bot.send_message(chat_id=chat_id, text=text, **kwargs)


def send_message(chat_id, text, **kwargs):
    try:
        return async_to_sync(_send_message)(chat_id, text, **kwargs)
    except telegram.error.TelegramError as e:
        logger.warning("Telegram error: %s", e)


def send_contact_request(chat_id, text):
    keyboard = telegram.ReplyKeyboardMarkup(
        [[telegram.KeyboardButton("Share phone number", request_contact=True)]],
        resize_keyboard=True,
        one_time_keyboard=True,
    )
    return send_message(chat_id, text, reply_markup=keyboard)


def send_remove_keyboard(chat_id, text):
    return send_message(
        chat_id, text, reply_markup=telegram.ReplyKeyboardRemove()
    )


async def _set_webhook():
    async with telegram.Bot(token=settings.TELEGRAM_BOT_TOKEN) as bot:
        return await bot.set_webhook(
            url=settings.TELEGRAM_WEBHOOK_URL,
            secret_token=settings.TELEGRAM_WEBHOOK_SECRET or None,
            allowed_updates=["message"],
        )


async def _delete_webhook():
    async with telegram.Bot(token=settings.TELEGRAM_BOT_TOKEN) as bot:
        return await bot.delete_webhook()


def set_webhook():
    return async_to_sync(_set_webhook)()


def delete_webhook():
    return async_to_sync(_delete_webhook)()
