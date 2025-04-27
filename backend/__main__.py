import argparse
from backend.api import app
from backend.scrape.ratemy import run_scrape_professors, run_scrape_comments
from backend.scrape.ucore import fetch_ucore_courses, store_courses_in_db
from backend.scrape.migrate import run_sqlite_pg_migration


parser = argparse.ArgumentParser(description="Run the flask app or web scraper")

parser.add_argument(
    "--app",
    help="Run the flask app",
    action="store_true",
)

parser.add_argument(
    "--scrape-profs",
    help="Scrapes all professor ids and departments from RateMyProfessors, storing to a local sqlite3 db. Erases previous data.",
    action="store_true",
)

parser.add_argument(
    "--scrape-ucores",
    help="Scrapes all ucores (art, humanities, social science, etc.) from the WSU course catalog, storing to a local sqlite3 db",
    action="store_true",
)

parser.add_argument(
    "--scrape-comments",
    help="Scrapes all comments from RateMyProfessors, storing to a local sqlite3 db",
    action="store_true",
)

parser.add_argument(
    "--scrape",
    help="Runs all scrape jobs, clearing the database and storing the data to the postgres database",
    action="store_true",
)

parser.add_argument(
    "--migrate",
    help="Migrate data from sqlite3 to postgres",
    action="store_true",
)

args = parser.parse_args()

if args.app:
    app.run(port=5000, debug=True)

if args.migrate:
    print(
        "Running this migration will destroy all data in the postgres database. Are you sure you want to do this? (y/n)"
    )
    match input().lower():
        case "y":
            run_sqlite_pg_migration()
        case _:
            exit()

elif args.scrape_profs:
    run_scrape_professors()

elif args.scrape_ucores:
    courses = fetch_ucore_courses()
    store_courses_in_db(courses)

elif args.scrape_comments:
    run_scrape_comments()

elif args.scrape:
    print(
        "This action will clear the sqlite database. Are you sure you want to do this? (y/n)"
    )
    match input().lower():
        case "y":
            courses = fetch_ucore_courses()
            store_courses_in_db(courses)
            run_scrape_professors()
            run_scrape_comments()
        case _:
            exit()


else:
    parser.print_help()
