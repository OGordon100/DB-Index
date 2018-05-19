import random
import urllib.request
import pandas as pd
from bs4 import BeautifulSoup
import re
import numpy as np
from datetime import datetime
import matplotlib.pyplot as pyplot
import time

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
BatsmanTimesNotOut = np.zeros(len(AllMatchID))
BatsmanRuns = np.zeros(len(AllMatchID))
BatsmanInnings = np.zeros(len(AllMatchID))
BatsmanNetBowling = np.zeros(len(AllMatchID))
BatsmanNet = np.zeros(len(AllMatchID))
PrintLoop = 0

for MatchID in AllMatchID:

    # Open match URL
    t = time.time()
    print(time.time() - t)
    MatchURL = f"http://www.espncricinfo.com/ci/engine/match/{MatchID!s}.html"  # Make sure to retry!
    MatchJSON = urllib.request.urlopen(MatchURL).read()
    MatchSoup = BeautifulSoup(MatchJSON, "lxml")
    print(time.time() - t)

    # Figure out who won batted first to determine if looping 0+2 or 1+3
    ScorecardBowlingJSON = pd.read_html(MatchURL)
    BattedFirst = MatchSoup.find("h2").text.split()[0]

    # Get bowling table
    if hasattr(ScorecardBowlingJSON[-1], 'TEAM') is True:
        del ScorecardBowlingJSON[-1]  # Bugfix

    if BattedFirst in PlayerTeamName.title():
        ScorecardOppBowlingAll = np.vstack(
            np.array([ScorecardBowlingRaw.values for ScorecardBowlingRaw in ScorecardBowlingJSON[::2]]))
        ScorecardTeamBowlingAll = np.vstack(
            np.array([ScorecardBowlingRaw.values for ScorecardBowlingRaw in ScorecardBowlingJSON[1::2]]))
        ScorecardOppExtrasRaw = np.vstack(
            np.array([OppExtrasRaw.text for OppExtrasRaw in MatchSoup.findAll("div", {"class": "wrap extras"})[::2]]))
        print(np.size(ScorecardOppBowlingAll,1))
    else:
        ScorecardOppBowlingAll = np.vstack(
            np.array([ScorecardBowlingRaw.values for ScorecardBowlingRaw in ScorecardBowlingJSON[1::2]]))
        ScorecardTeamBowlingAll = np.vstack(
            np.array([ScorecardBowlingRaw.values for ScorecardBowlingRaw in ScorecardBowlingJSON[::2]]))
        ScorecardOppExtrasRaw = np.vstack(
            np.array([OppExtrasRaw.text for OppExtrasRaw in MatchSoup.findAll("div", {"class": "wrap extras"})[1::2]]))
        print(np.size(ScorecardOppBowlingAll, 1))

    # Get batting table
    AllBatsmanRawText = MatchSoup.findAll("div", {"class": "cell runs"})
    AllBatsmanRawNames = MatchSoup.findAll("div", {"class": "cell batsmen"})
    AllBatsmanRawCommentary = MatchSoup.findAll("div", {"class": "cell commentary"})

    BatsmanCommentary = np.vstack(
        np.array([BatsmanRawCommentary.text for BatsmanRawCommentary in AllBatsmanRawCommentary]))
    BatsmanNames = np.vstack(np.array([BatsmanRawNames.text for BatsmanRawNames in AllBatsmanRawNames]))

    # Pad out table if player is absent/scorecard incomplete (for wartime matches!)
    if 'absent hurt' in BatsmanCommentary:
        print(f"Absent player {MatchURL}")
        BatsmanTextUnfixed = [BatsmanRawText.text for BatsmanRawText in AllBatsmanRawText]
        for AbsentIndex in np.fliplr(np.where(np.array(BatsmanTextUnfixed) == ' - '))[0]:
            del BatsmanTextUnfixed[AbsentIndex]
            BatsmanTextUnfixed[AbsentIndex:AbsentIndex] = ['0', 'absent', 'absent', 'absent', 'absent', 'absent']
        BatsmanText = np.array(BatsmanTextUnfixed).reshape((-1, 6))
    else:
        BatsmanText = np.array([BatsmanRawText.text for BatsmanRawText in AllBatsmanRawText]).reshape((-1, 6))

    try:
        ScorecardBattingAll = np.concatenate((BatsmanNames, BatsmanText, BatsmanCommentary), 1)
    except ValueError:
        print('Corrupted Page. Skipping')
        continue

    # Get statistics for batting
    # Get player batting cards (need to search incase player is captain/keeper)
    ScorecardBatting = ScorecardBattingAll[
        np.where((np.chararray.find(ScorecardBattingAll[:, 0].astype(str), PlayerName) + 1) == 1)]

    # Get number of innings played
    BatsmanInnings[PrintLoop] = np.size(ScorecardBatting, 0)

    # Get number of runs made by batsman
    BatsmanRuns[PrintLoop] = np.sum(list(map(int, ScorecardBatting[:, 1])))

    # Get number of times not out
    BatsmanTimesNotOut[PrintLoop] = list(ScorecardBatting[:, 7]).count('not out')

    # Get average of bowlers
    BatsmanRunsConc = np.sum(ScorecardOppBowlingAll[:, 4])
    BatsmanExtras = np.sum(np.array(
        re.findall('\d+', str(re.findall('Extras\d+', str(ScorecardOppExtrasRaw))))).astype(int))
    BatsmanWickets = np.sum(ScorecardOppBowlingAll[:, 5])
    BatsmanNetBowling[PrintLoop] = (BatsmanRunsConc + BatsmanExtras) / BatsmanWickets

    # Calculate net score for batsman
    BatsmanNet[PrintLoop] = BatsmanRuns[PrintLoop] / (BatsmanInnings[PrintLoop] - BatsmanTimesNotOut[PrintLoop]) \
                            - BatsmanNetBowling[PrintLoop]

    # Get statistics for bowling
    # if BatBowlAllrounder == 2 | 3:
    #     ScorecardBowling = ScorecardBowlingAll[
    #         np.where((np.chararray.find(ScorecardBowlingAll[:, 0].astype(str), PlayerName) + 1) == 1)]
    # If haven't bowled, don't do anything!

    print(f"    Completed {AllMatchDate[PrintLoop]} vs {AllMatchOpp[PrintLoop]}")
    PrintLoop += 1

# Calculate Don Bradman Index