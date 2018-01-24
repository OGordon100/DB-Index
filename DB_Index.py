###########################################################################
##        Don Bradman Batting Index (c), 2018                            ##
##    Don Bradman Batting Index is licensed under a Creative Common      ##
##      Creative Commons Attribution-NonCommercial-NoDerivatives 4.0     ##
##                          International License.                       ##
###########################################################################
##    You should have received a copy of the license along with this     ##
## work. If not, see <http://creativecommons.org/licenses/by-nc-sa/4.0/>.##
###########################################################################

from espncricinfo.match import Match
import random
import urllib.request
import re
import numpy as np
from bs4 import BeautifulSoup
from datetime import datetime
import matplotlib.pyplot as pyplot

###################################
## Get all batsmen for a given team
###################################

# Get URL containing players for a given team
def get_num(team_num):
    return {
        'england': 1,
        'australia': 2,
        'south africa': 3,
        'west indies': 4,
        'new zealand': 5,
        'india': 6,
        'pakistan': 7,
        'sri lanka': 8,
        'zimbabwe': 9,
        'bangladesh': 25,
    }[team_num]    
    print(team_num(team_name))
    
while True:
    try:
        team_name = input('Enter a test playing nation: ').lower()
        team_num = get_num(team_name)
        break
    except:
        print('Team not found. Try again!')

# Open cricinfo URL and parse for URLs containing player IDs
url_player = "http://www.espncricinfo.com/england/content/player/caps.json?country="+str(team_num)+";class=1"
json_text_player = urllib.request.urlopen(url_player).read()
soup_player = BeautifulSoup(json_text_player,"lxml")
soup_player_li = soup_player.find_all("li", {"class":"ciPlayername"})

# From parsed URLs, extract all player IDs and store
player_nums = np.array([])
for soup_loop in soup_player_li:
    link = (soup_loop.find('a', href=True)['href'])
    player_nums = np.append(player_nums,re.findall('\\d+', link))

player_names = np.chararray([])
for name_loop in soup_player_li:
    fullstr = str(name_loop)
    namepos = fullstr.find("middle;")+9
    player_names = np.append(player_names,fullstr[namepos:len(fullstr)-9])
player_names = np.delete(player_names,0)
    
print('Found '+str(player_nums.shape[0])+' players for '+ team_name.title())

###################################
## Select a batsman
###################################

# Pick individual batsman?
individual_name = input("Enter a name (e.g. "+random.choice(player_names)+") or type 'list' to list all " + team_name.title() + " players: \n")
while True:
    try: 
        if individual_name == 'list':
            print(player_names)
        individual_index_big = np.where(player_names==individual_name)
        individual_index = individual_index_big[0]
        # Get lookup stats
        loop_no = individual_index[0]
        batter_id = player_nums[loop_no]
        batter_name = player_names[loop_no]
        break
    except:
        individual_name = input("Enter a name (e.g. "
        +random.choice(player_names)+") or type 'list' to list all " + team_name.title() + " players: \n")

###################################
## For each invidividual batsman
###################################

# Get all matches batsman has played in
url_matches = "http://stats.espncricinfo.com/ci/engine/player/"+str(batter_id)+".json?class=1;template=results;type=allround;view=match"
json_text_matches = urllib.request.urlopen(url_matches).read()
soup_matches = BeautifulSoup(json_text_matches,"lxml")

# Get match IDs in a different way because cricinfo reuses classes -_-
soup_matches_li = soup_matches.find_all("tr",{"class":"data1"})
soup_matches_unparsed = soup_matches.findAll('a', href=re.compile('^/ci/engine/match/'))
match_nums = np.array([])
for text_loop in range(0,len(soup_matches_unparsed)-3):
    full_string = (str(soup_matches_unparsed[text_loop]))
    match_nums = np.append(match_nums,re.findall('\\d+', (full_string[:42])))

print('Found '+str(len(soup_matches_unparsed)-3)+' matches for '+batter_name+". Analysing")

###################################
## For all matches played in
###################################

# Get all scores made
soup_matches_score = soup_matches.find_all("tr",{"class":"data1"})
matchscore_all = np.array([])
oppscore_all = np.array([])
date_all = np.array([])

# Take pairs of scores (1st and 2nd innings)
def getLine(data, line_no):
    index = -1
    for _ in range(line_no):index = data.index('\n',index+1)
    return data[index+1:data.index('\n',index+1)]
