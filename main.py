from bot.telegram_bot_initializer import TelegramBotInitializer
import logging


if __name__ == "__main__":
    # Initialize the Telegram bot with the token
    logging.basicConfig(level=logging.INFO)

    bot_initializer = TelegramBotInitializer()