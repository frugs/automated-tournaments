import os

import pickle

import automatedtournaments

BOT_TOKEN = os.getenv("BOTTOKEN", "")
TOURNAMENT_APP_BASE_URL = os.getenv("TOURNAMENTAPPBASEURL", "http://localhost:23444")


def main():
    with open("firebase.cfg", 'rb') as db_config_file:
        db_config = pickle.load(db_config_file)

    user_database = automatedtournaments.UserDatabase(db_config)
    automatedtournaments.start_tournament_bot(BOT_TOKEN, user_database, TOURNAMENT_APP_BASE_URL)


if __name__ == "__main__":
    main()