import asyncio

import aiohttp

from automatedtournaments.tournament.challongeservice import ChallongeService


async def test():
    async with aiohttp.ClientSession() as client:
        service = ChallongeService(client, "automatedtournaments", "API_KEY")

        tournament_id = "testtournament4"

        await service.create_tournament(tournament_id, tournament_id, {})
        await service.sign_up_player(tournament_id, "frugs", "frugs", "frugs")
        await service.sign_up_player(tournament_id, "test_participant", "test_participant", "test_participant")

        await service.check_in_player(tournament_id, "frugs")
        await service.check_in_player(tournament_id, "test_participant")

        await service.start_tournament(tournament_id)

        matches = await service.open_matches_for_player(tournament_id, "frugs")
        match = matches[0]["match"]
        await service.submit_match_result(tournament_id, str(match["id"]), match["player2_id"], "0-1")
        await service.finish_tournament(tournament_id)


asyncio.get_event_loop().run_until_complete(test())