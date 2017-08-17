from typing import List

import aiohttp

BASE_URL = "https://api.challonge.com/v1"


class ChallongeService:

    def __init__(
            self,
            client_session: aiohttp.ClientSession,
            challonge_subdomain: str,
            challonge_api_key: str):

        self._web_client = client_session
        self._challonge_subdomain = challonge_subdomain
        self._challonge_api_key = challonge_api_key

    async def get_tournament_data(self, tournament_id: str):
        url = BASE_URL + "/tournaments/" + self._challonge_subdomain + "-" + tournament_id + ".json"
        query_params = {"api_key": self._challonge_api_key}
        async with self._web_client.get(url, params=query_params) as resp:
            return await resp.json()

    async def does_tournament_exist(self, tournament_id: str) -> bool:
        tournament_data = await self.get_tournament_data(tournament_id)

        return "tournament" in tournament_data

    async def has_tournament_started(self, tournament_id: str) -> bool:
        tournament_data = await self.get_tournament_data(tournament_id)

        if "tournament" not in tournament_data:
            return False

        return bool(tournament_data["tournament"].get("started_at", None))

    async def has_tournament_finished(self, tournament_id: str) -> bool:
        tournament_data = await self.get_tournament_data(tournament_id)

        if "tournament" not in tournament_data:
            return False

        return bool(tournament_data["tournament"].get("completed_at", None))

    async def create_tournament(self, tournament_id: str, tournament_name: str, tournament_settings: dict) -> None:
        url = BASE_URL + "/tournaments.json"
        query_params = {
            "api_key": self._challonge_api_key,
            "tournament[name]": tournament_name,
            "tournament[url]": tournament_id,
            "tournament[subdomain]": self._challonge_subdomain
        }

        query_params.update(tournament_settings)

        async with self._web_client.post(url, params=query_params) as _:
            pass

    async def destroy_tournament(self, tournament_id: str) -> None:
        url = BASE_URL + "/tournaments/" + self._challonge_subdomain + "-" + tournament_id + ".json"
        query_params = {
            "api_key": self._challonge_api_key,
        }

        async with self._web_client.delete(url, params=query_params) as _:
            pass

    async def start_tournament(self, tournament_id: str) -> None:
        url = BASE_URL + "/tournaments/" + self._challonge_subdomain + "-" + tournament_id + "/start.json"
        query_params = {"api_key": self._challonge_api_key}

        async with self._web_client.post(url, params=query_params) as _:
            pass

    async def finish_tournament(self, tournament_id: str) -> None:
        url = BASE_URL + "/tournaments/" + self._challonge_subdomain + "-" + tournament_id + "/finalize.json"
        query_params = {"api_key": self._challonge_api_key}

        async with self._web_client.post(url, params=query_params) as _:
            pass

    async def is_user_signed_up(self, tournament_id: str, discord_id: str) -> bool:
        return bool(await self._get_participant_id(tournament_id, discord_id))

    async def is_user_checked_in(self, tournament_id: str, discord_id: str) -> bool:
        participant_id = await self._get_participant_id(tournament_id, discord_id)

        if not participant_id:
            return False

        url = (
            BASE_URL +
            "/tournaments/" +
            self._challonge_subdomain +
            "-" +
            tournament_id +
            "/participants/" +
            participant_id +
            ".json")
        query_params = {"api_key": self._challonge_api_key}

        async with self._web_client.get(url, params=query_params) as resp:
            resp_data = await resp.json()

        if "participant" not in resp_data:
            return False

        return resp_data["participant"].get("checked_in", False)

    async def sign_up_player(self, tournament_id: str, discord_id: str, challonge_id: str, name: str) -> None:
        url = BASE_URL + "/tournaments/" + self._challonge_subdomain + "-" + tournament_id + "/participants.json"
        query_params = {
            "api_key": self._challonge_api_key,
            "participant[challonge_username]": challonge_id,
            "participant[name]": name,
            "participant[misc]": discord_id
        }

        async with self._web_client.post(url, params=query_params) as _:
            pass

    async def check_in_player(self, tournament_id: str, discord_id: str) -> None:
        participant_id = await self._get_participant_id(tournament_id, discord_id)

        if not participant_id:
            return

        url = (
            BASE_URL +
            "/tournaments/" +
            self._challonge_subdomain +
            "-" +
            tournament_id +
            "/participants/" +
            participant_id +
            "/check_in.json")
        query_params = {"api_key": self._challonge_api_key}

        async with self._web_client.post(url, params=query_params) as _:
            pass

    async def forfeit_player(self, tournament_id: str, discord_id: str) -> None:
        participant_id = await self._get_participant_id(tournament_id, discord_id)

        if not participant_id:
            return

        url = (
            BASE_URL +
            "/tournaments/" +
            self._challonge_subdomain +
            "-" +
            tournament_id +
            "/participants/" +
            participant_id +
            ".json")
        query_params = {"api_key": self._challonge_api_key}

        async with self._web_client.delete(url, params=query_params) as _:
            pass

    async def open_matches_for_player(self, tournament_id: str, discord_id: str) -> List[dict]:
        participant_id = await self._get_participant_id(tournament_id, discord_id)

        if not participant_id:
            return []

        url = BASE_URL + "/tournaments/" + self._challonge_subdomain + "-" + tournament_id + "/matches.json"
        query_params = {
            "api_key": self._challonge_api_key,
            "state": "open",
            "participant_id": participant_id
        }

        async with self._web_client.get(url, params=query_params) as resp:
            result = await resp.json()

        for match in result:
            if str(match["match"]["player1_id"]) == participant_id:
                match["match"]["player1_discord_id"] = discord_id
            else:
                match["match"]["player2_discord_id"] = discord_id

        return result

    async def submit_match_result(
            self,
            tournament_id: str,
            match_id: str,
            winner_participant_id: str,
            score_csv: str) -> None:

        url = (
            BASE_URL +
            "/tournaments/" +
            self._challonge_subdomain +
            "-" +
            tournament_id +
            "/matches/" +
            match_id +
            ".json")
        query_params = {
            "api_key": self._challonge_api_key,
            "match[scores_csv]": score_csv,
            "match[winner_id]": winner_participant_id
        }

        async with self._web_client.put(url, params=query_params) as _:
            pass

    async def _get_participant_id(self, tournament_id: str, discord_id: str) -> str:
        participants = await self.get_participants_in_tournament(tournament_id)

        participant_id = ""
        for participant in participants:
            if participant["participant"].get("misc", "") == discord_id:
                participant_id = str(participant["participant"]["id"])
                break

        return participant_id

    async def get_participants_in_tournament(self, tournament_id) -> List[dict]:
        url = BASE_URL + "/tournaments/" + self._challonge_subdomain + "-" + tournament_id + "/participants.json"
        query_params = {"api_key": self._challonge_api_key}
        async with self._web_client.get(url, params=query_params) as resp:
            participants = await resp.json()

        for participant in participants:
            participant_inner = participant["participant"]
            participant_inner["discord_id"] = participant_inner.get("misc", "")

        return participants

    async def get_matches_in_tournament(self, tournament_id: str) -> List:
        url = BASE_URL + "/tournaments/" + self._challonge_subdomain + "-" + tournament_id + "/matches.json"
        query_params = {"api_key": self._challonge_api_key}
        async with self._web_client.get(url, params=query_params) as resp:
            matches = await resp.json()

        participants = await self.get_participants_in_tournament(tournament_id)
        discord_id_lookup = dict(
            (participant["participant"]["id"], participant["participant"]["misc"])
            for participant
            in participants)

        for match in matches:
            match_inner = match["match"]
            match_inner["player1_discord_id"] = discord_id_lookup.get(match_inner["player1_id"], None)
            match_inner["player2_discord_id"] = discord_id_lookup.get(match_inner["player2_id"], None)

        return matches
