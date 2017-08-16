from aiohttp.web import Application, Response, Request, json_response, json_response

from .tournamentcontroller import TournamentController


class TournamentApp(Application):

    def __init__(self, tournament_controller: TournamentController):
        super().__init__()

        self.controller = tournament_controller

        self.router.add_post("/create", self.create)
        self.router.add_post("/start", self.start)
        self.router.add_post("/finish", self.finish)

        self.router.add_post("/signup/{discord_id}", self.sign_up)
        self.router.add_post("/forfeit/{discord_id}", self.forfeit)
        self.router.add_post("/checkin/{discord_id}", self.check_in)

        self.router.add_post("/victory/{discord_id}", self.record_victory)
        self.router.add_post("/loss/{discord_id}", self.record_loss)

    async def create(self, _: Request) -> Response:
        status, error = await self.controller.create_tournament()

        if status:
            return json_response()

        return json_response(data={"error": error}, status=409)

    async def start(self, _: Request) -> Response:
        status, error = await self.controller.start_tournament()

        if status:
            return json_response()

        return json_response(data={"error": error}, status=409)

    async def finish(self, _: Request) -> Response:
        status, error = await self.controller.finish_tournament()

        if status:
            return json_response()

        return json_response(data={"error": error}, status=409)

    async def sign_up(self, request: Request) -> Response:
        status, error = await self.controller.sign_up_player(request.match_info.get("discord_id", ""))

        if status:
            return json_response()

        return json_response(data={"error": error}, status=409)

    async def check_in(self, request: Request) -> Response:
        status, error = await self.controller.check_in_player(request.match_info.get("discord_id", ""))

        if status:
            return json_response()

        return json_response(data={"error": error}, status=409)

    async def forfeit(self, request: Request) -> Response:
        status, error = await self.controller.forfeit_player(request.match_info.get("discord_id", ""))

        if status:
            return json_response()

        return json_response(data={"error": error}, status=409)

    async def record_victory(self, request: Request) -> Response:
        status, error = await self.controller.record_victory(request.match_info.get("discord_id", ""))

        if status:
            return json_response()

        return json_response(data={"error": error}, status=409)

    async def record_loss(self, request: Request) -> Response:
        status, error = await self.controller.record_loss(request.match_info.get("discord_id", ""))

        if status:
            return json_response()

        return json_response(data={"error": error}, status=409)

