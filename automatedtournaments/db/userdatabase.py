import asyncio

from pyrebase import pyrebase


class UserDatabase:

    def __init__(self, db_config: dict):
        self._db_config = db_config

    async def get_challonge_id(self, discord_id: str) -> str:
        return await asyncio.get_event_loop().run_in_executor(None, self._get_challonge_id_inner, discord_id)

    async def set_challonge_id(self, discord_id: str, challonge_id: str) -> None:
        await asyncio.get_event_loop().run_in_executor(
            None, self._set_challonge_id_inner, discord_id, challonge_id)

    async def get_nickname(self, discord_id: str) -> str:
        return await asyncio.get_event_loop().run_in_executor(None, self._get_nickname_inner, discord_id)

    def _get_challonge_id_inner(self, discord_id: str):
        db = pyrebase.initialize_app(self._db_config).database()
        query_result = db.child("members").child(discord_id).get()

        if not query_result.pyres:
            return ""

        return query_result.val().get("challonge_username", "")

    def _set_challonge_id_inner(self, discord_id: str, challonge_id: str) -> None:
        db = pyrebase.initialize_app(self._db_config).database()
        db.child("members").child(discord_id).update({"challonge_username": challonge_id})

    def _get_nickname_inner(self, discord_id: str) -> str:
        db = pyrebase.initialize_app(self._db_config).database()
        query_result = db.child("members").child(discord_id).get()

        if not query_result.pyres:
            return ""

        result_data = query_result.val()
        return result_data.get("discord_server_nick", result_data.get("discord_display_name", ""))