for score_loop in range(1,(len(soup_matches_score))):
    # From each match summary, extract batsman score
    game_summary = str(soup_matches_score[score_loop])
    innings1 = re.findall('\\d+', getLine(game_summary,1))
    innings2 = re.findall('\\d+', getLine(game_summary,2))  
    if len(innings1) == 0:
        innings1 = 0
    else:
        innings1 = int(innings1[0])
    if len(innings2) == 0:
        innings2 = 0
    else:
        innings2 = int(innings2[0])
    
    # Get list of all match scores
    matchscore_all = np.append(matchscore_all,(innings1+innings2))


###################################
## For each match played in
###################################        
analyse_no = 0
for matchno in match_nums:
    analyse_no = analyse_no+1
    
    try:
        # Import match
        matchinfo = Match(matchno)
        pass
    except:
        # Very rarely the cricinfo page does not parse correctly. Carry on!
        matchscore_all = np.append(matchscore_all[0:analyse_no-1],
                                   matchscore_all[analyse_no:])
        print("Failed At Match "+str(analyse_no)+". The cricinfo page cannot be parsed.")
        continue
    
    # Get number of runs made by player (just for checking)
    # ematchscore = matchscore_all[analyse_no-1]
    
    # Determine which team (home/away) played for
    if int(matchinfo.team_1_id) == team_num:
        match_team = matchinfo.team_1_id
        opp_team = matchinfo.team_2_abbreviation
        opp_detail = matchinfo.team_2_players
        
    else:
        match_team = matchinfo.team_2_id
        opp_team = matchinfo.team_1_abbreviation
        opp_detail = matchinfo.team_1_players
    
    ###################################
    ## For each opposition bowler 
    ###################################
    
    # Look up each bowler in turn
    opp_ids = [d['object_id'] for d in opp_detail]
    opp_avg_all = np.array([])
    passing = 1
    for opp_loop in opp_ids:
        while True:
            try: 
                url_bowl = "http://stats.espncricinfo.com/ci/engine/player/"+str(opp_loop)+".json?class=1;template=results;type=bowling;view=match"
                json_text_bowl = urllib.request.urlopen(url_bowl).read()
            except:
                # Very rarely the cricinfo page refuses to respond. Make it!
                print("Failed Bowler "+str(opp_loop)+". The cricinfo page timed out. Retrying...")
                continue
            break
    
        # Parse it (badly)
        soup_bowl = BeautifulSoup(json_text_bowl,"lxml")
        soup_bowl_li = soup_bowl.find_all("tbody")
        soup_bowl_unparsed_temp = (soup_bowl_li[0])
        soup_bowl_unparsed = str(soup_bowl_unparsed_temp)
        soup_bowl_search = re.findall('<td(.*)</td>', soup_bowl_unparsed)
        soup_bowl_average = soup_bowl_search[len(soup_bowl_search)-6]
        
        # Check if stat entered for player (and that they clearly aren't a part timer)
        soup_bowl_test = soup_bowl_average[1]    
        if soup_bowl_test.isnumeric() == True:
            opp_avg_all = np.append(opp_avg_all,float(soup_bowl_average[1:]))
            if float(soup_bowl_average[1:]) > 50:
                     opp_avg_all = opp_avg_all[:-1]
        print('Completed Bowler '+str(opp_loop))             
    # Calculate overs bowled by bowler 
    # (turns out we can't do this with incomplete python APIs and a scorecard json that can have random extra crap with duplicate names)
    # Calculate mean bowling average of opposition
    opp_avg = np.mean(opp_avg_all)    
    oppscore_all = np.append(oppscore_all,opp_avg)
    date_all = np.append(date_all,np.datetime64(matchinfo.date).astype(datetime))
    print('Completed Match '+str(analyse_no)+': '+ matchinfo.date + ' vs ' + opp_team )

###################################
## Compare to DG Bradman
###################################    
    
# Get net runs of batsman vs all bowling they have faced :O
net_player = np.mean(matchscore_all-2*oppscore_all)
net_DB = 70.43 #!!!!!!!!!!!!!!

# Map to distribution
m = 0.638891996419767
c = 55
net_time = (matchscore_all-2*oppscore_all)

# Calculate mean over progressive games
DB_all = ((m*net_time)+c)
DB_moving = np.array([])
maxnum = range(0,len(DB_all-1))
for inc_loop in maxnum:
    DB_moving = np.append(DB_moving,np.mean((DB_all[:inc_loop+1])))

pyplot.title('Don Bradman Index of '+individual_name+ ' Over Career')
pyplot.plot_date(date_all,DB_moving,'-o')
pyplot.show()

print("\nCurrent Don Bradman Index for "+individual_name+" = " + str(round(DB_moving[-1],2)))
print("Maximum Don Bradman Index for "+individual_name+" = " + str(round(max(DB_moving),2)))
#print("std dev Don Bradman Index for "+individual_name+" = " + str(round(np.std(DB_all),2)))

###################################
## Fin'
################################### 
