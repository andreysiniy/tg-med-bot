import telegram
from telegram import Update, User, BotCommand, Message
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from telegram.constants import ParseMode, ChatAction
import logging
import db.mongodb_service as db
from helpers.configurator import Config
from llmservices.google_service import GoogleService

# Configure logging
db = db.Database()
logger = logging.getLogger(__name__)
class TelegramBotInitializer:
    """
    A class to initialize a Telegram bot with the provided token.
    This class encapsulates the logic for creating a Telegram bot instance.
    """
    def __init__(self):
        """
        Initializes the Telegram bot with the provided token.

        Args:
            token (str): The bot token provided by BotFather.
        """
        self.bot = self.initialize_telegram_bot()

    def initialize_telegram_bot(self) -> None:
        """
        Initializes the Telegram bot with the provided token.

        Args:
            token (str): The bot token provided by BotFather.

        Returns:
            telegram.Bot: An instance of the Telegram Bot.
        """
        try:
            application = (
                ApplicationBuilder()
                .token(Config().get("TELEGRAM", "token"))
                .http_version("1.1")
                .build()
            )
            application.add_handler(CommandHandler("start", self.start_command))
            application.add_handler(MessageHandler(filters.TEXT, self.default_response))
            
            application.run_polling()
            logger.info("Telegram bot initialized successfully.")
            
        except Exception as e:
            logger.error(f"Failed to initialize Telegram bot: {e}")
            raise
    
    async def register_user_if_not_exists(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Registers a user in the database if they do not already exist.

        Args:
            update (Update): The update containing the message from the user.
            context (ContextTypes.DEFAULT_TYPE): The context of the command.
        """
        user: User = update.effective_user
        if not db.check_if_user_exists(user.id):
            db.add_user(
                user_id=user.id,
                chat_id=update.effective_chat.id,
                username=user.username or "",
                first_name=user.first_name or "",
                last_name=user.last_name or ""
            )
            logger.info(f"User {user.username} registered successfully.")
        else:
            logger.info(f"User {user.username} already exists in the database.")
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handles the /start command.

        Args:
            update (Update): The update containing the message from the user.
            context (ContextTypes.DEFAULT_TYPE): The context of the command.
        """
        await self.register_user_if_not_exists(update, context)
        await update.message.reply_text(
            "Добро пожаловать! Я ваш Telegram бот для записи на прием к врачу. Чем могу помочь?",
            parse_mode=ParseMode.HTML
        )
    
    async def default_response(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handles any text message that does not match a command.

        Args:
            update (Update): The update containing the message from the user.
            context (ContextTypes.DEFAULT_TYPE): The context of the command.
        """
        reply_msg = await GoogleService().generate_json_text(update.message.text)
        await self.register_user_if_not_exists(update, context)
        await update.message.reply_text(
            f"Ваш запрос обработан. Ответ: {reply_msg}",
            parse_mode=ParseMode.HTML
        )

