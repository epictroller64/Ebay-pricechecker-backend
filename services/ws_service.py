from typing import Dict, Optional, Union
from fastapi import WebSocket
from jose import ExpiredSignatureError, JWTError, jwt
from datetime import datetime, timedelta
import os
from classes import SelectUser
from repository.user_repository import UserRepository

ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("WS_ACCESS_TOKEN_EXPIRE_MINUTES")) or 18000
SECRET_KEY = os.getenv("WS_SECRET_KEY")
ALGORITHM = "HS256"


if not SECRET_KEY:
    raise Exception("no ws secret key supplied")

class WSService:
    def __init__(self) -> None:
        self.user_repository = UserRepository()
        self.users: Dict[str, tuple[SelectUser, WebSocket]] = {}

    def add_websocket(self, websocket: WebSocket):
        self.websocket = websocket

    async def send_message(self, user_id: str, message_obj):
        target_user = self.users.get(user_id)
        if target_user:
            user, websocket = target_user
            await websocket.send_json(message_obj)
    
    def get_online_users(self):
        return [x[0] for x in self.users.items()]

    async def broadcast_message(self, message_obj):
        for k, v in self.users.items():
            user, ws = v
            await ws.send_json(message_obj)
    

    async def connect(self, token: str, websocket: WebSocket):
        validated_user = await self.validate_user(token)
        if validated_user.get("success"):
            user: SelectUser = validated_user['body']['user']
            session_token = self.generate_session_token(user.email, user.id)
            self.users[user.id] = (user, websocket)
            print("Websocket connected with ", user.email)
            return {"success": "OK", "body": session_token}
        return {"error": "User not authenticated"}
    
    async def disconnect(self, token: str):
        validated_user = await self.validate_user(token)
        if validated_user.get('success'):
            del self.users.validated_user['body']['user'].id


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

    
    def generate_session_token(self, email: str, user_id: str):
        to_encode = {"email": email, "id": user_id}.copy()
        expire = datetime.now() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt

ws_service = WSService()