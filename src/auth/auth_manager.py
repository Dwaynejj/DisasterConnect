import os
import re
from datetime import datetime, timedelta, timezone
from functools import wraps
from typing import Tuple, Dict, Any, Optional

import bcrypt
import jwt
from pymongo import MongoClient

class AuthError(Exception):
    """Custom authentication error."""
    pass

class AuthManager:
    def __init__(self):
        # We assume MONGODB_URI and JWT_SECRET are in environment variables
        self.mongo_uri = os.getenv('MONGODB_URI', 'mongodb://localhost:27017')
        self.jwt_secret = os.getenv('JWT_SECRET', 'super_secret_dev_key')
        self.mongo_client = MongoClient(self.mongo_uri)
        self.db = self.mongo_client.disasterconnect
        self.users = self.db.users
        self.blacklisted_tokens = self.db.token_blacklist
        
        # Ensure TTL index on token blacklist (expires after 8 hours)
        self.blacklisted_tokens.create_index("createdAt", expireAfterSeconds=28800)
        
        self._current_user = None
        self._current_token = None

    def register_user(self, username: str, email: str, password: str, role: str = 'responder') -> Tuple[bool, Any]:
        """Register a new user."""
        # Validate email
        if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            return False, "Invalid email format."
            
        # Check if username or email already exists
        if self.users.find_one({"$or": [{"username": username}, {"email": email}]}):
            return False, "Username or email already exists."
            
        # Hash password
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt(12))
        
        # Create avatar initials
        initials = username[:2].upper() if username else "U"
        
        user_doc = {
            "username": username,
            "email": email,
            "password_hash": password_hash,
            "role": role,
            "created_at": datetime.now(timezone.utc),
            "last_login": None,
            "is_active": True,
            "avatar_initials": initials
        }
        
        result = self.users.insert_one(user_doc)
        return True, str(result.inserted_id)

    def login(self, username_or_email: str, password: str) -> Tuple[bool, Any, Optional[Dict]]:
        """Login and generate JWT."""
        # Convert input to lowercase to support case-insensitive logins
        username_or_email = username_or_email.lower()
        user = self.users.find_one({
            "$or": [
                {"username": username_or_email},
                {"email": username_or_email}
            ]
        })
        
        if not user:
            return False, "Invalid credentials.", None
            
        if not user.get("is_active", True):
            return False, "Account is disabled.", None
            
        if not bcrypt.checkpw(password.encode('utf-8'), user["password_hash"]):
            return False, "Invalid credentials.", None
            
        # Success
        user_id = str(user["_id"])
        payload = {
            "user_id": user_id,
            "username": user["username"],
            "role": user["role"],
            "exp": datetime.now(timezone.utc) + timedelta(hours=8)
        }
        
        token = jwt.encode(payload, self.jwt_secret, algorithm="HS256")
        
        # Update last login
        self.users.update_one({"_id": user["_id"]}, {"$set": {"last_login": datetime.now(timezone.utc)}})
        
        user_dict = {
            "user_id": user_id,
            "username": user["username"],
            "email": user["email"],
            "role": user["role"],
            "avatar_initials": user.get("avatar_initials", "U")
        }
        
        self._current_user = user_dict
        self._current_token = token
        
        return True, token, user_dict

    def verify_token(self, token: str) -> Dict:
        """Decode JWT and verify it isn't blacklisted."""
        if self.blacklisted_tokens.find_one({"token": token}):
            raise AuthError("Token has been invalidated (logged out).")
            
        try:
            payload = jwt.decode(token, self.jwt_secret, algorithms=["HS256"])
            return payload
        except jwt.ExpiredSignatureError:
            raise AuthError("Token has expired.")
        except jwt.InvalidTokenError:
            raise AuthError("Invalid token.")

    def logout(self):
        """Logout by clearing current token and adding to blacklist."""
        if self._current_token:
            self.blacklisted_tokens.insert_one({
                "token": self._current_token,
                "createdAt": datetime.now(timezone.utc)
            })
        self._current_token = None
        self._current_user = None

    def get_current_user(self) -> Optional[Dict]:
        """Return cached user dict."""
        return self._current_user

# Global Singleton instance
auth_manager = AuthManager()

def require_role(role: str):
    """Decorator to require a specific role."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            user = auth_manager.get_current_user()
            if not user:
                raise AuthError("Not authenticated.")
            if user.get("role") != role:
                raise AuthError(f"Requires {role} role.")
            return func(*args, **kwargs)
        return wrapper
    return decorator
