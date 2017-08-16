import aiohttp
import aiohttp.web

from automatedtournaments.db import UserDatabase

from .tournamentapp import TournamentApp as _TournamentApp
from .tournamentcontroller import TournamentController as _TournamentController
from .tournamentidgenerator import TournamentIdGenerator as _TournamentIdGenerator
from .challongeservice import ChallongeService as _ChallongeService


def start_tournament_app(
        port: int,
        challonge_subdomain: str,
        challonge_api_key: str,
        user_db: UserDatabase,
        default_tournament_settings: dict):
    web_client = aiohttp.ClientSession()

    app = _TournamentApp(
        _TournamentController(
            _TournamentIdGenerator(),
            _ChallongeService(web_client, challonge_subdomain, challonge_api_key),
            user_db,
            default_tournament_settings))

    aiohttp.web.run_app(app, port=port)

    web_client.close()
