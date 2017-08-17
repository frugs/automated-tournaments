import asyncio
import discord
import aiohttp
import aiohttp.web

from discord import ChannelType
from automatedtournaments import UserDatabase

ERROR_REASONS = {
    "UNREGISTERED_USER": "Please use the *;register* command to register your challonge username first.",
    "TOURNAMENT_NOT_CREATED": "There are no open tournaments.",
    "TOURNAMENT_STARTED": "The tournament has already started, and sign-ups have closed.",
    "TOURNAMENT_FINISHED": "There are no open tournaments.",
    "USER_SIGNED_UP": "You're already signed up 🙃",
    "NO_OPEN_MATCHES_FOR_PLAYER": "You don't have any open matches."
}


class TournamentBot:

    def __init__(
            self,
            bot_token: str,
            discord_client: discord.Client,
            web_client: aiohttp.ClientSession,
            user_database: UserDatabase,
            tournament_app_base_url: str,
            web_app_port: int):
        self._bot_token = bot_token
        self._discord_client = discord_client
        self._web_client = web_client
        self._user_database = user_database
        self._tournament_app_base_url = tournament_app_base_url
        self._web_app = aiohttp.web.Application()
        self._web_app_port = web_app_port

        self._web_app.router.add_post("/announce", self.make_announcement)

        _command_lookup = [
            (func.replace("handle_", ""), getattr(self, func))
            for func
            in dir(self)
            if callable(getattr(self, func)) and func.startswith("handle_")]

        @discord_client.event
        async def on_ready() -> None:
            print('Discord client connected.')

        @discord_client.event
        async def on_message(message: discord.Message) -> None:
            if message.author == self._discord_client.user:
                return

            for command, func in _command_lookup:
                if message.content.startswith(";" + command):
                    await func(message)
                    break
            else:
                if self._discord_client.user.mention in message.content:
                    await self.handle_help(message)

    async def handle_help(self, message: discord.Message) -> None:
        await self._discord_client.send_message(
            message.channel,
            "Hi there, I'm {}! I'm here to manage automated tournaments for you.  I'll post a message to let you know "
            "when a tournament is open for you to sign up to. Here are a list of the commands I can accept:\n\n"
            "*;help* - Show this help message.\n\n"
            "*;register [challonge_username]* - Register your Challonge username with me. This is case sensitive, so "
            "make sure you have your casing correct!\n\n"
            "*;signup* - Sign up to the currently open tournament. Please ensure you have registered your challonge "
            "username with me using the *:register* command before attempting to sign up.\n\n"
            "*;forfeit* - Forfeit all your remaining matches in the currently open tournament.\n\n"
            "*;victory* - Record a victory for your current game in the current tournament.\n\n"
            "*;loss* - Record a loss for your current game in the current tournament.\n\n"
            "*;tournament* - Shows a link to the challonge page of the currently open tournament if there is one, or "
            "the last completed one otherwise.".format(self._discord_client.user.mention))

    async def handle_register(self, message: discord.Message) -> None:
        split_message = message.content.split(" ")
        if len(split_message) < 2:
            return

        challonge_id = split_message[1]

        await self._user_database.set_challonge_id(message.author.id, challonge_id)

        await self._discord_client.send_message(
            message.channel,
            "Registered challonge username **{}** for {}".format(challonge_id, message.author.mention))

    async def handle_signup(self, message: discord.Message) -> None:
        async with self._web_client.post(self._tournament_app_base_url + "/signup/" + message.author.id) as resp:
            resp_data = await resp.json()

        if resp_data and "error" in resp_data:
            reply = "Sorry, I couldn't sign you up!\n"
            reply += ERROR_REASONS.get(resp_data["error"], "")
        else:
            reply = "{} I've successfully signed you up to the tournament! Good luck 🙂".format(message.author.mention)

        await self._discord_client.send_message(message.channel, reply)

    async def handle_victory(self, message: discord.Message) -> None:
        async with self._web_client.post(self._tournament_app_base_url + "/victory/" + message.author.id) as resp:
            resp_data = await resp.json()

        if resp_data and "error" in resp_data:
            reply = "{} Sorry, I couldn't record your victory.\n".format(message.author.mention)
            reply += ERROR_REASONS.get(resp_data["error"], "")
        else:
            reply = "{} Thank you for reporting the result, and congratulations on your victory!".format(
                message.author.mention)

        await self._discord_client.send_message(message.channel, reply)

    async def handle_loss(self, message: discord.Message) -> None:
        async with self._web_client.post(self._tournament_app_base_url + "/loss/" + message.author.id) as resp:
            resp_data = await resp.json()

        if resp_data and "error" in resp_data:
            reply = "{} Sorry, I couldn't record your loss.\n".format(message.author.mention)
            reply += ERROR_REASONS.get(resp_data["error"], "")
        else:
            reply = "{} Hard luck; I hope you fare better next time. Thank you for reporting your loss.".format(
                message.author.mention)

        await self._discord_client.send_message(message.channel, reply)

    async def make_announcement(self, request: aiohttp.web.Request) -> aiohttp.web.Response:
        request_data = await request.json()

        if not request_data:
            return

        channel_name = request_data.get("channel", "")

        if not channel_name:
            return

        message = request_data.get("message", "")

        if not message:
            return

        matching_channels = [
            channel
            for channel
            in self._discord_client.get_all_channels()
            if channel.name == channel_name and not channel.is_private and channel.type == ChannelType.text]

        for channel in matching_channels:
            await self._discord_client.send_message(channel, message)

        return aiohttp.web.HTTPNoContent()

    def start(self):
        asyncio.ensure_future(self._discord_client.start(self._bot_token))

        aiohttp.web.run_app(self._web_app, port=self._web_app_port)

