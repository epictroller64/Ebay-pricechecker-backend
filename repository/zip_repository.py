import uuid
from data import execute_query, select_one


class ZipRepository:
    def __init__(self) -> None:
        pass

    async def insert_zip(self, filename: str):
        generated_uuid = str(uuid.uuid4())
        await execute_query("INSERT INTO zip_files (id, filename) VALUES (?, ?)", (generated_uuid, filename))
        return generated_uuid

    async def get_zip(self, id: str):
        return await select_one("SELECT * FROM zip_files WHERE id= ?", (id, ), as_dict=True)
    