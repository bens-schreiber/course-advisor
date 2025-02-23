import argparse
from backend.api import app
from backend.api import routes


parser = argparse.ArgumentParser(
    description="Run the flask app or web scraper (with or without tests)"
)

parser.add_argument(
    "--app",
    help="Run the flask app",
    action="store_true",
)

parser.add_argument(
    "--scraper",
    help="Run the web scraper",
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

elif args.scraper:
    raise NotImplementedError("The web scraper is not implemented yet.")

else:
    parser.print_help()
