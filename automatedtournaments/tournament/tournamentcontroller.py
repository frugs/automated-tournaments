from typing import Tuple

from .tournamentidgenerator import TournamentIdGenerator
from .challongeservice import ChallongeService
from automatedtournaments.db import UserDatabase


class TournamentController:

    def __init__(
            self,
            tournament_id_generator: TournamentIdGenerator,
            challonge_service: ChallongeService,
            user_database: UserDatabase,
            default_tournament_settings: dict):
        self._challonge_service = challonge_service
        self._tournament_id_generator = tournament_id_generator
        self._user_database = user_database
        self._default_tournament_settings = default_tournament_settings

        self._tournament_id = None

    async def create_tournament(self) -> Tuple[bool, str]:
        if self._tournament_id and not await self._challonge_service.has_tournament_finished(self._tournament_id):
            return False, "TOURNAMENT_ONGOING"

        for i in range(10):
            self._tournament_id = self._tournament_id_generator.next_id()

            if not await self._challonge_service.does_tournament_exist(self._tournament_id):
                break
        else:
            return False, "TOURNAMENT_IDS_EXHAUSTED"

        tournament_name = self._tournament_id_generator.next_name()

        await self._challonge_service.create_tournament(
            self._tournament_id, tournament_name, self._default_tournament_settings)

        return True, ""

    async def start_tournament(self) -> Tuple[bool, str]:
        if not self._tournament_id or not await self._challonge_service.does_tournament_exist(self._tournament_id):
            return False, "TOURNAMENT_NOT_CREATED"

        if await self._challonge_service.has_tournament_started(self._tournament_id):
            return False, "TOURNAMENT_STARTED"

        await self._challonge_service.start_tournament(self._tournament_id)

        return True, ""

    async def finish_tournament(self) -> Tuple[bool, str]:
        if not self._tournament_id or not await self._challonge_service.does_tournament_exist(self._tournament_id):
            return False, "TOURNAMENT_NOT_CREATED"

        if not await self._challonge_service.has_tournament_started(self._tournament_id):
            return False, "TOURNAMENT_NOT_STARTED"

        if await self._challonge_service.has_tournament_finished(self._tournament_id):
            return False, "TOURNAMENT_FINISHED"

        await self._challonge_service.finish_tournament(self._tournament_id)

        return True, ""

    async def sign_up_player(self, discord_id: str) -> Tuple[bool, str]:
        challonge_id = await self._user_database.get_challonge_id(discord_id)
        
        if not challonge_id:
            return False, "UNREGISTERED_USER"

        name = await self._user_database.get_nickname(discord_id)

        if not name:
            name = challonge_id

        if not self._tournament_id or not await self._challonge_service.does_tournament_exist(self._tournament_id):
            return False, "TOURNAMENT_NOT_CREATED"

        if await self._challonge_service.has_tournament_started(self._tournament_id):
            return False, "TOURNAMENT_STARTED"

        if await self._challonge_service.has_tournament_finished(self._tournament_id):
            return False, "TOURNAMENT_FINISHED"

        if await self._challonge_service.is_user_signed_up(self._tournament_id, discord_id):
            return False, "USER_SIGNED_UP"
        
        await self._challonge_service.sign_up_player(self._tournament_id, discord_id, challonge_id, name)

        return True, ""

    async def forfeit_player(self, discord_id: str) -> Tuple[bool, str]:

        if not self._tournament_id or not await self._challonge_service.does_tournament_exist(self._tournament_id):
            return False, "TOURNAMENT_NOT_CREATED"

        if await self._challonge_service.has_tournament_finished(self._tournament_id):
            return False, "TOURNAMENT_FINISHED"

        if not await self._challonge_service.is_user_signed_up(self._tournament_id, discord_id):
            return False, "USER_NOT_SIGNED_UP"

        await self._challonge_service.forfeit_player(self._tournament_id, discord_id)

        return True, ""

    async def check_in_player(self, discord_id: str) -> Tuple[bool, str]:

        if not self._tournament_id or not await self._challonge_service.does_tournament_exist(self._tournament_id):
            return False, "TOURNAMENT_NOT_CREATED"

        if await self._challonge_service.has_tournament_finished(self._tournament_id):
            return False, "TOURNAMENT_FINISHED"

        if not await self._challonge_service.is_user_signed_up(self._tournament_id, discord_id):
            return False, "USER_NOT_SIGNED_UP"

        if await self._challonge_service.is_user_checked_in(self._tournament_id, discord_id):
            return False, "USER_CHECKED_IN"

        await self._challonge_service.check_in_player(self._tournament_id, discord_id)

        return True, ""

    async def record_victory(self, discord_id: str) -> Tuple[bool, str]:

        if not self._tournament_id or not await self._challonge_service.does_tournament_exist(self._tournament_id):
            return False, "TOURNAMENT_NOT_CREATED"

        if await self._challonge_service.has_tournament_finished(self._tournament_id):
            return False, "TOURNAMENT_FINISHED"

        if not await self._challonge_service.is_user_signed_up(self._tournament_id, discord_id):
            return False, "USER_NOT_SIGNED_UP"

        open_matches = await self._challonge_service.open_matches_for_player(self._tournament_id, discord_id)

        if not open_matches:
            return False, "NO_OPEN_MATCHES_FOR_PLAYER"

        match = open_matches[0]["match"]

        if match.get("player1_discord_id", "") == discord_id:
            score = "1-0"
            winner_id = str(match["player1_id"])
        else:
            score = "0-1"
            winner_id = str(match["player2_id"])

        await self._challonge_service.submit_match_result(
            self._tournament_id,
            str(match["id"]),
            winner_id,
            score)

        return True, ""

    async def record_loss(self, discord_id: str) -> Tuple[bool, str]:

        if not self._tournament_id or not await self._challonge_service.does_tournament_exist(self._tournament_id):
            return False, "TOURNAMENT_NOT_CREATED"

        if await self._challonge_service.has_tournament_finished(self._tournament_id):
            return False, "TOURNAMENT_FINISHED"

        if not await self._challonge_service.is_user_signed_up(self._tournament_id, discord_id):
            return False, "USER_NOT_SIGNED_UP"

        open_matches = await self._challonge_service.open_matches_for_player(self._tournament_id, discord_id)

        if not open_matches:
            return False, "NO_OPEN_MATCHES_FOR_PLAYER"

        match = open_matches[0]["match"]

        if match.get("player1_discord_id", "") == discord_id:
            score = "0-1"
            winner_id = str(match["player2_id"])
        else:
            score = "1-0"
            winner_id = str(match["player1_id"])

        await self._challonge_service.submit_match_result(
            self._tournament_id,
            str(match["id"]),
            winner_id,
            score)

        return True, ""
