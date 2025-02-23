-- NOTE: This data does not accurately reflect the courses or departments at WSU.


insert into courses (id, name, credits, level) 
values
    (1, 'CPTS 121', 4, 100),
    (2, 'BIO 100', 4, 100),
    (3, 'HIST 101', 3, 100),
    (4, 'MATH 453', 2, 400)
on conflict do nothing;

insert into departments (id, name)
values
    (1, 'Computer Science'),
    (2, 'Biology'),
    (3, 'History'),
    (4, 'Mathematics')
on conflict do nothing;

insert into ucores (id, name)
values
    (1, 'Critical and Creative Thinking'),
    (2, 'Quantitative Reasoning'),
    (3, 'Scientific Literacy'),
    (4, 'Information Literacy'),
    (5, 'Communication'),
    (6, 'Diversity'),
    (7, 'Depth, Breadth, and Integration of Learning')
on conflict do nothing;

insert into course_departments (course_id, department_id)
values
    (1, 1), -- CPTS 121, Computer Science
    (2, 2), -- BIO 100, Biology
    (3, 3), -- HIST 101, History
    (4, 4)  -- MATH 453, Mathematics
on conflict do nothing;

insert into course_ucores (course_id, ucore_id)
values
    (1, 2), -- CPTS 121, Quantitative Reasoning
    (2, 3), -- BIO 100, Scientific Literacy
    (3, 1), -- HIST 101, Critical and Creative Thinking
    (4, 2)  -- MATH 453, Quantitative Reasoning
on conflict do nothing;


----------- LLM PROMPT STARTS HERE ---------
--
--
-- Create 6 distinct professor for each course.
-- Then, you will fill the `ratings` table with ratings for each professor. Each professor should have [0,5] ratings, such professor 1 falls into the first category, professor 2 falls into the second category, and so on:
--  1. A high quality professor (rmp_quality is relatively high, rmp_difficulty is relatively low, rmp_take_again is relatively high, rmp_rating_count is relatively high)
--  2. A high quality difficult professor (rmp_quality is relatively high, rmp_difficulty is relatively high, rmp_take_again is relatively high, rmp_rating_count is relatively high)
--  3. A low quality professor (rmp_quality is relatively low, rmp_difficulty is relatively high, rmp_take_again is relatively low, rmp_rating_count is relatively low)
--  4. A low quality easy professor (rmp_quality is relatively low, rmp_difficulty is relatively low, rmp_take_again is relatively low, rmp_rating_count is relatively low)
--  5. A professor with no ratings (rmp_rating_count is 0)
--  6. An average professor (rmp_quality is average, rmp_difficulty is average, rmp_take_again is average, rmp_rating_count is average)
--
-- Then, fill the `professor_course_ratings` table. This table should contain the calculated rating R(P, A) for each professor P with course A.
-- Finally, fill the `professor_cumulative_ratings` table. This table should contain the calculated rating R(P) for each professor P.
-- (definitions for R(P, A) and R(P) are in the README.md)
--
--
----------- LLM PROMPT ENDS HERE -----------

----------- LLM GENERATED DATA STARTS HERE -----------
-- Insert professors for each course
INSERT INTO professors (id, department_id, name)
VALUES
    -- CPTS 121 Professors
    (1, 1, 'Dr. Alice Johnson'),
    (2, 1, 'Dr. Bob Smith'),
    (3, 1, 'Dr. Carol White'),
    (4, 1, 'Dr. David Brown'),
    (5, 1, 'Dr. Eve Davis'),
    (6, 1, 'Dr. Frank Wilson'),

    -- BIO 100 Professors
    (7, 2, 'Dr. Grace Lee'),
    (8, 2, 'Dr. Henry Green'),
    (9, 2, 'Dr. Irene Black'),
    (10, 2, 'Dr. Jack Harris'),
    (11, 2, 'Dr. Karen Clark'),
    (12, 2, 'Dr. Leo Lewis'),

    -- HIST 101 Professors
    (13, 3, 'Dr. Mia Hall'),
    (14, 3, 'Dr. Noah Young'),
    (15, 3, 'Dr. Olivia King'),
    (16, 3, 'Dr. Paul Wright'),
    (17, 3, 'Dr. Quinn Scott'),
    (18, 3, 'Dr. Rachel Adams'),

    -- MATH 453 Professors
    (19, 4, 'Dr. Samuel Hill'),
    (20, 4, 'Dr. Taylor Baker'),
    (21, 4, 'Dr. Uma Carter'),
    (22, 4, 'Dr. Victor Evans'),
    (23, 4, 'Dr. Wendy Perez'),
    (24, 4, 'Dr. Xavier Reed')
