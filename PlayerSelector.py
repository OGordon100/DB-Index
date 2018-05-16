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

# Get all matches player has played in
AllMatchURL = (f'http://stats.espncricinfo.com/ci/engine/player/{PlayerNum!s}'
               '.json?class=1;template=results;type=allround;view=match')
AllMatchJSON = urllib.request.urlopen(AllMatchURL).read()
AllMatchSoup = BeautifulSoup(AllMatchJSON, "lxml")
AllMatchTable = AllMatchSoup.findAll("table", {"class": "engineTable"})[3]
MatchIDAll = re.findall('\\d+', str(AllMatchTable.findAll("td", {"style": "white-space: nowrap;"})))[::2]

# Get scorecard of each match played in
print(f"Found {(len(MatchIDAll))!s} matches for {PlayerName}. Analysing...")
for MatchID in MatchIDAll:

    print('Match')

    # Open URL
    MatchURL = f"http://www.espncricinfo.com/ci/engine/match/{MatchID!s}.html"
    MatchJSON = urllib.request.urlopen(MatchURL).read()
    MatchSoup = BeautifulSoup(MatchJSON, "lxml")

    # Get bowling table (this is how the internet is meant to be programmed)
    BowlingScorecard = pd.read_html(MatchURL)

    # Get batting table (this is how the internet is NOT meant to be programmed...)
    AllBatsmanRawText = MatchSoup.findAll("div", {"class": "cell runs"})
    AllBatsmanRawTextNames = MatchSoup.findAll("div", {"class": "cell batsmen"})
    BatsmanText = np.array([BatsmanRawText.text for BatsmanRawText in AllBatsmanRawText]).reshape((-1, 6))
    BatsmanNames = np.vstack(np.array([BatsmanRawTextNames.text for BatsmanRawTextNames in AllBatsmanRawTextNames]))
    BattingScorecard = np.concatenate((BatsmanNames,BatsmanText),1)
