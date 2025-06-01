from aiohttp import ClientSession
import datetime
from typing import Optional
from typing import List, Dict, Union
import logging

logger = logging.getLogger(__name__)

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
            logger.info(f"POST {url} with data {data} returned status {response.status}")
            #await self.close()
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
            logger.info(f"GET {url} with params {params} returned status {response.status}")
            #await self.close()
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
        api_response = await self.get(f"DoctorCards/{doctor_id}/timeslots/{date}")
        if isinstance(api_response, list):
            formatted_hours = [
                time_str[:5]
                for time_str in api_response 
                if isinstance(time_str, str) and len(time_str) >= 5
            ]
        return formatted_hours
    
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
    
    async def get_specific_doctors(
        self,
        clinic_id: Optional[int] = None,
        specialization: Optional[str] = None,
        name: Optional[str] = None,
        date: datetime = None
    ) -> dict:
        """
        Retrieves specific doctors by clinic ID and specialization.

        Args:
            clinic_id (int): The ID of the clinic.
            specialization (str): The specialization to filter doctors by.
            name (str): The name to filter doctors by.
            date (datetime): The date for which to filter doctors by their availability.
        If no parameters are provided, it retrieves all doctors.

        Returns:
            dict: The JSON response containing the specific doctors.
        """
        base_url = "DoctorCards"
        query_params = {}
        if clinic_id:
            query_params["clinicId"] = clinic_id
        if specialization:
            query_params["speciality"] = specialization
        if name:
            query_params["name"] = name
        if date:
            query_params["appointmentDate"] = date.strftime('%Y-%m-%dT%H:%M')
        query_string = "&".join(f"{key}={value}" for key, value in query_params.items())
        if query_string:
            return await self.get(f"{base_url}?{query_string}")
        else:
            return await self.get(base_url)
       
    async def get_clinic_by_name(self, name: str) -> dict:
        """
        Retrieves a clinic by its name.
        Args:
            name (str): The name of the clinic to retrieve.
        Returns:
            dict: The JSON response containing the clinic details.
        """
        return await self.get(f"ClinicCards/name/{name}")
    
    async def get_specializations(
        self,
        clinic_id: Optional[int] = None,
        specialization: Optional[str] = None,
        name: Optional[str] = None,
        date: datetime = None
    ) -> dict:
        """
        Retrieves specializations by clinic ID and specialization.

        Args:
            clinic_id (int): The ID of the clinic.
            specialization (str): The specialization to filter by.
            name (str): The name to filter by.
            date (datetime): The date for which to filter specializations.

        Returns:
            dict: The JSON response containing the specializations.
        """
        base_url = "DoctorCards/speciality"
        query_params = {}
        if clinic_id:
            query_params["clinicId"] = clinic_id
        if specialization:
            query_params["speciality"] = specialization
        if name:
            query_params["name"] = name
        if date:
            query_params["appointmentDate"] = date.strftime('%Y-%m-%dT%H:%M')
        query_string = "&".join(f"{key}={value}" for key, value in query_params.items())
        
        
        if query_string:
            api_response_list = await self.get(f"{base_url}?{query_string}")
        else:
            api_response_list = await self.get(f"{base_url}")

        transformed_specializations: List[Dict[str, Union[int, str]]] = []
        if isinstance(api_response_list, list):
            for index, spec_name in enumerate(api_response_list):
                if isinstance(spec_name, str): # Ensure the item from the list is a string
                    transformed_specializations.append({"id": index, "name": spec_name})
                else:
                    # Log a warning or handle non-string items as needed
                    logger.warning(f"Encountered non-string item in specializations list from API: {spec_name}")
        return transformed_specializations
    
    async def get_appointments_by_user_uuid(self, user_uuid: str) -> List[dict]:
        """
        Retrieves appointments by user UUID.

        Args:
            user_uuid (str): The UUID of the user to retrieve appointments for.

        Returns:
            List[dict]: A list of JSON responses containing the user's appointments.
        """
        return await self.get(f"Appointment/user/{user_uuid}")
    
    async def close(self):
        """
        Closes the HTTP session.
        """
        await self.session.close()
        logger.info("Backend API client session closed.")