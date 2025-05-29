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
