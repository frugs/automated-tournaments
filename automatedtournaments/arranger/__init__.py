import aiohttp.web

from .arrangetournament import TournamentArranger
from .arrangerapp import ArrangerApp as _ArrangerApp


def start_arranger_app(port: int, tournament_app_base_url: str, tournament_bot_base_url: str):

    web_client = aiohttp.ClientSession()
    app = _ArrangerApp(tournament_app_base_url, tournament_bot_base_url)

    aiohttp.web.run_app(app, port=port)

    web_client.close()