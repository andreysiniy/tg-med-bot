import telegram
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from telegram.ext import ContextTypes, ConversationHandler
from clients.backend_api_client import BackendApiClient
from datetime import date, timedelta, datetime
import db.mongodb_service as db
import logging

logger = logging.getLogger(__name__)
db = db.Database()

class ViewHandler:
    """
    Handler for viewing appointments.
    This class implements the logic for viewing appointments.
    It retrieves the user's appointments from the backend API and formats them for display.
    It also handles the case where the user has no appointments.
    """


    async def handle(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        user_uuid = db.get_user_uuid(user_id)

        if not user_uuid:
            await update.message.reply_text("Пожалуйста, зарегистрируйтесь перед просмотром записей.")
            return

        try:
            appointments = await BackendApiClient().get_appointments_by_user_uuid(user_uuid)
            temp_id = 1
            response_text = "Ваши записи на прием:\n\n"
            for appointment in appointments:
                doctor_card = await BackendApiClient().get_doctor_card(appointment.get("doctorId"))
                clinic_card = await BackendApiClient().get_clinic_card(doctor_card.get("clinicId"))
                appointment_time_str = appointment.get("appointmentTime")
                dt_object = datetime.fromisoformat(appointment_time_str)
                formatted_time = dt_object.strftime("%d.%m %H:%M")
                response_text += (
                    f"Запись на прием <b>#{temp_id}:</b>\n"
                    f"Врач: <b>{doctor_card.get('name')}</b>\n"
                    f"Номер телефона: <b>{doctor_card.get('phoneNumber')}</b>\n"
                    f"Специализация: <b>{doctor_card.get('speciality')}</b>\n"
                    f"Клиника: <b>{clinic_card.get('name')}</b>\n"
                    f"Адрес: <b>{clinic_card.get('location')}</b>\n"
                    f"Телефон клиники: <b>{clinic_card.get('phone')}</b>\n"
                    f"Дата и время приема: <b>{formatted_time}</b>\n"
                    f"\n"
                )
                temp_id += 1
            await update.message.reply_text(response_text, parse_mode='HTML')
            if not appointments:
                await update.message.reply_text("У вас нет записей на прием.")
        except Exception as e:
            logger.error(f"Error fetching appointments: {e}")
            await update.message.reply_text("Произошла ошибка при получении записей. Пожалуйста, попробуйте позже.")