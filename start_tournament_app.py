import os
import pickle

from automatedtournaments import start_tournament_app, UserDatabase

PORT = int(os.environ.get("PORT", "23444"))
CHALLONGE_SUBDOMAIN = os.environ.get("CHALLONGESUBDOMAIN", "")
CHALLONGE_API_KEY = os.environ.get("CHALLONGEAPIKEY", "")


def main():
    with open("firebase.cfg", 'rb') as db_config_file:
        db_config = pickle.load(db_config_file)

    with open("challonge.cfg", 'rb') as challonge_config_file:
        default_tournament_settings = pickle.load(challonge_config_file)

    user_database = UserDatabase(db_config)
    start_tournament_app(PORT, CHALLONGE_SUBDOMAIN, CHALLONGE_API_KEY, user_database, default_tournament_settings)


if __name__ == "__main__":
    main()