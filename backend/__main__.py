import argparse
from backend.api import app
from backend.api import routes
from backend.scrape import run_scrape_pids, run_scrape_db_seed


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
    "--scrape_ucores",
    help="Scrapes all ucores (art, humanities, social science, etc.) from the WSU course catalog, storing to a local sqlite3 db",
    action="store_true",
)

parser.add_argument(
    "--scrape_db_seed",
    help="Using the `scrape_pids` generated database, scrapes all professors, departments, courses, and comments from RateMyProfessor, clearing the database and storing the data to the postgres database",
    action="store_true",
)

parser.add_argument(
    "--init_db",
    help="Runs all scrape jobs, clearing the database and storing the data to the postgres database",
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

elif args.scrape_db_seed:
    run_scrape_db_seed()

elif args.scrape_ucores:
    raise NotImplementedError("Scraping ucores is not implemented yet.")

elif args.init_db:
    print(
        "This action will clear the database. Are you sure you want to do this? (y/n)"
    )
    match input().lower():
        case "y":
            print("Initializing the database...")
            # TODO: run_scrape_ucores()
            run_scrape_pids()
            run_scrape_db_seed()
        case "n":
            print("Exiting...")
            exit()
        case _:
            print("Invalid input. Exiting...")
            exit()


else:
    parser.print_help()
