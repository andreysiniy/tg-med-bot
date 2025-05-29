from aiohttp import ClientSession
import datetime

class BackendApiClient:
    def __init__(self):
        """
        Initializes the Backend API client with the base URL.
        """
        self.base_url = "http://localhost:5136/api/"
        self.session = ClientSession()

    async def post(self, endpoint: str, data: dict) -> dict:
        """
        Sends a POST request to the specified endpoint with the provided data.

        Args:
            endpoint (str): The API endpoint to send the request to.
            data (dict): The data to include in the POST request.

        Returns:
            dict: The JSON response from the API.
        """
        url = f"{self.base_url}{endpoint}"
        async with self.session.post(url, json=data) as response:
            response.raise_for_status()
            return await response.json()
    
    async def get(self, endpoint: str, params: dict = None) -> dict:
        """
        Sends a GET request to the specified endpoint with the provided parameters.

        Args:
            endpoint (str): The API endpoint to send the request to.
            params (dict, optional): The query parameters to include in the GET request.

        Returns:
            dict: The JSON response from the API.
        """
        url = f"{self.base_url}{endpoint}"
        async with self.session.get(url, params=params) as response:
            response.raise_for_status()
            return await response.json()
    
    async def get_clinic_card(self, clinic_id: int) -> dict:
        """
        Retrieves clinic cards by clinic ID.

        Args:
            clinic_id (int): The ID of the clinic to retrieve cards for.

        Returns:
            dict: The JSON response containing the clinic cards.
        """
        return await self.get(f"ClinicCards/{clinic_id}")
    
    async def get_clinic_cards(self) -> dict:
        """
        Retrieves all clinic cards.

        Returns:
            dict: The JSON response containing the clinic cards.
        """
        return await self.get(f"ClinicCards/")
    
    async def get_doctor_cards(self) -> dict:
        """
        Retrieves all doctor cards.

        Returns:
            dict: The JSON response containing the doctor cards.
        """
        return await self.get(f"DoctorCards/")
    
    async def get_doctor_card(self, doctor_id: int) -> dict:
        """
        Retrieves a doctor card by doctor ID.

        Args:
            doctor_id (int): The ID of the doctor to retrieve the card for.

        Returns:
            dict: The JSON response containing the doctor card.
        """
        return await self.get(f"DoctorCards/{doctor_id}")
    
    async def get_doctor_working_hours(self, doctor_id: int, date: datetime) -> dict:
        """
        Retrieves the working hours of a doctor for a specific date.

        Args:
            doctor_id (int): The ID of the doctor.
            date (datetime): The date for which to retrieve the working hours.

        Returns:
            dict: The JSON response containing the doctor's working hours.
        """
        return await self.get(f"DoctorCards/{doctor_id}/timeslots/{date.strftime("%Y-%m-%d")}")
    
    async def get_doctor_containting_name(self, name: str) -> dict:
        """
        Retrieves doctor cards containing a specific name.

        Args:
            name (str): The name to search for in doctor cards.

        Returns:
            dict: The JSON response containing the doctor cards that match the name.
        """
        return await self.get(f"DoctorCards/name/{name}")
    
    async def get_doctor_containting_specialization(self, specialization: str) -> dict:
        """
        Retrieves doctor cards containing a specific specialization.

        Args:
            specialization (str): The specialization to search for in doctor cards.

        Returns:
            dict: The JSON response containing the doctor cards that match the specialization.
        """
        return await self.get(f"DoctorCards/speciality/{specialization}")
    
    async def get_appointment(self, appointment_id: int) -> dict:
        """
        Retrieves an appointment by its ID.

        Args:
            appointment_id (int): The ID of the appointment to retrieve.

        Returns:
            dict: The JSON response containing the appointment details.
        """
        return await self.get(f"Appointment/{appointment_id}")
    
    async def get_appointments(self) -> dict:
        """
        Retrieves an appointment by its ID.

        Args:
            appointment_id (int): The ID of the appointment to retrieve.

        Returns:
            dict: The JSON response containing the appointment details.
        """
        return await self.get(f"Appointment/")
    
    async def post_appointment(self, data: dict) -> dict:
        """
        Creates a new appointment with the provided data.

        Args:
            data (dict): The data for the new appointment.

        Returns:
            dict: The JSON response containing the created appointment details.
        """
        return await self.post("Appointment", data)
    
