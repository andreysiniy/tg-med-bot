from google import genai
from google.genai import types
from helpers.configurator import Config
from datetime import datetime
import json
import re

class GoogleService:
    def __init__(self):
        self.token = Config().get("GOOGLE", "token")
        self.default_model = Config().get("GOOGLE", "model")

    async def generate_json_text(self, prompt: str, max_tokens: int = 500) -> str:
        client = genai.Client(api_key=Config().get("GOOGLE", "token"))
        
        response = client.models.generate_content(
            model=self.default_model,
            config=types.GenerateContentConfig(
                system_instruction=
                """
                Ты работаешь в роле чат-бота ассистента регистратуры клиники. 
                Твоя задача, на основе предоставленной информации понять интент пользователя, 
                хочет ли он записаться на прием к врачу, перенести существующий прием, удалить существующий прием,
                узнать информацию о враче или клинике, или задать другой вопрос. в качечстве ответа дай только JSON в формате:
                {
                    "intent": "<интент>",
                    "data": # данные, которые ты можешь извлечь из текста пользователя если они есть
                    {
                        "doctor": "Имя врача", # при наличии
                        "speialization": "Специализация врача", # при наличии
                        "clinic": "Название клиники", # при наличии
                        "date": "Дата приема", # при наличии (важно в формате YYYY-MM-DD, если время указано без даты не указана, то считай завтрашнюю дату)
                        "time": "Время приема" # при наличии (важно в формате HH:MM)
                        "question": "Вопрос пользователя" # при наличии
                    }
                }
                <интент> может быть одним из следующих: "book_appointment", "reschedule_appointment", "cancel_appointment", 
                "view_appointments", "other_question".
                Важно, чтобы ты отлавливал очевидные ошибки в запросах пользователя, например, если он пытается записаться на прием к врачу на уже прошедшую дату,
                или пытается перенести прием на дату, которая уже прошла (для этого вместе с сообщением пользователя передается текущая дата и время, важно сверяться с ними).
                Если не можешь понять интент или он не соответствует, дай ответ в формате:
                {
                    "intent": "unknown",
                    "reason": "Причина непонимания запроса"
                }
                """
                
            ),
            contents = f"Запрос пользователя: ({prompt}), Сегодня - {datetime.now().strftime('%Y-%m-%d')}, время - {datetime.now().strftime('%H:%M')}"
        )
        json_string = response.text
        try:
            parsed_json = json.loads(json_string)
        except json.JSONDecodeError:

            error_reason = "Модель вернула невалидный JSON."
            raw_text_for_error = json_string if 'json_string' in locals() else "No text received from model"

            match = re.search(r"```json\s*([\s\S]*?)\s*```", raw_text_for_error, re.DOTALL)
            if match:
                extracted_json_string = match.group(1).strip()
                try:
                    parsed_json = json.loads(extracted_json_string)
                    return parsed_json # Успех с извлечением
                except json.JSONDecodeError:
                    error_reason = "Модель вернула невалидный JSON даже после извлечения из блока кода."
                    raw_text_for_error = extracted_json_string

            return {
                "intent": "unknown",
                "reason": error_reason,
                "raw_output": raw_text_for_error
            }
        except Exception as e:
            # Обработка других ошибок API или неожиданных проблем
            # Например, google.api_core.exceptions.PermissionDenied (403) если ключ неверный
            # google.api_core.exceptions.ResourceExhausted (429) если превышены квоты
            return {
                "intent": "unknown",
                "reason": f"Произошла ошибка API или внутренняя ошибка: {type(e).__name__} - {str(e)}",
                "raw_output": None
            }
        return parsed_json