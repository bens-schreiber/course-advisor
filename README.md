# Washington State University Course Advisor

WSU Course Advisor is a search application with two specific queries for students:
1. What are the top professors for my course
2. What are the top classes (and subsequent top professor) to take for my class requirements (department, credit, university core credit)

The aim is this search engine will aid students in booking their next semesters courses.

In order to rank professors, we need a lot of data, being professors, classes, departments, and of course ratings for each class a professor teaches. RateMyProfessor provides this information, but only in a manner of `Professer -> Class`, which is unable to suit our needs as we want an inverse relation of `Class -> Professor` and `Requirements -> Class, Professor`. We employ web scraping to grab all of the data from RateMyProfessor, and then create this inverse lookup.

<img width="1440" alt="Screenshot 2025-04-27 at 5 19 12 PM" src="https://github.com/user-attachments/assets/e9788fb5-7118-477b-a1f5-9078c4b32536" />



This project was created as a semester project for CPTS 451. There are several TODOs we did not get to implement due to time constraints:
- [ ] Create an automated update for the web scraper. We currently only have a way to seed data (scrape all of RMP, make a database from it), but would like to have a scheduled job to fetch new results and insert them into the database.
- [ ] Associate courses with UCores. We currently scrape ucores, but the process of fuzzy searching a RMP course title (which are very different from one another, for example `CPTS 121` could be: `CPT 121` `121` `CPT` `CS 121` etc...) is complex and went out of scope for this project.
- [ ] Use an AI model to give a professor overview, course overview. We store all comments in our database, so an AI summary wouldn't be a stretch
- [ ] Implement a more sophisticated ranking algorithm. Our algorithm currently has constant weights employed, and doesn't fully consider many edge cases in rating (if a professor has 1 rating, that shouldn't necessarily be better than one with hundreds)


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
POSTGRES_USER=admin
POSTGRES_PASSWORD=postgres
POSTGRES_DB=course-advisor-db
POSTGRES_PORT=5432
RMP_PROFESSOR_DEPARTMENT_URL = "https://www.ratemyprofessors.com/search/professors/1143?q=*&did={did}"
RMP_PROFESSOR_URL = "https://www.ratemyprofessors.com/professor/{id}"
RMP_DEPARTMENTS=100
```

### Running the application
1. In the project root, `docker-compose up` to start the database
2. In another terminal, in the project root, run `python -m backend --app` to start the API
3. In another terminal, `cd frontend` and run `npm run dev` to start the frontend

### Running the scraper

The scraper is compromised of several different parts, all of them storing their progress in a local sqlite database.

Scrape data is stored in `scrape.db`, a local SQLite3 database. This is included in our git repository, and is pre-filled with all of the data. To migrate this data into the postgres db, without running the entire scraper again (which takes a long time), you can run the following command:


```bash
python -m backend --migrate
```

Or, to run the scraper again and source new data, run the following commands in this sequence:

1. `python -m backend --scrape-ucore`
2. `python -m backend --scrape-profs`
3. `python -m backend --scrape-comments`
4. `python -m backend --migrate`


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

$$ 
R(P,A) = \frac{\sum_{(q,d) \in A} (q \cdot w_q + (5-d) \cdot w_d) + 5 \cdot P.wta \cdot w_{wta}}{w_q + w_d + w_{wta}} 
$$

It would follow that


$$
R(P) = \frac{\sum_{A \in P.C} R(P, A)}{|P.C|}
$$

where (at this time)
- $w_q = 0.5$
- $w_d = 0.3$
- $w_{wta} = 0.2$


