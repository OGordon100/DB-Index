from espncricinfo.match import Match
import random
import urllib.request
import re
import numpy as np
from bs4 import BeautifulSoup
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

AllPlayers = {}

# Select a format & team
while True:
    try:
        PlayerTeamName = input('Enter a test playing nation: ').lower()
        PlayerTeamNum = NationNumsAll[PlayerTeamName]
        break
    except (NameError, KeyError):
        print('Team not found. Try again!')

# Parse cricinfo for list of all players
PlayerListURL = f"http://www.espncricinfo.com/england/content/player/caps.json?country={PlayerTeamNum!s};class=1"
PlayerListJSON = urllib.request.urlopen(PlayerListURL).read()
PlayerListSoup = BeautifulSoup(PlayerListJSON, "lxml")
PlayerListSoupLi = PlayerListSoup.find_all("li", {"class": "ciPlayername"})

for PlayerConstructor in PlayerListSoupLi:
    PlayerString = str(PlayerConstructor)
    PlayerURL = (PlayerConstructor.find('a', href=True)['href'])
    NamePos = PlayerString.find("middle;") + 9

    PlayerName = PlayerString[NamePos:len(PlayerString) - 9]
    PlayerNum = int(re.findall('\\d+', PlayerURL)[0])
    AllPlayers.update({PlayerName: PlayerNum})

print(f"Found {len(AllPlayers)!s} players for {PlayerTeamName.title()!s}")
