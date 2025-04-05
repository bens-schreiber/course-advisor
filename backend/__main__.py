import argparse
from backend.api import app
from backend.api import routes
from backend.scrape import run_scrape_pids, run_scrape_all


parser = argparse.ArgumentParser(
    description="Run the flask app or web scraper (with or without tests)"
)

parser.add_argument(
    "--app",
    help="Run the flask app",
    action="store_true",
)

parser.add_argument(
    "--scrape_pids",
    help="Scrapes all new professor ids from RateMyProfessors, storing to a local sqlite3 db",
    action="store_true",
)

parser.add_argument(
    "--scrape_all",
    help="Scrapes all comments from the stored professor ids, storing all professors, departments, comments, ratings, etc to the postgres db",
    action="store_true",
)

parser.add_argument(
    "--test",
    help="Run the tests",
    action="store_true",
)

args = parser.parse_args()

if args.app:
    if args.test:
        raise NotImplementedError("Tests for the flask app are not implemented yet.")
    app.run(port=5000, debug=True)

elif args.scrape_pids:
    run_scrape_pids()

elif args.scrape_all:
    run_scrape_all()

else:
    parser.print_help()
