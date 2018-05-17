import np as np
from espncricinfo.match import Match
import random
import urllib.request
import re
import numpy as np
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
import matplotlib.pyplot as pyplot

# Define game formats/countries
NationNumsAll = {'england': 1,
                 'australia': 2,
                 'south africa': 3,
                 'west indies': 4,
                 'new zealand': 5,
                 'india': 6,
                 'pakistan': 7,
                 'sri lanka': 8,
                 'zimbabwe': 9,
                 'bermuda': 12,
                 'netherlands': 15,
                 'canada': 17,
                 'hong kong': 19,
                 'papua new guinea': 20,
                 'bangladesh': 25,
                 'kenya': 26,
                 'united arab emirates': 27,
                 'ireland': 29,
                 'afghanistan': 40}

PlayerNameAll = {}
BatsmanText = np.empty(0)

# Select a format & team
while True:
    try:
        PlayerTeamName = input('Enter a test playing nation: ').lower()
        PlayerTeamID = NationNumsAll[PlayerTeamName]
        break
    except (NameError, KeyError):
        print("Team not found! ", end="", flush=True)

# Parse and extract list of all players for nation
PlayerListURL = f"http://www.espncricinfo.com/england/content/player/caps.json?country={PlayerTeamID!s};class=1"
PlayerListJSON = urllib.request.urlopen(PlayerListURL).read()
PlayerListSoup = BeautifulSoup(PlayerListJSON, "lxml")
PlayerListSoupLi = PlayerListSoup.find_all("li", {"class": "ciPlayername"})

for PConstructor in PlayerListSoupLi:
    PConstructString = str(PConstructor)
    PConstructURL = (PConstructor.find('a', href=True)['href'])
    PConstructNamePos = PConstructString.find("middle;") + 9

    PConstructName = PConstructString[PConstructNamePos:len(PConstructString) - 9]
    PConstructID = int(re.findall("\\d+", PConstructURL)[0])
    PlayerNameAll.update({PConstructName: PConstructID})

# Pick player
print(f"Found {len(PlayerNameAll)!s} players for {PlayerTeamName.title()!s}")
while True:
    PlayerName = input(f"Enter a name (e.g. {random.choice(list(PlayerNameAll.keys()))}) or type 'list' \n")

    if PlayerName.lower() == 'list':
        print(PlayerNameAll.keys())
    else:
        try:
            PlayerNum = PlayerNameAll[PlayerName]
            break
        except KeyError:
            print("Player not found! ", end="", flush=True)
            continue

# Determine if player is batsman/allrounder/bowler (for appropriate calculations)
BatBowlAllrounder = 3

# Get all matches player has played in
AllMatchURL = (f'http://stats.espncricinfo.com/ci/engine/player/{PlayerNum!s}'
               '.json?class=1;template=results;type=allround;view=match')
AllMatchJSON = urllib.request.urlopen(AllMatchURL).read()
AllMatchSoup = BeautifulSoup(AllMatchJSON, "lxml")  # Make sure to retry!
AllMatchTable = AllMatchSoup.findAll("table", {"class": "engineTable"})[3]
AllMatchDate = np.array([MatchDate.text for MatchDate in AllMatchSoup.findAll("b")[3:-6]])
AllMatchOpp = np.array([MatchOpp.text for MatchOpp in AllMatchSoup.findAll("a", {"class": "data-link"})[::2]])
AllMatchID = re.findall('\\d+', str(AllMatchTable.findAll("td", {"style": "white-space: nowrap;"})))[::2]

# For each game played in
print(f"Found {(len(AllMatchID))!s} matches for {PlayerName}. Analysing...")
BatsmanTimesNotOut = 0
BatsmanRuns = 0
BatsmanInnings = 0
PrintLoop = 0

