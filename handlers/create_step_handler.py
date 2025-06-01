import telegram
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from telegram.ext import ContextTypes, ConversationHandler
from clients.backend_api_client import BackendApiClient
from datetime import date, timedelta, datetime
from typing import Optional
import db.mongodb_service as db
import logging

logger = logging.getLogger(__name__)


db = db.Database()
class CreateStepHandler:
    """
    Handles button interactions in the Telegram bot.
    This class provides methods to create and manage buttons for user interactions.
    """

    (CHOOSE_CLINIC, CHOOSE_SPECIALIZATION, CHOOSE_DOCTOR, 
     CHOOSE_DATE, CHOOSE_TIME, CONFIRMATION) = range(6)
    

    

    #def __init__(self):
        #self.context.user_data.setdefault("create_appointment_data", {})

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

    async def start_appointment_creation(self, update: Update, context: ContextTypes.DEFAULT_TYPE, prefilled_data: Optional[dict] = None) -> int:
        """
        Starts the appointment creation process by prompting the user to select a clinic.
        
        Args:
            update (Update): The Telegram update containing the user's message.
            context (ContextTypes.DEFAULT_TYPE): The context containing user data.
        Returns:
            int: The next state in the conversation flow.
        """
        context.user_data.clear()
        context.user_data.setdefault("create_appointment_data", {})
        context.user_data["prefilled_info"] = prefilled_data or {} 
        return await self.prompt_clinic(update, context)

    # ---- Step 1: Clinic Selection ----
    async def prompt_clinic(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """
        Prompts the user to select a clinic from the available options.
        If no clinics are available, informs the user and ends the conversation.
        
        Args:
            update (Update): The Telegram update containing the user's message.
            context (ContextTypes.DEFAULT_TYPE): The context containing user data.
        Returns:
            int: The next state in the conversation flow, CHOOSE_CLINIC.
        """
        prefilled_clinic = context.user_data["prefilled_info"].get("clinic", None)
        if prefilled_clinic:
            clinics = await BackendApiClient().get_clinic_by_name(name=prefilled_clinic)
        else:
            clinics = await BackendApiClient().get_clinic_cards()
        if not clinics:
            await update.effective_message.reply_text("Извините, в данный момент нет доступных клиник.")
            return ConversationHandler.END
        
        clinic_names = [clinic["name"] for clinic in clinics]
        context.user_data["_temp_clinics_list"] = clinics # Сохраняем для быстрой выборки

        keyboard = await self._create_keyboard(clinic_names, items_per_row=1, add_back_button=True, back_button_text="Отмена")
        await update.effective_message.reply_text("Выберите клинику:", reply_markup=keyboard)
        return self.CHOOSE_CLINIC

    async def process_clinic_choice(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """
        Processes the user's choice of clinic.
        If the user selects a clinic, stores the clinic ID and name in the appointment data.
        If the user cancels, ends the conversation.
        
        Args:
            update (Update): The Telegram update containing the user's message.
            context (ContextTypes.DEFAULT_TYPE): The context containing user data.
        Returns:
            int: The next state in the conversation flow, CHOOSE_SPECIALIZATION.

        """
        chosen_clinic_name = update.message.text
        user_data = context.user_data
        appointment_data = user_data["create_appointment_data"]

        if chosen_clinic_name == "Отмена":
            return await self.cancel(update, context)

        selected_clinic = None
        for clinic in user_data.get("_temp_clinics_list", []):
            if clinic["name"] == chosen_clinic_name:
                selected_clinic = clinic
                break
        
        if not selected_clinic:
            await update.effective_message.reply_text("Пожалуйста, выберите клинику из списка.")
            return await self.prompt_clinic(update, context) # Повторить запрос клиники

        appointment_data["clinic_id"] = selected_clinic["clinicId"]
        appointment_data["clinic_name"] = selected_clinic["name"]
        user_data.pop("_temp_clinics_list", None) # Очистить временные данные   
        logger.info(f"Selected clinic: {appointment_data['clinic_name']} (ID: {appointment_data['clinic_id']})")
        return await self.prompt_specialization(update, context)

    # ---- Step 2: Specialization Selection ----
    async def prompt_specialization(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """
        Prompts the user to select a specialization from the available options based on the selected clinic.
        If no specializations are available, informs the user and prompts to select a clinic again.
        Args:
            update (Update): The Telegram update containing the user's message.
            context (ContextTypes.DEFAULT_TYPE): The context containing user data.
        Returns:
            int: The next state in the conversation flow, CHOOSE_SPECIALIZATION.
        """
        clinic_id = context.user_data["create_appointment_data"].get("clinic_id")
        prefilled_spec = context.user_data["prefilled_info"].get("specialization", None)
        prefilled_doc = context.user_data["prefilled_info"].get("doctor", None)
        prefilled_date = context.user_data["prefilled_info"].get("date", None)
        prefilled_time = context.user_data["prefilled_info"].get("time", None)
        if prefilled_date and prefilled_time:
            prefilled_datetime = f"{prefilled_date}T{prefilled_time}"
        else:
            prefilled_datetime = None


        specializations = await BackendApiClient().get_specializations(clinic_id=clinic_id, 
                specialization=prefilled_spec, name=prefilled_doc, date=prefilled_datetime)
        if not specializations:
            await update.effective_message.reply_text("Нет доступных специализаций.")
            return await self.prompt_clinic(update, context)

        spec_names = [spec["name"] for spec in specializations]
        context.user_data["_temp_specs_list"] = specializations

        keyboard = await self._create_keyboard(spec_names, items_per_row=3, back_button_text="Назад (к клинике)")
        await update.effective_message.reply_text("Выберите специальность врача:", reply_markup=keyboard)
        return self.CHOOSE_SPECIALIZATION

    async def process_specialization_choice(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """
        Processes the user's choice of specialization.
        If the user selects a specialization, stores the specialization ID and name in the appointment data.
        And if the user chooses to go back to the clinic selection, removes the clinic data and prompts for clinic selection again.
        Args:
            update (Update): The Telegram update containing the user's message.
            context (ContextTypes.DEFAULT_TYPE): The context containing user data.
        Returns:
            int: The next state in the conversation flow, CHOOSE_DOCTOR.
        """
        chosen_spec_name = update.message.text
        user_data = context.user_data
        appointment_data = user_data["create_appointment_data"]

        if chosen_spec_name == "Назад (к клинике)":
            appointment_data.pop("clinic_id", None)
            appointment_data.pop("clinic_name", None)
            return await self.prompt_clinic(update, context)

        selected_spec = None
        for spec in user_data.get("_temp_specs_list", []):
            if spec["name"] == chosen_spec_name:
                selected_spec = spec
                break
        
        if not selected_spec:
            await update.effective_message.reply_text("Пожалуйста, выберите специальность из списка.")
            return await self.prompt_specialization(update, context)

        appointment_data["specialization_id"] = selected_spec["id"]
        appointment_data["specialization_name"] = selected_spec["name"]
        user_data.pop("_temp_specs_list", None)

        return await self.prompt_doctor(update, context)

    # ---- Step 3: Doctor Selection ----
    async def prompt_doctor(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """
        Prompts the user to select a doctor based on the selected specialization and clinic.
        If no doctors are available, informs the user and prompts to select a specialization again.
        Args:
            update (Update): The Telegram update containing the user's message.
            context (ContextTypes.DEFAULT_TYPE): The context containing user data.
        Returns:
            int: The next state in the conversation flow, CHOOSE_DOCTOR.
        """
        prefilled_doc = context.user_data["prefilled_info"].get("doctor", None)
        prefilled_date = context.user_data["prefilled_info"].get("date", None)
        prefilled_time = context.user_data["prefilled_info"].get("time", None)
        if prefilled_date and prefilled_time:
            prefilled_datetime = f"{prefilled_date}T{prefilled_time}"
        else:
            prefilled_datetime = None
        appointment_data = context.user_data["create_appointment_data"]
        doctors = await BackendApiClient().get_specific_doctors(
            specialization=appointment_data.get("specialization_name"),
            clinic_id=appointment_data.get("clinic_id"),
            name=prefilled_doc,
            date=prefilled_datetime
        )
        if not doctors:
            await update.effective_message.reply_text(
                "По выбранной специальности в данной клинике нет врачей. Попробуйте изменить выбор."
            )
            # Вернуть к выбору специализации
            return await self.prompt_specialization(update, context)

        doctor_names = [doc["name"] for doc in doctors]
        context.user_data["_temp_doctors_list"] = doctors

        keyboard = await self._create_keyboard(doctor_names, items_per_row=1, back_button_text="Назад (к специализации)")
        await update.effective_message.reply_text("Выберите врача:", reply_markup=keyboard)
        return self.CHOOSE_DOCTOR
    
    async def process_doctor_choice(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """
        Processes the user's choice of doctor.
        If the user selects a doctor, stores the doctor ID and name in the appointment data.
        If the user chooses to go back to the specialization selection, removes the specialization data and prompts for specialization selection again.
        Args:
            update (Update): The Telegram update containing the user's message.
            context (ContextTypes.DEFAULT_TYPE): The context containing user data.
        Returns:
            int: The next state in the conversation flow, CHOOSE_DATE.
        """
        chosen_doc_name = update.message.text
        user_data = context.user_data
        appointment_data = user_data["create_appointment_data"]

        if chosen_doc_name == "Назад (к специализации)":
            appointment_data.pop("specialization_id", None)
            appointment_data.pop("specialization_name", None)
            return await self.prompt_specialization(update, context)

        selected_doc = None
        for doc in user_data.get("_temp_doctors_list", []):
            if doc["name"] == chosen_doc_name:
                selected_doc = doc
                break
        
        if not selected_doc:
            await update.effective_message.reply_text("Пожалуйста, выберите врача из списка.")
            return await self.prompt_doctor(update, context)

        appointment_data["doctor_id"] = selected_doc["doctorId"]
        appointment_data["doctor_name"] = selected_doc["name"]
        user_data.pop("_temp_doctors_list", None)
        
        return await self.prompt_date(update, context)    

    # ---- Step 4: Date Selection ----
    async def prompt_date(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """
        Prompts the user to select a date for the appointment.
        Generates a list of dates for the next two weeks starting from today.
        Args:
            update (Update): The Telegram update containing the user's message.
            context (ContextTypes.DEFAULT_TYPE): The context containing user data.
        Returns:
            int: The next state in the conversation flow, CHOOSE_DATE.
        """
        prefilled_date = context.user_data["prefilled_info"].get("date", None)
        opts = []
        prefilled_date_obj = datetime.strptime(prefilled_date, "%Y-%m-%d").date() if prefilled_date else None
        if prefilled_date_obj:    
            if prefilled_date_obj > date.today() + timedelta(days=14) or prefilled_date_obj < date.today():
                prefilled_date_obj = None
        start_date_val = date.today()
        dates_next_two_weeks = []
        for i in range(14):
            next_date = start_date_val + timedelta(days=i)
            dates_next_two_weeks.append(next_date.strftime("%Y-%m-%d"))
        if prefilled_date_obj:
            opts.append(prefilled_date_obj.strftime("%Y-%m-%d"))
            keyboard = await self._create_keyboard(options=opts, items_per_row=1, back_button_text="Назад (к врачу)")
        else:
            keyboard = await self._create_keyboard(dates_next_two_weeks, items_per_row=3, back_button_text="Назад (к врачу)")
        await update.effective_message.reply_text("Выберите дату приема:", reply_markup=keyboard)
        return self.CHOOSE_DATE

    async def process_date_choice(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """
        Processes the user's choice of date for the appointment.
        If the user selects a date, stores the date in the appointment data.
        If the user chooses to go back to the doctor selection, removes the doctor data and prompts for doctor selection again.
        Args:
            update (Update): The Telegram update containing the user's message.
            context (ContextTypes.DEFAULT_TYPE): The context containing user data.
        Returns:
            int: The next state in the conversation flow, CHOOSE_TIME.
        """
        chosen_date_str = update.message.text
        user_data = context.user_data
        appointment_data = user_data["create_appointment_data"]

        if chosen_date_str == "Назад (к врачу)":
            appointment_data.pop("doctor_id", None)
            appointment_data.pop("doctor_name", None)
            return await self.prompt_doctor(update, context)

        try:
            datetime.strptime(chosen_date_str, "%Y-%m-%d")
        except ValueError:
            await update.effective_message.reply_text("Некорректный формат даты. Выберите из предложенных.")
            return await self.prompt_date(update, context) 

        appointment_data["chosen_date_str"] = chosen_date_str
        
        prefilled_time = context.user_data["prefilled_info"].get("time", None)


        # Запрашиваем время для выбранной даты
        times = await BackendApiClient().get_doctor_working_hours(
            doctor_id=appointment_data.get("doctor_id"),
            date=chosen_date_str
        )
        
        if not times:
            await update.effective_message.reply_text(
                "На выбранную дату нет доступного времени. Пожалуйста, выберите другую дату."
            )
            appointment_data.pop("chosen_date_str", None)
            return await self.prompt_date(update, context) 

        context.user_data["_temp_available_times"] = times
        if prefilled_time and prefilled_time in times:
            times = [prefilled_time]
        keyboard = await self._create_keyboard(times, items_per_row=3, back_button_text="Назад (к дате)")
        await update.effective_message.reply_text("Выберите время приема:", reply_markup=keyboard)
        return self.CHOOSE_TIME

    # ---- Step 5: Time Selection ----
    async def process_time_choice(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """
        Processes the user's choice of time for the appointment.
        If the user selects a time, validates it against the current date and time.
        If the time is valid, stores it in the appointment data and prompts for confirmation.
        If the user chooses to go back to the date selection, removes the date data and prompts for date selection again.
        Args:
            update (Update): The Telegram update containing the user's message.
            context (ContextTypes.DEFAULT_TYPE): The context containing user data.
        Returns:
            int: The next state in the conversation flow, CONFIRMATION.
        """
        chosen_time_str = update.message.text
        user_data = context.user_data
        appointment_data = user_data["create_appointment_data"]

        if chosen_time_str == "Назад (к дате)":
            appointment_data.pop("chosen_date_str", None)
            user_data.pop("_temp_available_times", None)
            return await self.prompt_date(update, context)

        available_times = user_data.get("_temp_available_times", [])
        if chosen_time_str not in available_times:
            await update.effective_message.reply_text("Пожалуйста, выберите время из списка.")

            keyboard = await self._create_keyboard(available_times, items_per_row=3, back_button_text="Назад (к дате)")
            await update.effective_message.reply_text("Выберите время приема:", reply_markup=keyboard)
            return self.CHOOSE_TIME

        chosen_date_str = appointment_data["chosen_date_str"]
        logger.info(f"Chosen date: {chosen_date_str}, chosen time: {chosen_time_str}")
        dt_object = None
        try:
            date_obj = datetime.strptime(chosen_date_str, "%Y-%m-%d").date()
            time_obj = datetime.strptime(chosen_time_str, "%H:%M").time()
            dt_object_combined = datetime.combine(date_obj, time_obj)
            logger.info(f"Selected date and time: {dt_object_combined}")
            if dt_object_combined < datetime.now():
                await update.effective_message.reply_text(
                    "Выбранная дата и время уже прошли. Пожалуйста, выберите другую дату и время."
                )
                user_data.pop("_temp_available_times", None)
                # Вернуться к выбору даты, так как время на эту дату может быть неактуально
                return await self.prompt_date(update, context)
            
            dt_object = dt_object_combined.strftime("%Y-%m-%dT%H:%M:%S") # ISO формат

        except ValueError:
            await update.effective_message.reply_text("Некорректный формат. Пожалуйста, выберите из списка.")
            keyboard = await self._create_keyboard(available_times, items_per_row=3, back_button_text="Назад (к дате)")
            await update.effective_message.reply_text("Выберите время приема:", reply_markup=keyboard)
            return self.CHOOSE_TIME
        
        if dt_object:
            appointment_data["appointment_datetime_iso"] = dt_object
            user_data.pop("_temp_available_times", None)
            user_data.pop("chosen_date_str", None) # Больше не нужно
            return await self.prompt_confirmation(update, context)
        else:
            # Этого не должно случиться (надеюсь), но на всякий случай, если что-то пошло не так, а то вдруг дата невалидная, ну такое бывает, не? вроде как, но я не знаю
            await update.effective_message.reply_text("Произошла ошибка. Попробуйте снова.")
            return await self.prompt_date(update, context)

    # ---- Step 6: Confirmation ----
    async def prompt_confirmation(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        appointment_data = context.user_data["create_appointment_data"]
        dt_iso = appointment_data.get("appointment_datetime_iso")
        dt_readable = "не определено"
        if dt_iso:
            try:
                dt_readable = datetime.fromisoformat(dt_iso).strftime('%d.%m.%Y в %H:%M')
            except ValueError:
                pass 

        text = (
            "Подтвердите запись:\n"
            f"Клиника: {appointment_data.get('clinic_name', 'N/A')}\n"
            f"Специальность: {appointment_data.get('specialization_name', 'N/A')}\n"
            f"Врач: {appointment_data.get('doctor_name', 'N/A')}\n"
            f"Дата и время: {dt_readable}"
        )
        keyboard = await self._create_keyboard(["Подтвердить", "Изменить", "Отменить"], items_per_row=3, add_back_button=False)
        await update.effective_message.reply_text(text, reply_markup=keyboard)
        return self.CONFIRMATION    

    async def process_confirmation(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        choice = update.message.text
        
        if choice == "Подтвердить":
            request_body = {
                "patientName" : db.get_user_fullname(update.effective_user.id),
                "patientUuid" : db.get_user_uuid(update.effective_user.id),
                "phone" : "+7(999)999-99-99",
                "appointmentTime" : context.user_data["create_appointment_data"]["appointment_datetime_iso"],
                "doctorId" : context.user_data["create_appointment_data"]["doctor_id"]
            }
            logger.info(f"Creating appointment with data: {request_body}")
            response = await BackendApiClient().post_appointment(request_body)
            if response:
                await update.effective_message.reply_text("Вы успешно записаны!", reply_markup=ReplyKeyboardRemove())
                appointment_time_str = response['appointmentTime']
                dt_object = datetime.fromisoformat(appointment_time_str)
                formatted_time = dt_object.strftime("%d.%m %H:%M")
                text = (
                    "Данные записи:\n"
                    f"Пациент: <b>{response['patientName']}</b>\n"
                    f"Клиника: <b>{response['clinicName'].title()}</b>\n"
                    f"Специальность: <b>{response['doctorSpeciality'].title()}</b>\n"
                    f"Врач: <b>{response['doctorName'].title()}</b>\n"
                    f"Дата и время: <b>{formatted_time}</b>"
                )
                await update.effective_message.reply_text(text, parse_mode='HTML')
            else:
                await update.effective_message.reply_text("Не удалось создать запись. Попробуйте позже.", reply_markup=ReplyKeyboardRemove())
            context.user_data.clear()
            return ConversationHandler.END
        
        elif choice == "Изменить":
            # Можно спросить, что именно изменить, или просто вернуть к началу выбора даты (как наиболее вероятный сценарий)
            await update.effective_message.reply_text("Хорошо, давайте изменим детали.")
            # Удаляем последние шаги, чтобы начать с них
            context.user_data["create_appointment_data"].pop("appointment_datetime_iso", None)
            return await self.prompt_date(update, context)

        elif choice == "Отменить":
            return await self.cancel(update, context)
        
        else:
            await update.effective_message.reply_text("Пожалуйста, выберите один из вариантов.")
            return await self.prompt_confirmation(update, context)

    async def cancel(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """
        Cancels the appointment creation process and clears user data.
        Args:
            update (Update): The Telegram update containing the user's message.
            context (ContextTypes.DEFAULT_TYPE): The context containing user data.
        Returns:
            int: ConversationHandler.END to end the conversation.
            """
        await update.effective_message.reply_text(
            "Создание записи отменено.",
            reply_markup=ReplyKeyboardRemove() 
        )
        context.user_data.clear() # Очищаем все данные пользователя для этого диалога
        return ConversationHandler.END



        

