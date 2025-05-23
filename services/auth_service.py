from datetime import datetime, timedelta
from jose import ExpiredSignatureError, JWTError, jwt
import os
from typing import Dict, Optional, Union
import bcrypt
from classes import InsertUser, LoginUser, RegisterUser, SelectUser, Settings
from repository.settings_repository import SettingsRepository
from repository.user_repository import UserRepository

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv('ACCESS_TOKEN_EXPIRE_MINUTES')) or 18000

if not SECRET_KEY:
    raise Exception("no secret key supplied")

class AuthService:
    def __init__(self) -> None:
        self.user_repository = UserRepository()

    async def validate_user(self, token: str) -> Dict[str, Union[bool, Optional[str], Optional[SelectUser]]]:
        try:
            decoded_jwt = jwt.decode(token, SECRET_KEY, ALGORITHM)
            user_id = decoded_jwt['id']
            if user_id:
                user = await self.user_repository.get_user_by_id(decoded_jwt['id'])
                if user:
                    user.password = ''
                    return {"success": "OK", "body": {"user": user}}
            return {"error": "No user found"}
        except ExpiredSignatureError:
            return {"error": "Token expired invalid"}
        except JWTError:
            return {"error": "Token signature invalid"}
        except Exception as e:
            print(str(e))
            return {"error": "Token failed to be validated"}
        
    async def register(self, user: RegisterUser):
        existing_user = await self.user_repository.get_user_by_email(user.email)
        if existing_user:
            return {"error": "User already exists"}
        hashed_password = self.hash_password(user.password)
        result = await self.user_repository.insert_user(InsertUser(created_at=datetime.now(), email=user.email, password=hashed_password))
        session_token = self.generate_session_token(user.email, result)
        ### Create default settings insert
        await SettingsRepository().insert_settings(Settings(user_id=result, phone_number="", telegram_userid="", email=user.email, interval=60))
        return {"success": "OK", "body": {"token": session_token, "user_id": result}}
    
    async def login(self, user: LoginUser):
        existing_user = await self.user_repository.get_user_by_email(user.email)
        if not existing_user:
            return {"error": "User does not exist"}
        psswd_compare = self.verify_password(user.password, existing_user.password)
        if psswd_compare:
            session_token = self.generate_session_token(existing_user.email, existing_user.id)
            return {"success": "OK", "body": { "token": session_token, "user_id": existing_user.id} }
        return {"error": "Invalid password"}

    def hash_password(self, plainpassword: str):
        encoded = plainpassword.encode('utf-8')
        salt = bcrypt.gensalt()
        hashed_password = bcrypt.hashpw(encoded, salt)
        decoded_hashed = hashed_password.decode('utf-8')
        return decoded_hashed

    def verify_password(self, plaintext_pw: str, hashed_pw: str):
        plaintext_pw_bytes = plaintext_pw.encode('utf-8')
        hashed_pw_bytes = hashed_pw.encode('utf-8')
        return bcrypt.checkpw(plaintext_pw_bytes, hashed_pw_bytes)
    
    def generate_session_token(self, email: str, user_id: str):
        to_encode = {"email": email, "id": user_id}.copy()
        expire = datetime.now() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt
