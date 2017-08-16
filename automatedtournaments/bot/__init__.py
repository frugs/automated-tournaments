import aiohttp
import discord

from automatedtournaments import UserDatabase
from .tournamentbot import TournamentBot as _TournamentBot


def start_tournament_bot(bot_token: str, user_database: UserDatabase, tournament_app_base_url: str) -> None:
    discord_client = discord.Client()
    web_client = aiohttp.ClientSession()
    bot = _TournamentBot(bot_token, discord_client, web_client, user_database, tournament_app_base_url)

    bot.start()

    discord_client.close()
    web_client.close()
