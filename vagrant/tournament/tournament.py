#!/usr/bin/env python
#
# tournament.py -- implementation of a Swiss-system tournament
#

import psycopg2
import bleach

# indices for players table
name = 0
wins = 1
matches = 2
bye = 3
id = 4

# indices for matches table
winner = 0
loser = 1


def connect():
    """Connect to the PostgreSQL database.  Returns a database connection."""
    return psycopg2.connect("dbname=tournament")


def deleteMatches():
    """Remove all the match records from the database."""
    conn = connect()
    c = conn.cursor()
    c.execute("DELETE FROM matches")
    conn.commit()
    conn.close()


def deletePlayers():
    """Remove all the player records from the database."""
    conn = connect()
    c = conn.cursor()
    c.execute("DELETE FROM players")
    conn.commit()
    conn.close()


def countPlayers():
    """Returns the number of players currently registered."""
    conn = connect()
    c = conn.cursor()
    c.execute("SELECT count(*) FROM players")
    count = c.fetchall()[0][0]
    conn.close()
    return count


def registerPlayer(name):
    """Adds a player to the tournament database.

    The database assigns a unique serial id number for the player.  (This
    should be handled by your SQL database schema, not in your Python code.)

    Args:
      name: the player's full name (need not be unique).
    """
    # sanitize input
    name = bleach.clean(name)
    conn = connect()
    c = conn.cursor()
    # only need name, other values set to default
    c.execute("INSERT INTO players VALUES(%s)", (name,))
    conn.commit()
    conn.close()


def playerStandings():
    """Returns a list of the players and their win records, sorted by wins.

    The first entry in the list should be the player in first place, or a
    player tied for first place if there is currently a tie.

    Returns:
      A list of tuples, each of which contains (id, name, wins, matches):
        id: the player's unique id (assigned by the database)
        name: the player's full name (as registered)
        wins: the number of matches the player has won
        matches: the number of matches the player has played
    """
    conn = connect()
    c = conn.cursor()
    c.execute("SELECT playerID, name, wins, matches FROM players_by_wins")
    players = c.fetchall()
    conn.close()
    return players


def reportMatch(winner, loser):
    """Records the outcome of a single match between two players.

    Args:
      winner:  the id number of the player who won
      loser:  the id number of the player who lost
    """
    # sanitize input
    winner = bleach.clean(winner)
    loser = bleach.clean(loser)
    conn = connect()
    c = conn.cursor()
    # add match to table
    c.execute("INSERT INTO matches VALUES (%s, %s)", (winner, loser))
    # winner gains a victory and adds to match total
    c.execute("""UPDATE players SET wins = wins + 1, matches = matches + 1
        WHERE playerID = %s""", (winner,))
    # loser only adds to match total
    c.execute("""UPDATE players SET matches = matches + 1
        WHERE playerID = %s""", (loser,))
    conn.commit()
    conn.close()


def swissPairings():
    """Returns a list of pairs of players for the next round of a match.

    Assuming that there are an even number of players registered, each player
    appears exactly once in the pairings.  Each player is paired with another
    player with an equal or nearly-equal win record, that is, a player adjacent
    to him or her in the standings.

    Returns:
      A list of tuples, each of which contains (id1, name1, id2, name2)
        id1: the first player's unique id
        name1: the first player's name
        id2: the second player's unique id
        name2: the second player's name
    """
    conn = connect()
    c = conn.cursor()
    c.execute("SELECT * FROM players_by_wins")
    players = c.fetchall()
    pairings = []
    # if odd number of players, assign a bye round
    if len(players) % 2 == 1:
        byeMatch, byePlayer = determineBye()
        pairings.append(byeMatch)
        players.remove(byePlayer)
    # iterate through rest of players
    # zip(*[iter(list)]*n) is Python idiom that iterates through
    # every n elements of a list
    for player1, player2 in zip(*[iter(players)]*2):
        match = (player1[id], player1[name], player2[id], player2[name])
        pairings.append(match)
    conn.close()
    return pairings


def determineBye():
    """Determines, at random, a player who has never had a bye round and returns
    a formatted bye match for this player.
    """
    conn = connect()
    c = conn.cursor()
    # randomly select one player who has never had a bye
    c.execute("""SELECT * FROM players WHERE bye = False
        ORDER BY RANDOM() LIMIT 1""")
    byePlayer = c.fetchall()[0]
    match = (byePlayer[id], byePlayer[name], 'bye')
    # update selected player's bye boolean
    c.execute("""UPDATE players SET bye = True
        WHERE playerID = %s""", (byePlayer[id],))
    conn.commit()
    conn.close()
    return match, byePlayer


def resetByes():
    """Testing function that resets the bye boolean to False for all players"""
    conn = connect()
    c = conn.cursor()
    c.execute("UPDATE players SET bye = False")
    conn.commit()
    conn.close()
