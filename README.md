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
5. `pip install -r ./backend/requirements.txt` to install the required python packages
6. `cd frontend` and run `npm install` to install the required packages for the frontend

Then, you'll want to run `touch .env` in the project root and add the following environment variables:
```bash
POSTGRES_USER=admin             # Replace with your desired username
POSTGRES_PASSWORD=postgres      # Replace with your desired password
POSTGRES_DB=course-advisor-db
POSTGRES_PORT=5432
```

### Running the application
1. In the project root, `docker-compose up` to start the database
2. In another terminal, in the project root, run `python -m backend --app` to start the API
3. In another terminal, `cd frontend` and run `npm run dev` to start the frontend

### Running the scraper
TODO: Link to Google Drive / One Drive for a postgres db dump 

To scrape all professor ids:
```bash
python -m backend --scrape_pids
```

To scrape all ucores:
```bash
python -m backend --scrape_ucores
```

To scrape all professors, courses, comments, departments and assign ucores (previous scrape jobs must be completed):
```bash
python -m backend --scrape_db_seed
```

To run all of these jobs in one command, populating the initial database:
```bash
python -m backend --init_db
```

### Postgres
View postgres manually in the terminal:
```bash
docker exec -it course-advisor-postgres psql -U ${POSTGRES_USER} -d ${POSTGRES_DB}
```

## Professor Ratings
A professor is ranked on a $[0, 5.0]$ scale for a paticular course. The formula for a profesors rating in a paticular course is as follows:

A rating on RateMyProfessor gives two values on the same $[0, 5.0]$ scale:
- `quality` 
- `difficulty`

As well as the value
- `would take again` (percentage of students who would take the professor again)

Given these ratings, we want to calculate
1. The overall rating of the professor in a particular course $R(P, A)$
2. The overall rating of the professor $R(P)$

This will be done using our own formula.

Given 
- $A = \{  (q, d) \}$ a set of ratings (quality, difficulty)
- $C = \{ A \}$ a set of ratings for a course
- $P = (wta, C)$ = a professor with a $wta$ and set of courses $C$
 - $w_q + w_d + w_{wta} = 1 $

$$ R(P,A) = \frac{\sum_{(q,d) \in A} (q \cdot w_q + (5-d) \cdot w_d) + 5 \cdot P.wta \cdot w_{wta}}{w_q + w_d + w_{wta}} 
$$

It would follow that
$$
R(P) = \frac{\sum_{A \in P.C} R(P, A)}{|P.C|}
$$

where (at this time)
- $w_q = 0.5$
- $w_d = 0.3$
- $w_{wta} = 0.2$


