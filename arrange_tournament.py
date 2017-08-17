import asyncio
import datetime
import os

import aiohttp

TOURNAMENT_BOT_BASE_URL = os.getenv("TOURNAMENTBOTBASEURL", "http://localhost:23445")
TOURNAMENT_APP_BASE_URL = os.getenv("TOURNAMENTAPPBASEURL", "http://localhost:23444")

ANNOUNCEMENT_CHANNEL_NAME = "events"


def is_success(status: int):
    return 200 <= status <= 299


def round_to_closest_hour(exact_time: datetime.datetime) -> datetime.datetime:
    current_hour = exact_time.replace(minute=0, second=0, microsecond=0)
    next_hour = (exact_time + datetime.timedelta(hours=1)).replace(minute=0, second=0, microsecond=0)

    if next_hour - exact_time < exact_time - current_hour:
        return next_hour
    else:
        return current_hour


def main() -> None:
    time_scheduled = datetime.datetime.now(datetime.timezone.utc)
    start_time = round_to_closest_hour(time_scheduled + datetime.timedelta(hours=1))

    loop = asyncio.get_event_loop()
    web_client = aiohttp.ClientSession()

    tournament_data = loop.run_until_complete(create_tournament(web_client, start_time))
    if not tournament_data:
        return

    loop.run_until_complete(announce_tournament(web_client, tournament_data))

    asyncio.ensure_future(start_tournament(web_client, tournament_data, start_time))
    asyncio.ensure_future(announce_opened_matches(web_client))
    asyncio.ensure_future(finish_tournament_once_all_matches_completed(web_client))

    loop.run_until_complete(wait_till_tournament_finished(web_client))

    loop.run_until_complete(announce_champion(web_client, tournament_data))

    web_client.close()


async def create_tournament(web_client: aiohttp.ClientSession, start_time: datetime.datetime) -> dict:
    async with web_client.post(
            TOURNAMENT_APP_BASE_URL + "/create", json={"start_time": start_time.isoformat()}) as resp:
        success = is_success(resp.status)

    if not success:
        return {}

    async with web_client.get(TOURNAMENT_APP_BASE_URL + "/") as resp:
        resp_data = await resp.json()

    if not resp_data or "tournament" not in resp_data:
        return {}

    return resp_data["tournament"]


async def announce_tournament(web_client: aiohttp.ClientSession, tournament_data: dict) -> None:
    tournament_name = tournament_data.get("name", "")
    tournament_url = tournament_data.get("full_challonge_url", "")

    message = (
        "{} will be starting in an hour! Please sign up and participate using the *;signup* command. Please "
        "visit {} to see the rules, the bracket, and the list of participants.".format(
            tournament_name, tournament_url))

    announcement_data = {
        "channel": ANNOUNCEMENT_CHANNEL_NAME,
        "message": message
    }
    async with web_client.post(TOURNAMENT_BOT_BASE_URL + "/announce", json=announcement_data) as _:
        pass


async def start_tournament(
        web_client: aiohttp.ClientSession, tournament_data: dict, start_time: datetime.datetime) -> None:
    while datetime.datetime.now(datetime.timezone.utc) < start_time:
        asyncio.sleep(30)

    tournament_name = tournament_data.get("name", "")
    tournament_url = tournament_data.get("full_challonge_url", "")

    async with web_client.post(TOURNAMENT_APP_BASE_URL + "/start") as _:
        pass

    async with web_client.get(TOURNAMENT_APP_BASE_URL + "/") as resp:
        resp_data = await resp.json()

    if resp_data.get("tournament", {}).get("started_at", None):
        message = (
            "{} is starting now! Please check {} to find out who your opponent is.".format(
                tournament_name, tournament_url))
    else:
        async with web_client.post(TOURNAMENT_APP_BASE_URL + "/destroy") as _:
            pass

        message = "{} has been cancelled due to lack of participants 🙁".format(tournament_name)

    announcement_data = {
        "channel": ANNOUNCEMENT_CHANNEL_NAME,
        "message": message
    }
    async with web_client.post(TOURNAMENT_BOT_BASE_URL + "/announce", json=announcement_data) as _:
        pass


async def announce_opened_matches(web_client: aiohttp.ClientSession) -> None:
    announced_matches = set()

    while True:
        await asyncio.sleep(15)

        async with web_client.get(TOURNAMENT_APP_BASE_URL + "/matches") as resp:
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
            async with web_client.post(TOURNAMENT_BOT_BASE_URL + "/announce", json=announcement_data) as _:
                pass


async def finish_tournament_once_all_matches_completed(web_client: aiohttp.ClientSession) -> None:
    matches_remaining = True

    while matches_remaining:
        await asyncio.sleep(15)

        async with web_client.get(TOURNAMENT_APP_BASE_URL + "/matches") as resp:
            resp_data = await resp.json()

        if "matches" in resp_data:
            matches = resp_data["matches"]

            matches_remaining = not all(match.get("match", {}).get("state", "") == "complete" for match in matches)

    async with web_client.post(TOURNAMENT_APP_BASE_URL + "/finish") as _:
        pass


async def wait_till_tournament_finished(web_client: aiohttp.ClientSession) -> None:
    while True:
        await asyncio.sleep(60)

        async with web_client.get(TOURNAMENT_APP_BASE_URL + "/") as resp:
            resp_data = await resp.json()

        if "tournament" not in resp_data:
            break

        tournament = resp_data["tournament"]
        finished = tournament.get("completed_at", None)

        if finished:
            break


async def announce_champion(web_client: aiohttp.ClientSession, tournament_data: dict) -> None:
    async with web_client.get(TOURNAMENT_APP_BASE_URL + "/participants") as resp:
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
        async with web_client.post(TOURNAMENT_BOT_BASE_URL + "/announce", json=announcement_data) as _:
            pass


if __name__ == '__main__':
    main()
