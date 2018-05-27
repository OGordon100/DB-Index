import urllib.request
from bs4 import BeautifulSoup
import re
import numpy as np
from DBFinder import DBCalculator
import random
import json
import os.path
import matplotlib.image as mpimg
import matplotlib.pyplot as plt

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

# Pick players
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
UpdateDB = 1
if os.path.isfile(f"./Images/{PlayerTeamName.title()}/{PlayerName}.png"):
    if input("Already in database. View result? [y/n]: ") == "y":
        fig = plt.imshow(mpimg.imread(f"./Images/{PlayerTeamName.title()}/{PlayerName}.png"))
        plt.axis('off')
        fig.axes.get_xaxis().set_visible(False)
        fig.axes.get_yaxis().set_visible(False)
        plt.show()
        UpdateDB = 0

if UpdateDB == 1:
    # Find DB index
    DB = DBCalculator(PlayerName, PlayerTeamName, PlayerNum)

    # Open DB database
    with open('Database.json', 'r') as fp:
        Database = json.load(fp)

    Database[PlayerName] = DB

    # Save DB database
    with open('Database.json', 'w') as fp:
        json.dump(Database, fp)
