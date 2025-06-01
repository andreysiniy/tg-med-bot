import telegram
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from telegram.ext import ContextTypes, ConversationHandler
from clients.backend_api_client import BackendApiClient
from datetime import date, timedelta, datetime
import db.mongodb_service as db
import logging

logger = logging.getLogger(__name__)
db = db.Database()

class EditHandler:
    """
    Handler for editing appointments.
    This class implements the logic for editing appointments.
    It retrieves the user's appointments from the backend API and allows the user to select an appointment to edit.
    It also handles the case where the user has no appointments.
    """

    CHOOSE_APPOINTMENT, EDIT_APPOINTMENT_DATE, EDIT_APPOINTMENT_TIME, CONFIRMATION = range(6, 10)

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
    async def start_appointment_editing(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """
        Starts the appointment editing process by prompting the user to choose an appointment.
        Args:
            update (Update): The update object containing the message.
            context (ContextTypes.DEFAULT_TYPE): The context object for the conversation.
        """
        context.user_data.clear()
        context.user_data.setdefault("edit_appointment_data", {})
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
                await update.message.reply_text("У вас нет записей на прием для редактирования.")
                return
            temp_id = 1
            response_text = "Выберете запись, которую нужно отредактировать:\n\n"
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
            options = [f"Запись #{i + 1}" for i in range(len(appointments))]
            keyboard = await self._create_keyboard(options, items_per_row=2, add_back_button=True, back_button_text="Отмена")
            await update.message.reply_text("Выберите запись для редактирования:", reply_markup=keyboard)
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
            await update.message.reply_text("Пожалуйста, зарегистрируйтесь перед редактированием записей.")
            return ConversationHandler.END

        selected_option = update.message.text
        if "Запись" not in selected_option:
            await update.message.reply_text("Пожалуйста, выберите корректную запись для редактирования.")
            return await self.prompt_appointment_choosing(update, context)
        
        appointment_index = int(selected_option.split("#")[1].strip()) - 1
        appointments = await BackendApiClient().get_appointments_by_user_uuid(user_uuid)
        if not appointments:
            await update.message.reply_text("У вас нет записей на прием для редактирования.")
            return ConversationHandler.END

        if selected_option == "Отмена":
            return await self.cancel(update, context)

        if appointment_index < 0 or appointment_index >= len(appointments):
            await update.message.reply_text("Некорректный выбор записи. Пожалуйста, попробуйте снова.")
            return await self.prompt_appointment_choosing(update, context)
        
        context.user_data['selected_appointment'] = appointments[appointment_index]
        

        return await self.prompt_edit_appointment_date(update, context)
    
    async def prompt_edit_appointment_date(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """
        Prompts the user to edit the date of the selected appointment.
        
        Args:
            update (Update): The update object containing the message.
            context (ContextTypes.DEFAULT_TYPE): The context object for the conversation.
        Returns:
            int: The next step in the conversation.
        """
        start_date_val = date.today()
        dates_next_two_weeks = []
        for i in range(14):
            next_date = start_date_val + timedelta(days=i)
            dates_next_two_weeks.append(next_date.strftime("%Y-%m-%d"))
        keyboard = await self._create_keyboard(dates_next_two_weeks, items_per_row=3, back_button_text="Назад (к выбору записи)")
        await update.effective_message.reply_text("Выберите новую дату приема:", reply_markup=keyboard)
        return self.EDIT_APPOINTMENT_DATE
                
    async def choose_appointment_date(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """
        Handles the user's choice of new appointment date.
        
        Args:
            update (Update): The update object containing the message.
            context (ContextTypes.DEFAULT_TYPE): The context object for the conversation.
        Returns:
            int: The next step in the conversation.
        """
        selected_date = update.message.text
        if selected_date == "Назад (к выбору записи)":
            context.user_data.pop('selected_appointment', None)
            return await self.prompt_appointment_choosing(update, context)
        
        context.user_data['edit_appointment_data']['new_date'] = selected_date

        return await self.prompt_edit_appointment_time(update, context)

    async def prompt_edit_appointment_time(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """
        Prompts the user to edit the time of the selected appointment.
        
        Args:
            update (Update): The update object containing the message.
            context (ContextTypes.DEFAULT_TYPE): The context object for the conversation.
        Returns:
            int: The next step in the conversation.
        """
        times = await BackendApiClient().get_doctor_working_hours(
            doctor_id=context.user_data['selected_appointment'].get("doctorId"),
            date=context.user_data['edit_appointment_data'].get('new_date')
        )
        keyboard = await self._create_keyboard(times, items_per_row=3, back_button_text="Назад (к выбору даты)")
        await update.effective_message.reply_text("Выберите новое время приема:", reply_markup=keyboard)
        return self.EDIT_APPOINTMENT_TIME
    
    async def choose_appointment_time(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """
        Handles the user's choice of new appointment time.
        
        Args:
            update (Update): The update object containing the message.
            context (ContextTypes.DEFAULT_TYPE): The context object for the conversation.
        Returns:
            int: The next step in the conversation.
        """
        selected_time = update.message.text
        if selected_time == "Назад (к выбору даты)":
            context.user_data['edit_appointment_data'].pop('new_date', None)
            return await self.prompt_edit_appointment_date(update, context)
        
        context.user_data['edit_appointment_data']['new_time'] = selected_time

        return await self.prompt_edit_confirm(update, context)
    
    async def prompt_edit_confirm(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """
        Prompts the user to confirm the changes made to the appointment.
        Args:
            update (Update): The update object containing the message.
            context (ContextTypes.DEFAULT_TYPE): The context object for the conversation.
        Returns:
            int: The next step in the conversation.
        """
        selected_appointment = context.user_data['selected_appointment']
        new_date = context.user_data['edit_appointment_data'].get('new_date')
        new_time = context.user_data['edit_appointment_data'].get('new_time')
        doctor_card = await BackendApiClient().get_doctor_card(selected_appointment.get("doctorId"))
        clinic_card = await BackendApiClient().get_clinic_card(doctor_card.get("clinicId"))

        confirmation_text = (
            f"Вы уверены, что хотите изменить запись на прием?\n\n"
            f"Врач: <b>{doctor_card.get('name')}</b>\n"
            f"Клиника: <b>{clinic_card.get('name')}</b>\n"
            f"Старая дата и время: <b>{selected_appointment.get('appointmentTime')}</b>\n"
            f"Новая дата: <b>{new_date}</b>\n"
            f"Новое время: <b>{new_time}</b>\n"
        )
        
        keyboard = ReplyKeyboardMarkup(
            [["Да", "Нет"]],
            one_time_keyboard=True,
            resize_keyboard=True
        )
        
        await update.effective_message.reply_text(confirmation_text, parse_mode='HTML', reply_markup=keyboard)
        return self.CONFIRMATION
    

    async def confirm_edit(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """
        Confirms the changes made to the appointment.
        
        Args:
            update (Update): The update object containing the message.
            context (ContextTypes.DEFAULT_TYPE): The context object for the conversation.
        Returns:
            int: The next step in the conversation.
        """
        if update.message.text == "Да":
            user_id = update.effective_user.id
            user_uuid = db.get_user_uuid(user_id)

            dt_object = None
            try:
                date_obj = datetime.strptime(context.user_data['edit_appointment_data']['new_date'], "%Y-%m-%d").date()
                time_obj = datetime.strptime(context.user_data['edit_appointment_data']['new_time'], "%H:%M").time()
                dt_object_combined = datetime.combine(date_obj, time_obj)
                logger.info(f"Selected date and time: {dt_object_combined}")
                if dt_object_combined < datetime.now():
                    await update.effective_message.reply_text(
                        "Выбранная дата и время уже прошли. Пожалуйста, выберите другую дату и время."
                    )
                    context.user_data['edit_appointment_data'].pop('new_date', None)
                    context.user_data['edit_appointment_data'].pop('new_time', None)
                    return await self.prompt_edit_appointment_date(update, context)                
                dt_object = dt_object_combined.isoformat()
            except ValueError as e:
                logger.error(f"Error parsing date or time: {e}")
                await update.message.reply_text("Некорректный формат даты или времени. Пожалуйста, попробуйте снова.")
                context.user_data['edit_appointment_data'].pop('new_date', None)
                context.user_data['edit_appointment_data'].pop('new_time', None)
                return await self.prompt_edit_appointment_date(update, context)

            request_body = {
                "appointmentId": context.user_data['selected_appointment'].get("appointmentId"),
                "patientName": context.user_data['selected_appointment'].get("patientName"),
                "patientUuid": user_uuid,
                "phone": context.user_data['selected_appointment'].get("phone"),
                "appointmentTime": dt_object,
                "doctorId": context.user_data['selected_appointment'].get("doctorId")
            }

            new_date = context.user_data['edit_appointment_data'].get('new_date')
            new_time = context.user_data['edit_appointment_data'].get('new_time')
            selected_appointment = context.user_data['selected_appointment']

            
            await BackendApiClient().put_appointment(
                appointment_id=selected_appointment.get("appointmentId"),
                data=request_body
            )
            await update.message.reply_text("Запись успешно изменена!")
            context.user_data.clear() 
            return ConversationHandler.END

        else:
            return await self.cancel(update, context)
    
    async def cancel(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """
        Cancels the appointment editing process.
        
        Args:
            update (Update): The update object containing the message.
            context (ContextTypes.DEFAULT_TYPE): The context object for the conversation.
        Returns:
            int: The next step in the conversation.
        """
        await update.message.reply_text("Редактирование записи отменено.", reply_markup=ReplyKeyboardRemove())
        context.user_data.clear()
        return ConversationHandler.END