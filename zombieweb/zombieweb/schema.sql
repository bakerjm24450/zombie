DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS bodyparts;
DROP TABLE IF EXISTS lockstatus;

CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL
);

CREATE TABLE bodyparts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    status INTEGER
);

CREATE TABLE lockstatus (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    status INTEGER
);
