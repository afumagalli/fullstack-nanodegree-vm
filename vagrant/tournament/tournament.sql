-- Table definitions for the tournament project.
--
-- Put your SQL 'create table' statements in this file; also 'create view'
-- statements if you choose to use it.
--
-- You can write comments in this file by starting them with two dashes, like
-- these lines here.

DROP DATABASE IF EXISTS tournament;
DROP TABLE IF EXISTS matches, players;

CREATE DATABASE tournament;

\c tournament;

CREATE TABLE matches
(
matchID serial,
winner int,
loser int
);

CREATE TABLE players
(
playerID serial,
name text,
wins int,
losses int
);
