from aiohttp.web import Application, Response, Request, json_response, json_response

from .tournamentcontroller import TournamentController


class TournamentApp(Application):

    def __init__(self, tournament_controller: TournamentController):
        super().__init__()

        self._controller = tournament_controller

        self.router.add_get("/", self.index)
        self.router.add_get("/matches", self.matches)
        self.router.add_get("/participants", self.participants)

        self.router.add_post("/create", self.create)
        self.router.add_post("/destroy", self.destroy)
        self.router.add_post("/start", self.start)
        self.router.add_post("/finish", self.finish)

        self.router.add_post("/signup/{discord_id}", self.sign_up)
        self.router.add_post("/forfeit/{discord_id}", self.forfeit)
        self.router.add_post("/checkin/{discord_id}", self.check_in)

        self.router.add_post("/victory/{discord_id}", self.record_victory)
        self.router.add_post("/loss/{discord_id}", self.record_loss)

    async def index(self, _: Request) -> Response:
        result, error = await self._controller.get_active_tournament()

        if result:
            return json_response(result)

        return json_response(data={"error": error})

    async def create(self, _: Request) -> Response:
        status, error = await self._controller.create_tournament()

        if status:
            return json_response()

        return json_response(data={"error": error}, status=409)

    async def destroy(self, _: Request) -> Response:
        status, error = await self._controller.destroy_tournament()

        if status:
            return json_response()

        return json_response(data={"error": error}, status=409)

    async def start(self, _: Request) -> Response:
        status, error = await self._controller.start_tournament()

        if status:
            return json_response()

        return json_response(data={"error": error}, status=409)

    async def finish(self, _: Request) -> Response:
        status, error = await self._controller.finish_tournament()

        if status:
            return json_response()

        return json_response(data={"error": error}, status=409)

    async def sign_up(self, request: Request) -> Response:
        status, error = await self._controller.sign_up_player(request.match_info.get("discord_id", ""))

        if status:
            return json_response()

        return json_response(data={"error": error}, status=409)

    async def check_in(self, request: Request) -> Response:
        status, error = await self._controller.check_in_player(request.match_info.get("discord_id", ""))

        if status:
            return json_response()

        return json_response(data={"error": error}, status=409)

    async def forfeit(self, request: Request) -> Response:
        status, error = await self._controller.forfeit_player(request.match_info.get("discord_id", ""))

        if status:
            return json_response()

        return json_response(data={"error": error}, status=409)

    async def record_victory(self, request: Request) -> Response:
        status, error = await self._controller.record_victory(request.match_info.get("discord_id", ""))

        if status:
            return json_response()

        return json_response(data={"error": error}, status=409)

    async def record_loss(self, request: Request) -> Response:
        status, error = await self._controller.record_loss(request.match_info.get("discord_id", ""))

        if status:
            return json_response()

        return json_response(data={"error": error}, status=409)

    async def matches(self, _: Request) -> Response:
        result, error = await self._controller.get_matches_in_tournament()

        if result:
            return json_response(data=result)

        return json_response(data={"error": error}, status=409)

    async def participants(self, _: Request) -> Response:
        result, error = await self._controller.get_participants_in_tournament()

        if result:
            return json_response(data=result)

        return json_response(data={"error": error}, status=409)
