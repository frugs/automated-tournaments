import os

import automatedtournaments

TOURNAMENT_APP_BASE_URL = os.getenv("TOURNAMENTAPPBASEURL", "http://localhost:23444")
TOURNAMENT_BOT_BASE_URL = os.getenv("TOURNAMENTBOTBASEURL", "http://localhost:23445")
PORT = os.getenv("PORT", "23446")


def main():
    automatedtournaments.start_arranger_app(int(PORT), TOURNAMENT_APP_BASE_URL, TOURNAMENT_BOT_BASE_URL)


if __name__ == "__main__":
    main()