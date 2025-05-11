
import uuid
from data import execute_query, select_all_dict


class ListingRelationsRepository:
    def __init__(self) -> None:
        self.listing_relations = []

    async def get_all_listing_relations(self):
        return await select_all_dict("SELECT * FROM listing_relations")
    
    async def get_listing_relations_by_listing_id(self, listing_id: str):
        return await select_all_dict("SELECT * FROM listing_relations WHERE listing_id = ?", (listing_id, ))

    async def get_listing_relations_by_user_id(self, user_id: str):
        return await select_all_dict("SELECT * FROM listing_relations WHERE user_id = ?", (user_id, ))
    
    async def insert_listing_relation(self, user_id: str, listing_id: str):
        generated_uuid = str(uuid.uuid4())
        return await execute_query("INSERT OR IGNORE INTO listing_relations (id, user_id, listing_id) VALUES (?, ?, ?)", (generated_uuid, user_id, listing_id))
    
    async def delete_listing_relation(self, listing_id, user_id):
        return await execute_query("DELETE FROM listing_relations WHERE user_id = ? AND listing_id = ?", (user_id, listing_id))