ON CONFLICT DO NOTHING;

-- Insert ratings for each professor
INSERT INTO ratings (professor_id, course_id, rmp_quality, rmp_difficulty, rmp_comment)
VALUES
    -- CPTS 121 Professors
    -- High quality professor
    (1, 1, 4.8, 2.5, 'Excellent teacher, very clear and helpful.'),
    -- High quality difficult professor
    (2, 1, 4.7, 4.0, 'Challenging but rewarding course.'),
    -- Low quality professor
    (3, 1, 2.5, 4.5, 'Hard to follow lectures.'),
    -- Low quality easy professor
    (4, 1, 2.8, 2.0, 'Easy but not very informative.'),
    -- Professor with no ratings
    (5, 1, 0.0, 0.0, NULL),
    -- Extra professor
    (6, 1, 3.5, 3.0, 'Average experience.'),

    -- BIO 100 Professors
    -- High quality professor
    (7, 2, 4.9, 2.0, 'Great explanations and engaging lectures.'),
    -- High quality difficult professor
    (8, 2, 4.6, 4.2, 'Tough but fair.'),
    -- Low quality professor
    (9, 2, 2.4, 4.3, 'Not very organized.'),
    -- Low quality easy professor
    (10, 2, 2.7, 2.1, 'Easy but not very useful.'),
    -- Professor with no ratings
    (11, 2, 0.0, 0.0, NULL),
    -- Extra professor
    (12, 2, 3.8, 3.2, 'Good overall.'),

    -- HIST 101 Professors
    -- High quality professor
    (13, 3, 4.7, 2.3, 'Very knowledgeable and engaging.'),
    -- High quality difficult professor
    (14, 3, 4.5, 4.1, 'Challenging but interesting.'),
    -- Low quality professor
    (15, 3, 2.6, 4.4, 'Hard to understand.'),
    -- Low quality easy professor
    (16, 3, 2.9, 2.2, 'Easy but not very informative.'),
    -- Professor with no ratings
    (17, 3, 0.0, 0.0, NULL),
    -- Extra professor
    (18, 3, 3.6, 3.1, 'Decent course.'),

    -- MATH 453 Professors
    -- High quality professor
    (19, 4, 4.8, 2.4, 'Clear and concise lectures.'),
    -- High quality difficult professor
    (20, 4, 4.6, 4.3, 'Difficult but very rewarding.'),
    -- Low quality professor
    (21, 4, 2.5, 4.5, 'Hard to follow.'),
    -- Low quality easy professor
    (22, 4, 2.8, 2.1, 'Easy but not very useful.'),
    -- Professor with no ratings
    (23, 4, 0.0, 0.0, NULL),
    -- Extra professor
    (24, 4, 3.7, 3.0, 'Average experience.')
ON CONFLICT DO NOTHING;

-- Insert professor course ratings
INSERT INTO professor_course_ratings (professor_id, course_id, rating)
SELECT
    r.professor_id,
    r.course_id,
    (SUM(r.rmp_quality * 0.5 + (5 - r.rmp_difficulty) * 0.3) / COUNT(r.id)) + 5 * 0.2 AS rating
FROM
    ratings r
GROUP BY
    r.professor_id, r.course_id
ON CONFLICT DO NOTHING;

-- Insert professor cumulative ratings
INSERT INTO professor_cumulative_ratings (professor_id, rating)
SELECT
    pcr.professor_id,
    AVG(pcr.rating) AS rating
FROM
    professor_course_ratings pcr
GROUP BY
    pcr.professor_id
ON CONFLICT DO NOTHING;
----------- LLM GENERATED DATA ENDS HERE -----------