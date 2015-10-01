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

-- table of all registered players
CREATE TABLE players
(
name text,
wins int DEFAULT 0,
matches int DEFAULT 0,
bye boolean DEFAULT false,
-- bye is true iff the player has had a bye round before
playerID serial primary key
);

-- table of all matches in tournament
CREATE TABLE matches
(
winner int references players(playerID),
loser int references players(playerID)
);

-- view used to make selecting players by wins concise
CREATE VIEW players_by_wins AS
	SELECT * FROM players ORDER BY wins DESC;
