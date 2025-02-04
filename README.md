# Washington State University Course Advisor

## Running

Requirements:
- Python
- Python venv
- Node.js
- Docker
- Docker Compose

### Setup instructions
1. Clone the repository
2. `cd` into the repository
3. In the project root, `python -m venv .venv` to create a virtual environment
4. `source .venv/bin/activate` to activate the virtual environment
5. `pip install -r ./api/requirements.txt` to install the required packages for the API
6. `pip install -r ./scrape/requirements.txt` to install the required packages for the scraper
7. `cd frontend` and run `npm install` to install the required packages for the frontend

Then, you'll want to run `touch .env` in the project root and add the following environment variables:
```bash
POSTGRES_USER=admin             # Replace with your desired username
POSTGRES_PASSWORD=postgres      # Replace with your desired password
POSTGRES_DB=course-advisor-db
POSTGRES_PORT=5432
```

### Running the application
1. In the project root, `docker-compose up` to start the database
2. In another terminal, in the project root, run `python ./api/run.py` to start the API
3. In another terminal, `cd frontend` and run `npm run dev` to start the frontend

Information for running tests and the web scraper TBD