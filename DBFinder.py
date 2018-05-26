import urllib.request
import pandas as pd
from bs4 import BeautifulSoup
import re
import numpy as np
from datetime import datetime
import matplotlib.pyplot as plt
from matplotlib import dates
import datetime
import time

def DBCalculator(PlayerName, PlayerTeamName, PlayerNum):
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
        MatchURL = f"http://www.espncricinfo.com/ci/engine/match/{MatchID!s}.html"  # Make sure to retry!
        while True:
            try:
                MatchJSON = urllib.request.urlopen(MatchURL).read()
                break
            except urllib.error.HTTPError:
                print('         Server Timeout. Retrying...')
        MatchSoup = BeautifulSoup(MatchJSON, "lxml")

        # Figure out who won batted first to determine if looping 0+2 or 1+3 for bowling card
        ScorecardBowlingJSON = pd.read_html(MatchURL)
        BattedFirst = MatchSoup.find("h2").text.split()[0]

        # Deal with too many tables being served for no reason
        for ExtraTableNum, ExtraTableFixData in enumerate(ScorecardBowlingJSON):
            if np.size(ExtraTableFixData, 1) < 10:
                del ScorecardBowlingJSON[ExtraTableNum]
        for ExtraTableNum, ExtraTableFixData in enumerate(ScorecardBowlingJSON):
            if np.size(ExtraTableFixData, 1) < 10:
                del ScorecardBowlingJSON[
                    ExtraTableNum]  # Built in compiler seems to skip 1 line, so need to run twice :(

        # Deal with abandoned matches
        if len(ScorecardBowlingJSON) <= 1:
            print(f"         {AllMatchDate[PrintLoop]} Abandoned. Skipping")
            BatsmanNet[PrintLoop] = float('nan')
            PrintLoop += 1
            continue

        # Deal with in progress matches
        InProgressFinder = MatchSoup.find("div", {"class": "wrap extras"})
        if str(InProgressFinder) == "None":
            print(f"         {AllMatchDate[PrintLoop]} Currently in Progress!")
            BatsmanNet[PrintLoop] = float('nan')
            PrintLoop += 1
            continue

        # Parse out actual bowling table (and extras which aren't in a table for some reason)
        if BattedFirst in PlayerTeamName.title():
            ScorecardOppBowlingAll = np.vstack(
                np.array([ScorecardBowlingRaw.values for ScorecardBowlingRaw in ScorecardBowlingJSON[0:4][::2]]))
            ScorecardOppExtrasRaw = np.vstack(
                np.array(
                    [OppExtrasRaw.text for OppExtrasRaw in MatchSoup.findAll("div", {"class": "wrap extras"})[::2]]))
        else:
            ScorecardOppBowlingAll = np.vstack(
                np.array([ScorecardBowlingRaw.values for ScorecardBowlingRaw in ScorecardBowlingJSON[0:4][1::2]]))
            ScorecardOppExtrasRaw = np.vstack(
                np.array(
                    [OppExtrasRaw.text for OppExtrasRaw in MatchSoup.findAll("div", {"class": "wrap extras"})[1::2]]))

        # Get batting table (this part of the webpage is in an arbitrary non-table format for reasons unknown)
        AllBatsmanRawText = MatchSoup.findAll("div", {"class": "cell runs"})
        AllBatsmanRawNames = MatchSoup.findAll("div", {"class": "cell batsmen"})
        AllBatsmanRawCommentary = MatchSoup.findAll("div", {"class": "cell commentary"})

        BatsmanCommentary = np.vstack(
            np.array([BatsmanRawCommentary.text for BatsmanRawCommentary in AllBatsmanRawCommentary]))

        BatsmanNames = np.vstack(np.array([BatsmanRawNames.text for BatsmanRawNames in AllBatsmanRawNames]))

        # Find index of "R" to find out where each innings changes
        RIdx = np.array(())
        AllBatsmanRuns = []
        for idx, BatsmanRawText in enumerate(AllBatsmanRawText):
            # Find index of "R" to find out where each innings changes
            if BatsmanRawText.text == 'R':
                RIdx = np.append(RIdx, idx)
        NumInnings = len(RIdx)
        RIdx = np.append(RIdx, len(AllBatsmanRawText) + 1)

        # For each innings
        for Innings in range(0, NumInnings):
            # Get innings raw text
            InningsAllBatsmanRawText = AllBatsmanRawText[int(RIdx[Innings]):int(RIdx[Innings + 1])]

            # Find number of columns per innings (because some scorecards miss data)
            InningsNumColumns = 0
            for InningsBatsmanRawText in InningsAllBatsmanRawText:
                InningsNumColumns += len(re.findall("R|M|B|4s|6s|SR", InningsBatsmanRawText.text))

            # Pad out array if incomplete because of absent batsman (for wartime matches!)
            if 'absent hurt' in BatsmanCommentary:
                InningsBatsmanTextUnfixed = [InningsBatsmanRawText.text for InningsBatsmanRawText in
                                             InningsAllBatsmanRawText]
                PadLocations = np.fliplr(np.where(np.array(InningsBatsmanTextUnfixed) == ' - '))[0]
                if len(PadLocations) > 0:
                    for AbsentIndex in PadLocations:
                        del InningsBatsmanTextUnfixed[AbsentIndex]
                        InningsBatsmanTextUnfixed[AbsentIndex:AbsentIndex] = np.insert(
                            np.repeat('absent hurt', InningsNumColumns - 1), 0, '0')
                InningsAllBatsmanRawText = np.array(InningsBatsmanTextUnfixed)
                AllBatsmanRuns = np.append(AllBatsmanRuns, np.array(
                    [BatsmanRawText for BatsmanRawText in InningsAllBatsmanRawText[0::InningsNumColumns]]))
            else:
                AllBatsmanRuns = np.append(AllBatsmanRuns, np.array(
                    [BatsmanRawText.text for BatsmanRawText in InningsAllBatsmanRawText[0::InningsNumColumns]]))

        try:
            ScorecardBattingAll = np.concatenate((BatsmanNames, np.vstack(AllBatsmanRuns), BatsmanCommentary), 1)
        except ValueError:
            print(f"         {AllMatchDate[PrintLoop]} Corrupted. Skipping")
            BatsmanNet[PrintLoop] = float('nan')
            PrintLoop += 1
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
        BatsmanTimesNotOut[PrintLoop] = list(ScorecardBatting[:, 2]).count('not out') \
                                        + list(ScorecardBatting[:, 2]).count('absent hurt')

        # Get average of bowler
        BatsmanRunsConc = np.sum(ScorecardOppBowlingAll[:, 4])
        BatsmanExtras = np.sum(np.array(
            re.findall('\d+', str(re.findall('Extras\d+', str(ScorecardOppExtrasRaw))))).astype(int))
        BatsmanWickets = np.sum(ScorecardOppBowlingAll[:, 5])
        if BatsmanWickets > 0:
            BatsmanNetBowling[PrintLoop] = (BatsmanRunsConc + BatsmanExtras) / BatsmanWickets
        else:
            print(f"         {AllMatchDate[PrintLoop]} Corrupted. Skipping")
            BatsmanNet[PrintLoop] = float('nan')
            PrintLoop += 1
            continue

        # Calculate net score for batsman (need to tweak equation if never got out or didn't play!)
        if list(ScorecardBatting[:, 2]).count('absent hurt') > 0:
            BatsmanNet[PrintLoop] = float('nan')
        elif BatsmanInnings[PrintLoop] - BatsmanTimesNotOut[PrintLoop] == 0:
            BatsmanNet[PrintLoop] = BatsmanRuns[PrintLoop] - BatsmanNetBowling[PrintLoop]
        else:
            BatsmanNet[PrintLoop] = BatsmanRuns[PrintLoop] / (BatsmanInnings[PrintLoop] - BatsmanTimesNotOut[PrintLoop]) \
                                    - BatsmanNetBowling[PrintLoop]

        print(
            f"    Completed {PrintLoop+1}/{len(AllMatchID)} ({(time.time() - t):.2f}s): {AllMatchDate[PrintLoop]} vs {AllMatchOpp[PrintLoop]} ")
        PrintLoop += 1

    # Calculate Don Bradman Index
    DBNet = 69.309311145510833
    m = 0.7214037937129101
    c = 50
    AllDBBatsman = (m * BatsmanNet) + c
    DBBatsman = np.zeros(len(AllMatchID))
    for GamesPlayed in range(0, len(AllMatchID)):
        DBBatsman[GamesPlayed] = np.round(np.nanmean(AllDBBatsman[0:GamesPlayed + 1]),2)

    DB = {"Country": PlayerTeamName.title(), "Dates": np.ndarray.tolist(AllMatchDate), "DB Index": np.ndarray.tolist(DBBatsman)}

    # Display results
    PlotDates = list(map(datetime.datetime.strptime, AllMatchDate, len(AllMatchDate) * ['%d %b %Y']))
    PlotFormat = dates.DateFormatter('%b %Y')
    plt.plot_date(PlotDates, DBBatsman, 'o-')
    plt.ylim(0, 110)
    plt.xlabel('Date')
    plt.ylabel('Don Bradman Index')
    plt.title(f"DB Index for {PlayerName} = {DBBatsman[-1]:.2f}")
    plt.gcf().axes[0].xaxis.set_major_formatter(PlotFormat)
    plt.gcf().autofmt_xdate(rotation=60)
    plt.savefig(f"Images/{PlayerTeamName.title()}/{PlayerName}.png")
    #plt.show()
    plt.gcf().clear()
    return DB
