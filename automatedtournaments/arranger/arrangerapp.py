import datetime

import asyncio
from aiohttp.web import Application, Request, Response

from . import TournamentArranger


class ArrangerApp(Application):

    def __init__(self, tournament_app_base_url: str, tournament_bot_base_url: str):
        super().__init__()

        self.tournament_app_base_url = tournament_app_base_url
        self.tournament_bot_base_url = tournament_bot_base_url
        self.router.add_post("/arrange", self.arrange)

    async def arrange(self, _: Request) -> Response:
        asyncio.get_event_loop().run_in_executor(
            None,
            TournamentArranger(
                self.tournament_app_base_url,
                self.tournament_bot_base_url,
                datetime.timedelta(minutes=20),
                False).arrange_tournament)
        return Response()
