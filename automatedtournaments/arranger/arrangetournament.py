import asyncio
import datetime

import aiohttp

from .util import is_success, round_to_closest_hour

ANNOUNCEMENT_CHANNEL_NAME = "events"
SECONDARY_ANNOUNCEMENT_CHANNEL_NAME = "general"


class TournamentArranger:
    
    def __init__(
            self,
            tournament_app_base_url: str,
            tournament_bot_base_url: str,
            start_in: datetime.timedelta,
            round_to_nearest_hour: bool):

        self.tournament_app_base_url = tournament_app_base_url
        self.tournament_bot_base_url = tournament_bot_base_url
        self.start_in = start_in
        self.round_to_nearest_hour = round_to_nearest_hour

    def arrange_tournament(self) -> None:
        time_scheduled = datetime.datetime.now(datetime.timezone.utc)
        start_time = time_scheduled + self.start_in

        if self.round_to_nearest_hour:
            start_time = round_to_closest_hour(start_time)

        loop = asyncio.new_event_loop()
        web_client = aiohttp.ClientSession(loop=loop)

        tournament_data = loop.run_until_complete(self.create_tournament(web_client, start_time))
        if not tournament_data:
            return

        loop.run_until_complete(self.announce_tournament(web_client, tournament_data))

        asyncio.ensure_future(
            self.announce_pre_start_tournament(web_client, tournament_data, start_time, loop=loop), loop=loop)
        asyncio.ensure_future(self.start_tournament(web_client, tournament_data, start_time, loop=loop), loop=loop)
        asyncio.ensure_future(self.announce_opened_matches(web_client, loop=loop), loop=loop)
        asyncio.ensure_future(self.finish_tournament_once_all_matches_completed(web_client, loop=loop), loop=loop)

        loop.run_until_complete(self.wait_till_tournament_finished(web_client, loop=loop))

        loop.run_until_complete(self.announce_champion(web_client, tournament_data))

        web_client.close()

    async def create_tournament(self, web_client: aiohttp.ClientSession, start_time: datetime.datetime) -> dict:
        async with web_client.post(
                self.tournament_app_base_url + "/create", json={"start_time": start_time.isoformat()}) as resp:
            success = is_success(resp.status)
    
        if not success:
            return {}
    
        async with web_client.get(self.tournament_app_base_url + "/") as resp:
            resp_data = await resp.json()
    
        if not resp_data or "tournament" not in resp_data:
            return {}
    
        return resp_data["tournament"]

    async def announce_tournament(self, web_client: aiohttp.ClientSession, tournament_data: dict) -> None:
        tournament_name = tournament_data.get("name", "The tournament")
        tournament_url = tournament_data.get("full_challonge_url", "the Challonge page")

        start_in_hours, remainder = divmod(self.start_in.seconds, 3600)
        start_in_minutes = remainder // 60

        if start_in_hours:
            start_in_str = "in {} hours".format(start_in_hours)

            if start_in_minutes:
                start_in_str += "and {} minutes".format(start_in_minutes)
        elif start_in_minutes:
            start_in_str = "in {} minutes".format(start_in_minutes)
        else:
            start_in_str = "now"
    
        message = (
            "@here {} will be starting {}! Please sign up and participate using the *;signup* command. Please "
            "visit {} to see the rules, the bracket, and the list of participants.".format(
                tournament_name, start_in_str, tournament_url))
    
        announcement_data = {
            "channel": ANNOUNCEMENT_CHANNEL_NAME,
            "message": message
        }
        async with web_client.post(self.tournament_bot_base_url + "/announce", json=announcement_data) as _:
            pass

    async def announce_pre_start_tournament(self, web_client, tournament_data, start_time, loop=None) -> None:
        announcement_time = start_time - datetime.timedelta(minutes=15)
    
        while datetime.datetime.now(datetime.timezone.utc) < announcement_time:
            await asyncio.sleep(30, loop=loop)
    
        tournament_name = tournament_data.get("name", "The tournament")
        tournament_url = tournament_data.get("full_challonge_url", "the Challonge page")
    
        message = (
            "{} will be starting in fifteen minutes! Please sign up and participate using the *;signup* command. "
            "Please visit {} to see the rules, the bracket, and the list of participants.".format(
                tournament_name, tournament_url))
    
        async with web_client.post(self.tournament_bot_base_url + "/announce", json={
            "channel": ANNOUNCEMENT_CHANNEL_NAME,
            "message": "@here " + message
        }) as _:
            pass
    
        async with web_client.post(self.tournament_bot_base_url + "/announce", json={
            "channel": SECONDARY_ANNOUNCEMENT_CHANNEL_NAME,
            "message": message
        }) as _:
            pass
    
    async def start_tournament(
            self,
            web_client: aiohttp.ClientSession,
            tournament_data: dict,
            start_time: datetime.datetime,
            loop: asyncio.BaseEventLoop=None) -> None:
    
        while datetime.datetime.now(datetime.timezone.utc) < start_time:
            await asyncio.sleep(30, loop=loop)
    
        tournament_name = tournament_data.get("name", "The tournament")
        tournament_url = tournament_data.get("full_challonge_url", "the Challonge page")
    
        async with web_client.post(self.tournament_app_base_url + "/start") as _:
            pass
    
        async with web_client.get(self.tournament_app_base_url + "/") as resp:
            resp_data = await resp.json()
    
        if resp_data.get("tournament", {}).get("started_at", None):
            message = (
                "@here {} is starting now! Please check {} to find out who your opponent is.".format(
                    tournament_name, tournament_url))
        else:
            async with web_client.post(self.tournament_app_base_url + "/destroy") as _:
                pass
    
            message = "{} has been cancelled due to lack of participants 🙁".format(tournament_name)
    
        announcement_data = {
            "channel": ANNOUNCEMENT_CHANNEL_NAME,
            "message": message
        }
        async with web_client.post(self.tournament_bot_base_url + "/announce", json=announcement_data) as _:
            pass

    async def announce_opened_matches(
            self, web_client: aiohttp.ClientSession, loop: asyncio.BaseEventLoop=None) -> None:
        announced_matches = set()
    
        while True:
            await asyncio.sleep(15, loop=loop)
    
            async with web_client.get(self.tournament_app_base_url + "/matches") as resp:
                resp_data = await resp.json()
    
            message = ""
    
            if "matches" in resp_data:
                matches = resp_data["matches"]
    
                for match in matches:
                    match_inner = match.get("match", {})
    
                    if "id" not in match_inner or match_inner["id"] in announced_matches:
                        continue
    
                    if (match_inner.get("state", "") == "open" and
                            "player1_discord_id" in match_inner and
                            "player2_discord_id" in match_inner):
    
                        player1_mention = "<@{}>".format(match_inner["player1_discord_id"])
                        player2_mention = "<@{}>".format(match_inner["player2_discord_id"])
    
                        message += "{}, your next opponent is {}!\n".format(player1_mention, player2_mention)
    
                        announced_matches.add(match_inner["id"])
    
            if message:
                announcement_data = {
                    "channel": ANNOUNCEMENT_CHANNEL_NAME,
                    "message": message
                }
                async with web_client.post(self.tournament_bot_base_url + "/announce", json=announcement_data) as _:
                    pass

    async def finish_tournament_once_all_matches_completed(
            self, web_client: aiohttp.ClientSession, loop: asyncio.BaseEventLoop=None) -> None:
        matches_remaining = True
    
        while matches_remaining:
            await asyncio.sleep(15, loop=loop)
    
            async with web_client.get(self.tournament_app_base_url + "/matches") as resp:
                resp_data = await resp.json()
    
            if "matches" in resp_data:
                matches = resp_data["matches"]
    
                matches_remaining = not all(match.get("match", {}).get("state", "") == "complete" for match in matches)
    
        success = False
    
        while not success:
            async with web_client.post(self.tournament_app_base_url + "/finish") as resp:
                success = is_success(resp.status)
    
            await asyncio.sleep(5, loop=loop)

    async def wait_till_tournament_finished(
            self,
            web_client: aiohttp.ClientSession,
            loop: asyncio.BaseEventLoop=None) -> None:
        while True:
            await asyncio.sleep(60, loop=loop)
    
            async with web_client.get(self.tournament_app_base_url + "/") as resp:
                resp_data = await resp.json()
    
            if "tournament" not in resp_data:
                break
    
            tournament = resp_data["tournament"]
            finished = tournament.get("completed_at", None)
    
            if finished:
                break
    
    async def announce_champion(self, web_client: aiohttp.ClientSession, tournament_data: dict) -> None:
        async with web_client.get(self.tournament_app_base_url + "/participants") as resp:
            resp_data = await resp.json()
    
        winner_discord_id = ""
    
        if "participants" in resp_data:
            for participant in resp_data["participants"]:
                participant_inner = participant.get("participant", {})
    
                if participant_inner.get("final_rank", None) == 1:
                    winner_discord_id = participant_inner.get("discord_id", "")
                    break
    
        if winner_discord_id:
            message = "@here Please congratulate <@{}>, the champion of {}!".format(
                winner_discord_id, tournament_data.get("name", "the tournament"))
    
            announcement_data = {
                "channel": ANNOUNCEMENT_CHANNEL_NAME,
                "message": message
            }
            async with web_client.post(self.tournament_bot_base_url + "/announce", json=announcement_data) as _:
                pass

