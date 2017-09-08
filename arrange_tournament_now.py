import datetime
import os
import automatedtournaments.arranger

TOURNAMENT_APP_BASE_URL = os.getenv("TOURNAMENTAPPBASEURL", "http://localhost:23444")
TOURNAMENT_BOT_BASE_URL = os.getenv("TOURNAMENTBOTBASEURL", "http://localhost:23445")


def main():
    automatedtournaments.arranger.TournamentArranger(
        TOURNAMENT_APP_BASE_URL,
        TOURNAMENT_BOT_BASE_URL,
        datetime.timedelta(hours=1),
        True).arrange_tournament()


if __name__ == "__main__":
    main()