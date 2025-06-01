import telegram
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from telegram.ext import ContextTypes, ConversationHandler
from clients.backend_api_client import BackendApiClient
from datetime import date, timedelta, datetime
import db.mongodb_service as db
import logging

logger = logging.getLogger(__name__)
db = db.Database()

class DeleteHandler:
    """
    Handler for deleting appointments.
    This class implements the logic for deleting appointments.
    It retrieves the user's appointments from the backend API and allows the user to select an appointment to delete.
    """

    CHOOSE_APPOINTMENT, CONFIRMATION = range(10,12)

    async def _create_keyboard(self, options: list, items_per_row: int = 2, 
                               add_back_button: bool = True, back_button_text: str = "Назад") -> ReplyKeyboardMarkup:
        """ 
        Creates a keyboard layout for the given options.
        
        Args:
            options (list): List of options to create buttons for.
            items_per_row (int): Number of buttons per row.
            add_back_button (bool): Whether to add a "Back" button.
            back_button_text (str): Text for the "Back" button.
        Returns:
            ReplyKeyboardMarkup: A keyboard markup object with the specified options.
        
        """
        buttons = [KeyboardButton(option) for option in options]
        keyboard_layout = [buttons[i:i + items_per_row] for i in range(0, len(buttons), items_per_row)]
        if add_back_button:
            keyboard_layout.append([KeyboardButton(back_button_text)])
        return ReplyKeyboardMarkup(
            keyboard_layout,
            one_time_keyboard=True,
            resize_keyboard=True
        )

    async def start_appointment_deletion(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """
        Starts the appointment editing process by prompting the user to choose an appointment.
        Args:
            update (Update): The update object containing the message.
            context (ContextTypes.DEFAULT_TYPE): The context object for the conversation.
        """
        context.user_data.clear()
        context.user_data.setdefault("delete_appointment_data", {})
        return await self.prompt_appointment_choosing(update, context)


    async def prompt_appointment_choosing(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """
        Starts the appointment editing process by retrieving the user's appointments.
        
        Args:
            update (Update): The update object containing the message.
            context (ContextTypes.DEFAULT_TYPE): The context object for the conversation.
        Returns:
            int: The next step in the conversation.
        """
        user_id = update.effective_user.id
        user_uuid = db.get_user_uuid(user_id)

        if not user_uuid:
            await update.message.reply_text("Пожалуйста, зарегистрируйтесь перед редактированием записей.")
            return

        try:
            appointments = await BackendApiClient().get_appointments_by_user_uuid(user_uuid)
            if not appointments:
                await update.message.reply_text("У вас нет записей на прием для отмены.")
                return
            temp_id = 1
            response_text = "Выберете запись, которую нужно удалить:\n\n"
            for appointment in appointments:
                doctor_card = await BackendApiClient().get_doctor_card(appointment.get("doctorId"))
                clinic_card = await BackendApiClient().get_clinic_card(doctor_card.get("clinicId"))
                appointment_time_str = appointment.get("appointmentTime")
                dt_object = datetime.fromisoformat(appointment_time_str)
                formatted_time = dt_object.strftime("%d.%m %H:%M")
                response_text += (
                    f"Запись на прием <b>#{temp_id}:</b>\n"
                    f"Врач: <b>{doctor_card.get('name').title()}</b>\n"
                    f"Номер телефона: <b>{doctor_card.get('phoneNumber')}</b>\n"
                    f"Специализация: <b>{doctor_card.get('speciality').title()}</b>\n"
                    f"Клиника: <b>{clinic_card.get('name').title()}</b>\n"
                    f"Адрес: <b>{clinic_card.get('location').title()}</b>\n"
                    f"Телефон клиники: <b>{clinic_card.get('phone')}</b>\n"
                    f"Дата и время приема: <b>{formatted_time}</b>\n"
                    f"\n"
                )
                temp_id += 1            
            await update.message.reply_text(response_text, parse_mode='HTML')
            options = [f"Запись #{i + 1}" for i in range(len(appointments))]
            keyboard = await self._create_keyboard(options, items_per_row=2, add_back_button=True, back_button_text="Отмена")
            await update.message.reply_text("Выберите запись для отмены:", reply_markup=keyboard)
            return self.CHOOSE_APPOINTMENT

        except Exception as e:
            logger.error(f"Error fetching appointments: {e}")
            await update.message.reply_text("Произошла ошибка при получении записей. Пожалуйста, попробуйте позже.")
    
    async def choose_appointment(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """
        Handles the user's choice of appointment to edit.
        
        Args:
            update (Update): The update object containing the message.
            context (ContextTypes.DEFAULT_TYPE): The context object for the conversation.
        Returns:
            int: The next step in the conversation.
        """
        user_id = update.effective_user.id
        user_uuid = db.get_user_uuid(user_id)

        if not user_uuid:
            await update.message.reply_text("Пожалуйста, зарегистрируйтесь перед удалением записей.")
            return ConversationHandler.END

        selected_option = update.message.text
        if "Запись" not in selected_option:
            await update.message.reply_text("Пожалуйста, выберите корректную запись для удаления.")
            return await self.prompt_appointment_choosing(update, context)
        
        appointment_index = int(selected_option.split("#")[1].strip()) - 1
        appointments = await BackendApiClient().get_appointments_by_user_uuid(user_uuid)
        if not appointments:
            await update.message.reply_text("У вас нет записей на прием для удаления.")
            return ConversationHandler.END

        if selected_option == "Отмена":
            return await self.cancel(update, context)

        if appointment_index < 0 or appointment_index >= len(appointments):
            await update.message.reply_text("Некорректный выбор записи. Пожалуйста, попробуйте снова.")
            return await self.prompt_appointment_choosing(update, context)
        
        context.user_data['selected_appointment'] = appointments[appointment_index]
        

        return await self.prompt_delete_confirm(update, context)
    
    async def prompt_delete_confirm(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """
        Prompts the user to confirm the deletion of the appointment.
        Args:
            update (Update): The update object containing the message.
            context (ContextTypes.DEFAULT_TYPE): The context object for the conversation.
        Returns:
            int: The next step in the conversation.
        """
        selected_appointment = context.user_data['selected_appointment']
        doctor_card = await BackendApiClient().get_doctor_card(selected_appointment.get("doctorId"))
        clinic_card = await BackendApiClient().get_clinic_card(doctor_card.get("clinicId"))
        appointment_time_str = selected_appointment.get("appointmentTime")
        dt_object = datetime.strftime(datetime.fromisoformat(appointment_time_str), "%d.%m в %H:%M")

        confirmation_text = (
            f"Вы уверены, что хотите удалить запись на прием?\n\n"
            f"Врач: <b>{doctor_card.get('name').title()}</b>\n"
            f"Клиника: <b>{clinic_card.get('name').title()}</b>\n"
            f"Дата и время: <b>{dt_object}</b>\n"
        )
        
        keyboard = ReplyKeyboardMarkup(
            [["Да", "Нет"]],
            one_time_keyboard=True,
            resize_keyboard=True
        )
        
        await update.effective_message.reply_text(confirmation_text, parse_mode='HTML', reply_markup=keyboard)
        return self.CONFIRMATION
    
    async def confirm_delete(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """
        Handles the user's confirmation to delete the appointment.
        
        Args:
            update (Update): The update object containing the message.
            context (ContextTypes.DEFAULT_TYPE): The context object for the conversation.
        Returns:
            int: The next step in the conversation.
        """
        if update.message.text == "Да":
            selected_appointment = context.user_data['selected_appointment']
            user_uuid = db.get_user_uuid(update.effective_user.id)
            if not user_uuid:
                await update.message.reply_text("Пожалуйста, зарегистрируйтесь перед удалением записей.")
                return ConversationHandler.END
            
            try:
                await BackendApiClient().delete_appointment(selected_appointment.get("appointmentId"), user_uuid)
                await update.message.reply_text("Запись успешно удалена.")
            except Exception as e:
                logger.error(f"Error deleting appointment: {e}")
                await update.message.reply_text("Произошла ошибка при удалении записи. Пожалуйста, попробуйте позже.")
            
            return ConversationHandler.END
        
        elif update.message.text == "Нет":
            await update.message.reply_text("Удаление записи отменено.")
            context.user_data.clear()
            return ConversationHandler.END
        
        else:
            await update.message.reply_text("Пожалуйста, ответьте 'Да' или 'Нет'.")
            return self.prompt_delete_confirm(update, context)

    async def cancel(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """
        Cancels the appointment deletion process.
        
        Args:
            update (Update): The update object containing the message.
            context (ContextTypes.DEFAULT_TYPE): The context object for the conversation.
        Returns:
            int: The next step in the conversation.
        """
        await update.message.reply_text("Удаление записи отменено.", reply_markup=ReplyKeyboardRemove())
        context.user_data.clear()
        return ConversationHandler.END