
from common import CLIMB_POINTS
# Replicate Spamlytics rankings for the data we have been collecting.
#  ( http://bit.ly/SPAMalytics2022 )
#  Tracks with the following : Team Number,Match Number,Starting Location,
#  Robot Preload (1) ,Taxi (2),Auto Cargo Acquired (1),Auto Cargo High Goal (3),Auto Cargo Low Goal (1),Auto Cargo Dropped (-1)
#  Cargo Acquired (0.5), Cargo High Goal (1.5), Cargo Low Goal (0.5), Cargo Dropped (-0.5) 
#  Defensive Performed (2), Defense Encountered (0), Hangar Attempt(0), Hang Level (15,10,6,4,0), Fouls (-3), Technical Fouls (-15)
#  We won't track Acquire, so remove penalty for miss, and bonus for acquire.  We also don't track fouls or defensive


def score(row):
    # From combined app and tba data, determine a score for the match
    # meant to be used as an apply over the already merged data
    if ( row.is_red == 'T' or row.is_red == 'F' ):
      return ( row.taxi_auto * 2 +
            row.upper_hub_auto * 4 +
            row.lower_hub_auto * 2 +
            row.upper_hub_teleop * 2 +
            row.lower_hub_teleop * 1 +
            CLIMB_POINTS[row.climb]
           )
    else:
        return (0)

def print_a(): print('a')