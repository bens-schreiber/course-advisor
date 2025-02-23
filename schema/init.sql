-- Initial PostgreSQL schema for the database
create table courses (
    id serial primary key,
    name text not null,
    credits int not null,
    level int not null,
    created_at timestamp not null default now(),
    updated_at timestamp not null default now()
);

create table departments (
    id serial primary key,
    name text not null,
    created_at timestamp not null default now(),
    updated_at timestamp not null default now()
);

create table ucores (
    id serial primary key,
    name text not null,
    created_at timestamp not null default now(),
    updated_at timestamp not null default now()
);

create table course_departments (
    id serial primary key,
    course_id int not null references courses(id),
    department_id int not null references departments(id),
    created_at timestamp not null default now(),
    updated_at timestamp not null default now(),

    unique (course_id, department_id)
);

create table course_ucores (
    id serial primary key,
    course_id int not null references courses(id),
    ucore_id int not null references ucores(id),
    created_at timestamp not null default now(),
    updated_at timestamp not null default now(),

    unique (course_id, ucore_id)
);

create table professors (
    id serial primary key,
    department_id int not null references departments(id),
    name text not null,
    created_at timestamp not null default now(),
    updated_at timestamp not null default now()
);

create table ratings (
    id serial primary key,
    professor_id int not null references professors(id),
    course_id int not null references courses(id),
    rmp_quality numeric(3,2) check (rmp_quality between 0 and 5) not null,
    rmp_difficulty numeric(3, 2) check (rmp_difficulty between 0 and 5) not null,
    rmp_comment text,
    created_at timestamp not null default now(),
    updated_at timestamp not null default now()
);

create index idx_professor_course on ratings (professor_id, course_id);

create table professor_cumulative_ratings (
    id serial primary key,
    professor_id int not null references professors(id),
    rating numeric(3,2) check (rating between 0 and 5) not null,
    created_at timestamp not null default now(),
    updated_at timestamp not null default now(),

    unique (professor_id)
);

create table professor_course_ratings (
    id serial primary key,
    professor_id int not null references professors(id),
    course_id int not null references courses(id),
    rating numeric(3,2) check (rating between 0 and 5) not null,
    created_at timestamp not null default now(),
    updated_at timestamp not null default now(),

    unique (professor_id, course_id)
);