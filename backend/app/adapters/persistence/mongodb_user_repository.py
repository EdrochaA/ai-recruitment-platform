"""
MongoDB User Repository Adapter
Implementation of UserRepositoryPort using MongoDB
"""

from typing import Optional
from datetime import datetime
from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError
from bson.objectid import ObjectId

from app.domain.entities.user import User, UserRole
from app.domain.ports.user_repository_port import UserRepositoryPort


class MongoDBUserRepository(UserRepositoryPort):
    """MongoDB implementation of user repository"""
    
    def __init__(self, connection_string: str, database_name: str):
        """Initialize MongoDB connection"""
        self.client = MongoClient(connection_string)
        self.db = self.client[database_name]
        self.users_collection = self.db["users"]
        
        # Create unique index on email
        self.users_collection.create_index("email", unique=True)
    
    async def create_user(self, name: str, email: str, hashed_password: str, role: UserRole) -> User:
        """Create a new user in MongoDB"""
        user_doc = {
            "name": name,
            "email": email,
            "role": role.value,
            "hashed_password": hashed_password,
            "created_at": datetime.utcnow(),
        }
        
        try:
            result = self.users_collection.insert_one(user_doc)
            user_doc["_id"] = str(result.inserted_id)
            return self._doc_to_user(user_doc)
        except DuplicateKeyError:
            raise ValueError(f"User with email {email} already exists")
    
    async def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email from MongoDB"""
        user_doc = self.users_collection.find_one({"email": email})
        
        if not user_doc:
            return None
        
        return self._doc_to_user(user_doc)
    
    async def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Get user by ID from MongoDB"""
        try:
            user_doc = self.users_collection.find_one({"_id": ObjectId(user_id)})
            
            if not user_doc:
                return None
            
            return self._doc_to_user(user_doc)
        except Exception:
            return None
    
    async def user_exists(self, email: str) -> bool:
        """Check if user exists by email"""
        return self.users_collection.find_one({"email": email}) is not None
    
    def _doc_to_user(self, doc: dict) -> User:
        """Convert MongoDB document to User domain model"""
        return User(
            id=str(doc["_id"]),
            name=doc["name"],
            email=doc["email"],
            role=UserRole(doc["role"]),
            created_at=doc.get("created_at", datetime.utcnow()),
            hashed_password=doc.get("hashed_password", "")
        )
    
    def close(self):
        """Close MongoDB connection"""
        self.client.close()
