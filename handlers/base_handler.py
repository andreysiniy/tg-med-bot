import asyncio
import clients.backend_api_client as BackendApiClient

class BaseHandler:
    """
        Base class for all handlers.
        This class should be inherited by all specific handlers.
        It provides a common interface for handling requests.
    """
    #def __init__(self):
        

    async def handle(self):
        raise NotImplementedError("Subclasses must implement the handle method.")


class CreateAppointmentHandler(BaseHandler):
    """
        Handler for creating appointments.
        This class should implement the logic for creating appointments.
    """
    
    async def handle(self, data):
        # Implement the logic for creating an appointment
        pass

class CreateSpecificAppointmentHandler(CreateAppointmentHandler):
    """
        Handler for creating specific appointments.
        This class should implement the logic for creating specific appointments.
    """
    def __init__(self, data : dict):
        """
            Initializes the handler with specific appointment data.
            Args:
                data (dict): The data for the specific appointment.
        """
        self.data = data if isinstance(data, dict) else {}
        self.create_appointment_data = dict()
        self.user_interaction_order = [
            "clinic",
            "specialization",
            "doctor",
            "date",
            "time",
            "phone_number"
        ]

    async def handle_clinic_step(self, clinic: str):
        """
            Handles the clinic step of the appointment creation.
            Args:
                clinic (str): The name of the clinic.
        """
        clinics = await BackendApiClient.get_clinic_containting_name(clinic)

    async def handle_data_steps(self, data: dict):
        """
            Handles the data for creating a specific appointment.
            Args:
                data (dict): The data for the specific appointment.
        """
        interactions_mapping = {
            "clinic": lambda : self.handle_clinic_step(self.data.get("clinic", "")),
            "specialization": "specialization",
            "doctor": "doctor",
            "date": "date",
            "time": "time",
            "phone_number": "phone_number"
        }

    async def handle(self, data : dict):
        self.user_interaction_order = [
            step for step in self.base_interaction_order 
            if step not in self.data
        ]


        

class CancelAppointmentHandler(BaseHandler):
    """
        Handler for canceling appointments.
        This class should implement the logic for canceling appointments.
    """
    
    async def handle(self, appointment_id: int):
        # Implement the logic for canceling an appointment
        pass

class RescheduleAppointmentHandler(BaseHandler):
    """
        Handler for rescheduling appointments.
        This class should implement the logic for rescheduling appointments.
    """
    
    async def handle(self, appointment_id: int, new_date: str, new_time: str):
        # Implement the logic for rescheduling an appointment
        pass

class HelpHandler(BaseHandler):
    """
        Handler for providing help information.
        This class should implement the logic for providing help information.
    """
    
    async def handle(self):
        # Implement the logic for providing help information
        pass