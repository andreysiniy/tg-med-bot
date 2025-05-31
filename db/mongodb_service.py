from typing import Optional, Any

import pymongo
import uuid
from datetime import datetime

class Database:
    def __init__(self):
        """
        Initializes the MongoDB client and connects to the database.
        """
        self.client = pymongo.MongoClient("mongodb://localhost:27017/")
        self.db = self.client["telegram_bot_db"]

        self.user_collection = self.db["user"]
        self.dialog_collection = self.db["dialog"]
    
    def check_if_user_exists(self, user_id: int) -> bool:
        """
        Checks if a user exists in the database.

        Args:
            user_id (int): The ID of the user to check.

        Returns:
            bool: True if the user exists, False otherwise.
        """
        return self.user_collection.count_documents({"user_id": user_id}) > 0
    
    def add_user(self, 
        user_id: int,
        chat_id: int, 
        username: str = str, 
        first_name: str = "", 
        last_name: str = ""
    ):
        user_dict = {
            "user_id": user_id,
            "chat_id": chat_id,
            "username": username,
            "user_uuid": str(uuid.uuid4()),
            "first_name": first_name,
            "last_name": last_name,
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        }
        if not self.check_if_user_exists(user_id):
            self.user_collection.insert_one(user_dict)

    def get_user_uuid(self, user_id: int) -> Optional[str]:
        """
        Retrieves the UUID of a user by their user ID.

        Args:
            user_id (int): The ID of the user.

        Returns:
            Optional[str]: The UUID of the user if found, None otherwise.
        """
        user = self.user_collection.find_one({"user_id": user_id}, {"user_uuid": 1})
        return user["user_uuid"] if user else None
    
    def get_user_fullname(self, user_id: int) -> Optional[str]:
        """
        Retrieves the username of a user by their user ID.

        Args:
            user_id (int): The ID of the user.

        Returns:
            Optional[str]: The username of the user if found, None otherwise.
        """
        user_firstname = self.user_collection.find_one({"user_id": user_id}, {"first_name": 1})
        user_lastname = self.user_collection.find_one({"user_id": user_id}, {"last_name": 1})
        user = user_firstname.get("first_name", "") +  ' ' + user_lastname.get("last_name", "")
        return user if user else None