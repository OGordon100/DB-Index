# DB-Index
Don Bradman Index for Cricket Batting Ability

TO RUN:
  - Run the script, select a country and select a player (suggestions are included for you)
  - You can select any player who has ever played cricket (you can go back to the very first test match if desired!)
  - Wait a little while
  
CONTEXT:
  - In cricket, a batsman's ability is generally defined by their average
  - However, this does not take into account the ability of the bowlers they face.
  - This package does so, and then outputs an easy to understand number that "scores" a batsman relative to Don Bradman
      (aka the greatest player who ever lived)
  - 0 = terrible batsman, 100 = Don Bradman (this is set by definition, hence the "Don Bradman" index), >100 = better than Don Bradman
  - An average batsman who will typically score a number of runs equal to the combined average of the bowlers he faces scores 50.
  - The best players score at most 70, giving further indication of just how good Bradman was, because not only does he have a high index,
      but he has a high index relative to the ability of those around him.
