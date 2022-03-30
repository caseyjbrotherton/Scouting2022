"""
# Process App Data

 This script will read data collected from 2729 Storm Robotics' Scouting Radar
and create match summaries 
 https://github.com/2729StormRobotics/ScoutingRadar2022
"""

# *TODO: Consider how we should handle dirty data*

import glob
import logging

import numpy as np
import pandas as pd

import sys

from common import canalytics
from common import CLIMB_POINTS
from common import CLIMB_NAMES
from common import ID_COLUMNS, DESC_COLUMNS, VALUE_COLUMNS

logging.basicConfig(stream=sys.stdout, level=logging.WARN) # restart the kernel after changing level
logger = logging.getLogger('Process_App')

columns_required = ID_COLUMNS + VALUE_COLUMNS + DESC_COLUMNS
df = pd.DataFrame(columns=columns_required)

# Read all of the CSVs available in the current directory, and combine them
for objective_file in glob.glob("objective*.csv"):
     temp = pd.read_csv(objective_file,na_filter=False)
     df = pd.concat([df,temp])
if ( df.empty ):
    logger.error('Something went wrong, we read no data.')
    raise SystemExit("Need to stop")
   
# If incremental copies of data occured, we could have duplicate lines of data.
# Safe to delete these duplicates
df.drop_duplicates( inplace = True)

# If scouting errors occurred, we could have duplicates across a team/match combination.
# We should print a message, and halt.  Problem needs to be fixed before we continue.
df_dup = df[df.duplicated( subset = ["team","match"], keep = False)]
if ( not df_dup.empty ):
     logger.error('There are duplicate entries for team/match with different results.')
     logger.debug(df_dup.sort_values( by = ["team","match"] ))
     raise SystemExit("Need to stop")
     
# Concat will set columns to NA if they don't exist in one of the concatenated dataframes.
# We can subset the dataframe to include just the required columns, 
# check each of the columns in each row, and return a dataframe with True in each row/column if the value is NA.
# and finally check for any True value across the entire dataframe 
# Otherwise something went wrong with the data collection, and best to throw an error now.
missing_columns = pd.isna(df[columns_required])
if ( missing_columns.any( axis = None)):
     logger.error("Missing data in one of the required columns" )
     missing_columns_series = missing_columns.any()
     logger.debug("Column list with at least one missing entry:")
     logger.debug( missing_columns_series[missing_columns_series] ) # print only columns in the series that have a value of True.
     raise SystemExit("Need to stop")
        
# TODO: Check and see if there are combinations that do not match TBA's match list.
# TODO: Consider whether we can continue with above problems.

# Change data to be one row per match/team/event/time.  
# Makes it easier to aggregate counts 
# Could be removed later if data stream changes.
events = df.melt( id_vars = ID_COLUMNS,
               value_vars = VALUE_COLUMNS,
               var_name = 'event', 
               value_name = 'time')
events = events.assign(time=events.time.str.split(";")).explode('time')

events = events[ events['time'] != '' ]

desc = df[ID_COLUMNS + DESC_COLUMNS]
desc=desc.rename(columns={"Endgame_Position" : "endgame_position"})

# Translate times into an integer to make easier comparisons.
events['time'] = events['time'].astype(int)
# create a new value for teleop, and auto that we can use to easily group by and aggregate
events['auto'] = '_teleop'
events.loc[events['time'] < 15, 'auto'] = '_auto'
# create a new key that designated teleop vs auto as well as lowercase to fit in with rest of code
events['combo'] = events['event'].apply( lambda x: x.lower()) + events['auto']

# Count all events that occured in a match, and merge them with text columns that were excluded out of events
summary_events=events.groupby(ID_COLUMNS + ['combo']).agg( 
    counts = pd.NamedAgg(column='time', aggfunc='count' ))
match_summary=summary_events.pivot_table( index = ID_COLUMNS, columns = 'combo', values = 'counts' )
match_summary=match_summary.merge(desc, on = ID_COLUMNS, how = 'left')


# Write match summary that we can do further aggregation and analysis on later.  
match_summary=match_summary.fillna(0)
match_summary.to_csv('./data/app_matches.csv')