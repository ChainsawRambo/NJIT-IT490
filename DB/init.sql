CREATE DATABASE bartender;
\c bartender
CREATE TABLE usersinfo
(
    username varchar(50),
    firstname varchar(50),
    lastname varchar(50) not null,
    email varchar(255) not null unique,
    hash VARCHAR(255) NOT NULL
);
