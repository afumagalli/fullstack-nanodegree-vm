-- Table definitions for the tournament project.
--
-- Put your SQL 'create table' statements in this file; also 'create view'
-- statements if you choose to use it.
--
-- You can write comments in this file by starting them with two dashes, like
-- these lines here.

DROP DATABASE IF EXISTS tournament;

CREATE DATABASE tournament;

\c tournament;

DROP TABLE IF EXISTS matches, players;

CREATE TABLE matches
(
winner int,
loser int
);

CREATE TABLE players
(
name text,
wins int DEFAULT 0,
matches int DEFAULT 0,
playerID serial
);
