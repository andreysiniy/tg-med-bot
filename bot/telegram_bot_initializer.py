import telegram
from telegram import Update, User, BotCommand
from telegram.ext import Application, ApplicationBuilder, CallbackContext, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler
from telegram.constants import ParseMode 
import logging
import db.mongodb_service as db
from helpers.configurator import Config
from llmservices.google_service import GoogleService
from clients.backend_api_client import BackendApiClient
from handlers.create_step_handler import CreateStepHandler

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
        self.step_handler_instance = CreateStepHandler()
        self.conv_handler: ConversationHandler | None = None
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
            self.application = (
                ApplicationBuilder()
                .token(Config().get("TELEGRAM", "token"))
                .http_version("1.1")
                .build()
            )
            

            self.conv_handler = ConversationHandler(
            entry_points=[CommandHandler("new_appointment", self.step_handler_instance.start_appointment_creation),
                          MessageHandler(filters.TEXT & ~filters.COMMAND, self.default_response)
                          ],
            states={
                CreateStepHandler.CHOOSE_CLINIC: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.step_handler_instance.process_clinic_choice)],
                CreateStepHandler.CHOOSE_SPECIALIZATION: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.step_handler_instance.process_specialization_choice)],
                CreateStepHandler.CHOOSE_DOCTOR: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.step_handler_instance.process_doctor_choice)],
                CreateStepHandler.CHOOSE_DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.step_handler_instance.process_date_choice)], # Обрабатывает дату и предлагает время
                CreateStepHandler.CHOOSE_TIME: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.step_handler_instance.process_time_choice)],
                CreateStepHandler.CONFIRMATION: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.step_handler_instance.process_confirmation)],
            },
            fallbacks=[CommandHandler("cancel", self.step_handler_instance.cancel)],

        )
            self.application.add_handler(self.conv_handler)
            
            self.application.add_handler(CommandHandler("start", self.start_command))
            self.application.add_handler(CommandHandler("gettest", self.gettest_command))
            

            self.application.run_polling()
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
        logger.info(f"Received message: {update.message.text}")
        logger.info(f"Generated reply: {reply_msg}")

        if not reply_msg:
            await update.message.reply_text(
                "Извините, я не смог понять ваш запрос. Пожалуйста, попробуйте переформулировать."
            )
        
        if reply_msg.get("intent") == "unknown":
            await update.message.reply_text(
                f"Не могу понять ваш запрос: {reply_msg.get('reason', 'Неизвестная ошибка')} Пожалуйста, попробуйте переформулировать."
            )
            return

        logger.info(f"handlers: {self.conv_handler.entry_points}")
        if reply_msg.get("intent") == "book_appointment":
            return await self.step_handler_instance.start_appointment_creation(update, context)


        await update.message.reply_text(
            f"Ваш запрос обработан. Ответ: {reply_msg}",
            parse_mode=ParseMode.HTML
        )

    async def gettest_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handles the /test command.

        Args:
            update (Update): The update containing the message from the user.
            context (ContextTypes.DEFAULT_TYPE): The context of the command.
        """

        logger.info(f"handlers: {self.conv_handler.entry_points}")
        uuid = db.get_user_uuid(update.effective_user.id)
        await update.message.reply_text(
            f"Ваш UUID: <b>{uuid}</b>",
            parse_mode=ParseMode.HTML
        )