for MatchID in AllMatchID:

    # Open match URL
    MatchURL = f"http://www.espncricinfo.com/ci/engine/match/{MatchID!s}.html"  # Make sure to retry!
    MatchJSON = urllib.request.urlopen(MatchURL).read()
    MatchSoup = BeautifulSoup(MatchJSON, "lxml")

    # Get bowling table (this is how the internet is meant to be programmed)
    # Figure out who won batted first to determine if looping 0+2 or 1+3
    ScorecardBowlingJSON = pd.read_html(MatchURL)
    BattedFirst = MatchSoup.find("h2").text.split()[0]
    if BattedFirst in PlayerTeamName.title():
        ScorecardOppBowlingAll = np.vstack(
            np.array([ScorecardBowlingRaw.values for ScorecardBowlingRaw in ScorecardBowlingJSON[::2]]))
        ScorecardTeamBowlingAll = np.vstack(
            np.array([ScorecardBowlingRaw.values for ScorecardBowlingRaw in ScorecardBowlingJSON[1::2]]))
        ScorecardOppExtrasRaw = np.vstack(
            np.array([OppExtrasRaw.text for OppExtrasRaw in MatchSoup.findAll("div", {"class": "wrap extras"})[::2]]))
    else:
        ScorecardOppBowlingAll = np.vstack(
            np.array([ScorecardBowlingRaw.values for ScorecardBowlingRaw in ScorecardBowlingJSON[1::2]]))
        ScorecardTeamBowlingAll = np.vstack(
            np.array([ScorecardBowlingRaw.values for ScorecardBowlingRaw in ScorecardBowlingJSON[::2]]))
        ScorecardOppExtrasRaw = np.vstack(
            np.array([OppExtrasRaw.text for OppExtrasRaw in MatchSoup.findAll("div", {"class": "wrap extras"})[1::2]]))

    # Get batting table (this is how the internet is NOT meant to be programmed...)
    AllBatsmanRawText = MatchSoup.findAll("div", {"class": "cell runs"})
    AllBatsmanRawNames = MatchSoup.findAll("div", {"class": "cell batsmen"})
    AllBatsmanRawCommentary = MatchSoup.findAll("div", {"class": "cell commentary"})

    BatsmanText = np.array([BatsmanRawText.text for BatsmanRawText in AllBatsmanRawText]).reshape((-1, 6))
    BatsmanNames = np.vstack(np.array([BatsmanRawNames.text for BatsmanRawNames in AllBatsmanRawNames]))
    BatsmanCommentary = np.vstack(
        np.array([BatsmanRawCommentary.text for BatsmanRawCommentary in AllBatsmanRawCommentary]))
    ScorecardBattingAll = np.concatenate((BatsmanNames, BatsmanText, BatsmanCommentary), 1)

    # Get statistics for batting
    if BatBowlAllrounder == 1 | 3:
        # Get player batting cards (need to search incase player is captain/keeper)
        ScorecardBatting = ScorecardBattingAll[
            np.where((np.chararray.find(ScorecardBattingAll[:, 0].astype(str), PlayerName) + 1) == 1)]

        # Get number of innings played
        BatsmanInnings += np.size(ScorecardBatting, 0)

        # Get number of runs made by batsman
        BatsmanRuns += np.sum(list(map(int, ScorecardBatting[:, 1])))

        # Get number of times not out
        BatsmanTimesNotOut += list(ScorecardBatting[:, 7]).count('not out')

        # Get average of bowlers
        BatsmanOvers = ScorecardOppBowlingAll[:, 2]
        BatsmanRunsConc = ScorecardOppBowlingAll[:, 4]
        BatsmanExtras = np.array(
            re.findall('\d+', str(re.findall('Extras\d+', str(ScorecardOppExtrasRaw))))).astype(int)
        BatsmanWickets = ScorecardOppBowlingAll[:, 5]
        

    # Get statistics for bowling
    # if BatBowlAllrounder == 2 | 3:
    #     ScorecardBowling = ScorecardBowlingAll[
    #         np.where((np.chararray.find(ScorecardBowlingAll[:, 0].astype(str), PlayerName) + 1) == 1)]

    print(f"    Completed {AllMatchDate[PrintLoop]} vs {AllMatchOpp[PrintLoop]}")
    PrintLoop += 1
