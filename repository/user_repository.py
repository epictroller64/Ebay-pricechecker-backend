
from typing import Optional
import uuid
from classes import InsertUser, SelectUser
from data import execute_query, select_one


class UserRepository:

    async def get_user_by_id(self, id: str) -> Optional[SelectUser]:
        result = await select_one("SELECT * FROM users WHERE id = ?", (id,), as_dict=True)
        if result:
            return SelectUser(id=result['id'], created_at=result['created_at'], email=result['email'], password=result['password'] )
        return None
    
    async def insert_user(self, user: InsertUser) -> str:
        generated_uuid = str(uuid.uuid4())
        result = await execute_query("INSERT INTO users (id, email, password, created_at) VALUES (?, ?,?,?)", (generated_uuid, user.email, user.password, user.created_at))
        if not result:
            raise Exception("No user was inserted")
        return generated_uuid

    async def get_user_by_email(self, email: str) -> Optional[SelectUser]:
        user = await select_one("SELECT * FROM users WHERE email = ?", (email, ), as_dict=True)
        if user:
            return SelectUser(id=user['id'], created_at=user['created_at'], email=user['email'], password=user['password'])