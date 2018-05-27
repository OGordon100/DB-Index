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


def DBCalculator(player_name, player_team_name, player_num):
    # Get all matches player has played in
    all_match_url = (f'http://stats.espncricinfo.com/ci/engine/player/{player_num!s}'
                     '.json?class=1;template=results;type=allround;view=match')
    all_match_json = urllib.request.urlopen(all_match_url).read()
    all_match_soup = BeautifulSoup(all_match_json, "lxml")  # Make sure to retry!
    all_match_table = all_match_soup.findAll("table", {"class": "engineTable"})[3]
    all_match_date = np.array([MatchDate.text for MatchDate in all_match_soup.findAll("b")[3:-6]])
    all_match_opp = np.array([MatchOpp.text for MatchOpp in all_match_soup.findAll("a", {"class": "data-link"})[::2]])
    all_match_id = re.findall('\\d+', str(all_match_table.findAll("td", {"style": "white-space: nowrap;"})))[::2]

    # For each game played in
    print(f"Found {(len(all_match_id))!s} matches for {player_name}. Analysing...")
    batsman_times_not_out = np.zeros(len(all_match_id))
    batsman_runs = np.zeros(len(all_match_id))
    batsman_innings = np.zeros(len(all_match_id))
    batsman_net_bowling = np.zeros(len(all_match_id))
    batsman_net = np.zeros(len(all_match_id))
    home_away = np.zeros(len(all_match_id))
    home_away[:] = np.nan
    print_loop = 0

    for MatchID in all_match_id:

        # Open match URL
        t = time.time()
        match_url = f"http://www.espncricinfo.com/ci/engine/match/{MatchID!s}.html"  # Make sure to retry!
        while True:
            try:
                match_json = urllib.request.urlopen(match_url).read()
                break
            except urllib.error.HTTPError:
                print('         Server Timeout. Retrying...')
        match_soup = BeautifulSoup(match_json, "lxml")

        # Figure out who won batted first to determine if looping 0+2 or 1+3 for bowling card
        scorecard_bowling_json = pd.read_html(match_url)
        batted_first = match_soup.find("h2").text.split()[0]

        # Deal with too many tables being served for no reason
        for ExtraTableNum, ExtraTableFixData in enumerate(scorecard_bowling_json):
            if np.size(ExtraTableFixData, 1) < 10:
                del scorecard_bowling_json[ExtraTableNum]
        for ExtraTableNum, ExtraTableFixData in enumerate(scorecard_bowling_json):
            if np.size(ExtraTableFixData, 1) < 10:
                del scorecard_bowling_json[
                    ExtraTableNum]  # Built in compiler seems to skip 1 line, so need to run twice :(

        # Deal with abandoned matches
        if len(scorecard_bowling_json) <= 1:
            print(f"         {all_match_date[print_loop]} Abandoned. Skipping")
            batsman_net[print_loop] = float('nan')
            print_loop += 1
            continue

        # Deal with in progress matches
        in_progress_finder = match_soup.find("div", {"class": "wrap extras"})
        if str(in_progress_finder) == "None":
            print(f"         {all_match_date[print_loop]} Currently in Progress!")
            batsman_net[print_loop] = float('nan')
            print_loop += 1
            continue

        # Figure out home (=1) and away (=2) team (or neutral = 3)
        find_home_1 = match_soup.find("div", {"class": "cscore_info-overview"}).text.split("tour of")
        if not find_home_1:
            home_away[print_loop] = 3
        elif player_team_name.title() in find_home_1[0]:
            home_away[print_loop] = 2
        elif player_team_name.title() in find_home_1[1]:
            home_away[print_loop] = 1

        # Parse out actual bowling table (and extras which aren't in a table for some reason)
        if batted_first in player_team_name.title():
            scorecard_opp_bowling_all = np.vstack(
                np.array([ScorecardBowlingRaw.values for ScorecardBowlingRaw in scorecard_bowling_json[0:4][::2]]))
            scorecard_opp_extras_raw = np.vstack(
                np.array(
                    [OppExtrasRaw.text for OppExtrasRaw in match_soup.findAll("div", {"class": "wrap extras"})[::2]]))
        else:
            scorecard_opp_bowling_all = np.vstack(
                np.array([ScorecardBowlingRaw.values for ScorecardBowlingRaw in scorecard_bowling_json[0:4][1::2]]))
            scorecard_opp_extras_raw = np.vstack(
                np.array(
                    [OppExtrasRaw.text for OppExtrasRaw in match_soup.findAll("div", {"class": "wrap extras"})[1::2]]))

        # Get batting table (this part of the webpage is in an arbitrary non-table format for reasons unknown)
        all_batsman_raw_text = match_soup.findAll("div", {"class": "cell runs"})
        all_batsman_raw_names = match_soup.findAll("div", {"class": "cell batsmen"})
        all_batsman_raw_commentary = match_soup.findAll("div", {"class": "cell commentary"})

        batsman_commentary = np.vstack(
            np.array([BatsmanRawCommentary.text for BatsmanRawCommentary in all_batsman_raw_commentary]))

        batsman_names = np.vstack(np.array([BatsmanRawNames.text for BatsmanRawNames in all_batsman_raw_names]))

        # Find index of "R" to find out where each innings changes
        r_idx = np.array(())
        all_batsman_runs = []
        for idx, BatsmanRawText in enumerate(all_batsman_raw_text):
            # Find index of "R" to find out where each innings changes
            if BatsmanRawText.text == 'R':
                r_idx = np.append(r_idx, idx)
        num_innings = len(r_idx)
        r_idx = np.append(r_idx, len(all_batsman_raw_text) + 1)

        # For each innings
        for Innings in range(0, num_innings):
            # Get innings raw text
            InningsAllBatsmanRawText = all_batsman_raw_text[int(r_idx[Innings]):int(r_idx[Innings + 1])]

            # Find number of columns per innings (because some scorecards miss data)
            InningsNumColumns = 0
            for InningsBatsmanRawText in InningsAllBatsmanRawText:
                InningsNumColumns += len(re.findall("R|M|B|4s|6s|SR", InningsBatsmanRawText.text))

            # Pad out array if incomplete because of absent batsman (for wartime matches!)
            if 'absent hurt' in batsman_commentary:
                InningsBatsmanTextUnfixed = [InningsBatsmanRawText.text for InningsBatsmanRawText in
                                             InningsAllBatsmanRawText]
                PadLocations = np.fliplr(np.where(np.array(InningsBatsmanTextUnfixed) == ' - '))[0]
                if len(PadLocations) > 0:
                    for AbsentIndex in PadLocations:
                        del InningsBatsmanTextUnfixed[AbsentIndex]
                        InningsBatsmanTextUnfixed[AbsentIndex:AbsentIndex] = np.insert(
                            np.repeat('absent hurt', InningsNumColumns - 1), 0, '0')
                InningsAllBatsmanRawText = np.array(InningsBatsmanTextUnfixed)
                all_batsman_runs = np.append(all_batsman_runs, np.array(
                    [BatsmanRawText for BatsmanRawText in InningsAllBatsmanRawText[0::InningsNumColumns]]))
            else:
                all_batsman_runs = np.append(all_batsman_runs, np.array(
                    [BatsmanRawText.text for BatsmanRawText in InningsAllBatsmanRawText[0::InningsNumColumns]]))

        try:
            ScorecardBattingAll = np.concatenate((batsman_names, np.vstack(all_batsman_runs), batsman_commentary), 1)
        except ValueError:
            print(f"         {all_match_date[print_loop]} Corrupted. Skipping")
            batsman_net[print_loop] = float('nan')
            print_loop += 1
            continue

        # Get statistics for batting
        # Get player batting cards (need to search incase player is captain/keeper)
        ScorecardBatting = ScorecardBattingAll[
            np.where((np.chararray.find(ScorecardBattingAll[:, 0].astype(str), player_name) + 1) == 1)]

        # Get number of innings played
        batsman_innings[print_loop] = np.size(ScorecardBatting, 0)

        # Get number of runs made by batsman
        batsman_runs[print_loop] = np.sum(list(map(int, ScorecardBatting[:, 1])))

        # Get number of times not out
        batsman_times_not_out[print_loop] = list(ScorecardBatting[:, 2]).count('not out') \
                                            + list(ScorecardBatting[:, 2]).count('absent hurt')

        # Get average of bowler
        BatsmanRunsConc = np.sum(scorecard_opp_bowling_all[:, 4])
        BatsmanExtras = np.sum(np.array(
            re.findall('\d+', str(re.findall('Extras\d+', str(scorecard_opp_extras_raw))))).astype(int))
        BatsmanWickets = np.sum(scorecard_opp_bowling_all[:, 5])
        if BatsmanWickets > 0:
            batsman_net_bowling[print_loop] = (BatsmanRunsConc + BatsmanExtras) / BatsmanWickets
        else:
            print(f"         {all_match_date[print_loop]} Corrupted. Skipping")
            batsman_net[print_loop] = float('nan')
            print_loop += 1
            continue

        # Calculate net score for batsman (need to tweak equation if never got out or didn't play!)
        if list(ScorecardBatting[:, 2]).count('absent hurt') > 0:
            batsman_net[print_loop] = float('nan')
        elif batsman_innings[print_loop] - batsman_times_not_out[print_loop] == 0:
            batsman_net[print_loop] = batsman_runs[print_loop] - batsman_net_bowling[print_loop]
        else:
            batsman_net[print_loop] = batsman_runs[print_loop] / (
                        batsman_innings[print_loop] - batsman_times_not_out[print_loop]) \
                                      - batsman_net_bowling[print_loop]

        print(
            f"    Completed {print_loop+1}/{len(all_match_id)} ({(time.time() - t):.2f}s): {all_match_date[print_loop]} vs {all_match_opp[print_loop]} ")
        print_loop += 1

    # Calculate Don Bradman Index
    DBNet = 69.309311145510833
    m = 0.7214037937129101
    c = 50
    AllDBBatsman = (m * batsman_net) + c
    DBBatsman = np.zeros(len(all_match_id))
    for GamesPlayed in range(0, len(all_match_id)):
        DBBatsman[GamesPlayed] = np.round(np.nanmean(AllDBBatsman[0:GamesPlayed + 1]), 2)

    DB = {"Country": player_team_name.title(), "Dates": np.ndarray.tolist(all_match_date),
          "DB Index": np.ndarray.tolist(DBBatsman), "HomeAway": np.ndarray.tolist(home_away)}

    # Display results
    PlotDates = list(map(datetime.datetime.strptime, all_match_date, len(all_match_date) * ['%d %b %Y']))
    PlotFormat = dates.DateFormatter('%b %Y')
    plt.plot_date(PlotDates, DBBatsman, 'o-')
    plt.ylim(0, 110)
    plt.xlabel('Date')
    plt.ylabel('Don Bradman Index')
    plt.title(f"DB Index for {player_name} = {DBBatsman[-1]:.2f}")
    plt.gcf().axes[0].xaxis.set_major_formatter(PlotFormat)
    plt.gcf().autofmt_xdate(rotation=60)
    plt.savefig(f"Images/{player_team_name.title()}/{player_name}.png")
    # plt.show()
    plt.gcf().clear()
    return DB
