"""

combine_data

Read TBA data as well as app collected scouting data.

Combine, and summarize for use later on.

"""

import glob
import logging

import numpy as np
import pandas as pd

import sys

from common import canalytics
from common import TOTAL_AVG,FIRST_AVG,LAST_AVG
from common import CLIMB_POINTS
from common import CLIMB_NAMES

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
logger = logging.getLogger('Combine_Data')

# Without index_col=0, pandas will create a new, made up index for each line read from a csv created from a pandas dataframe
# TODO: write csv's without index.
tba_oprs = pd.read_csv('./data/tba_oprs.csv',index_col=0)
app_matches = pd.read_csv('./data/app_matches.csv',index_col=0)
tba_matches_by_team = pd.read_csv('./data/tba_matches_by_team.csv',index_col=0)

prescouting = pd.read_csv('./data/prescouting.csv')


matches = tba_matches_by_team.merge(app_matches,on=["team","match"],how="outer")
    
# predicted_time should be valid for all tba matches.  Any scouting line without a tba predicted time is likely recorded incorrectly.
incorrect_scouting = matches[ pd.isna(matches['predicted_time']) ]
if ( incorrect_scouting.any( axis = None)):
     logger.debug("Scouting without tba:" )
     logger.debug(incorrect_scouting)
     #logger.debug("match: %s team: %s".format(x.match,x.team)) for x in incorrect_scouting 

matches.dropna(subset=['predicted_time'],inplace=True)   
matches['scouting_points'] = matches.apply(canalytics.score,axis=1)
matches['climb_points'] = matches.apply( lambda row: CLIMB_POINTS[row.climb], axis=1)

# Any match that doesn't have is_red doesn't have any scouting data.
# let's make an indicator variable to help with averages.
matches['scouting_valid'] = 0

matches.loc[matches['is_red'] == 'T', 'scouting_valid'] = 1
matches.loc[matches['is_red'] == 'F', 'scouting_valid'] = 1
# similarly, with a TBA row without a post_result_time
# TODO, check for the right way to check for tba to be valid.
matches['tba_valid'] = 0
matches.loc[matches['post_result_time'] != 'None' , 'tba_valid'] = 1
matches['tba_and_scouting_valid'] = 0
matches.loc[(matches['scouting_valid'] == 1) & (matches['tba_valid'] == 1) , 'tba_and_scouting_valid' ] = 1

# If our scouting shows a start climb, and TBA has no score for the climb, and both are valid, then it is a Falied climb.
matches['climb_failed'] = 0
matches.loc[( matches['start_climb_teleop'] > 0 ) & ( matches['climb_points'] == 0 ) , 'climb_failed'] = 1

matches.fillna(0)
matches.to_csv("./data/match_summary.csv")

team_summary = matches.groupby('team').agg( 
                                      valid_scouting = pd.NamedAgg(column='scouting_valid', aggfunc='sum'),
                                      valid_tba = pd.NamedAgg(column='tba_valid', aggfunc='sum'),
                                      valid_tba_and_scouting = pd.NamedAgg(column='tba_and_scouting_valid', aggfunc='sum'),
                                      scouting_points_total = pd.NamedAgg(column='scouting_points', aggfunc = 'sum' ),
                                      climb_success_total = pd.NamedAgg(column = 'climb_points', aggfunc = lambda x: sum(x.where(x==0,other=1)) ),
                                      climb_failed_total = pd.NamedAgg(column = 'climb_failed', aggfunc = 'sum' ),
                                      climb_points_total = pd.NamedAgg(column = 'climb_points', aggfunc = 'sum' ),
                                      teleop_cargo_upper_total = pd.NamedAgg(column = 'upper_hub_teleop', aggfunc = 'sum' ),
                                      teleop_cargo_lower_total = pd.NamedAgg(column = 'lower_hub_teleop', aggfunc = 'sum' ),
                                      auto_cargo_upper_total = pd.NamedAgg(column = 'upper_hub_auto', aggfunc = 'sum' ),
                                      auto_cargo_lower_total = pd.NamedAgg(column = 'lower_hub_auto', aggfunc = 'sum' ),
                                      highest_climb_points = pd.NamedAgg(column='climb_points', aggfunc='max'),
                                      #first_avg = pd.NamedAgg(column=['scouting_points','scouting_valid'], aggfunc = lambda x:  sum(x.head(FIRST_AVG))/FIRST_AVG if x.size >= TOTAL_AVG else 0),
                                      #first_few = pd.NamedAgg(column='scouting_points', aggfunc = lambda x: ",".join(str(i) for i in x.head(FIRST_AVG))),
                                      last_few = pd.NamedAgg(column='scouting_points', aggfunc = lambda x: ",".join(str(i) for i in x.tail(LAST_AVG))),
                                      last_avg = pd.NamedAgg(column='scouting_points', aggfunc = lambda x: sum(x.tail(LAST_AVG))/LAST_AVG if x.size >=TOTAL_AVG else 0))
                                                         

team_summary['scouting_points_avg'] = team_summary.scouting_points_total / team_summary.valid_scouting
team_summary['climb_success_pct'] = 100 * ( team_summary.climb_success_total / team_summary.valid_tba )
team_summary['climb_failure_pct'] = 100 * ( team_summary.climb_failed_total / team_summary.valid_tba_and_scouting )
team_summary['total_cargo_avg'] = ( team_summary.auto_cargo_upper_total + team_summary.auto_cargo_lower_total + team_summary.teleop_cargo_upper_total + team_summary.teleop_cargo_lower_total ) /  team_summary.valid_scouting
team_summary['auto_cargo_avg'] = ( team_summary.auto_cargo_upper_total + team_summary.auto_cargo_lower_total ) / team_summary.valid_scouting
team_summary['teleop_cargo_avg'] = ( team_summary.teleop_cargo_upper_total + team_summary.teleop_cargo_lower_total ) / team_summary.valid_scouting
team_summary['climb_points_avg'] = ( team_summary.climb_points_total ) / team_summary.valid_tba
team_summary['highest_endgame_position']=team_summary.apply( lambda row: CLIMB_NAMES[row.highest_climb_points], axis=1)
team_summary.rename(columns={'valid_tba' : 'matches'  , 'valid_scouting' : 'scouted_matches' }, inplace=True)

team_summary=team_summary.merge(tba_oprs, on='team', how="left")
team_summary=team_summary.merge(prescouting, on='team', how="left")
team_summary.rename(columns={'OPR': 'pre_oprs','Climb Points' : 'pre_climb_points', 'District Ranking' : 'pre_district_rank', 'District Points Earned' : 'pre_district_points' } , inplace=True)
team_summary=team_summary[['team','matches','scouted_matches','scouting_points_avg', 'first_avg','last_avg','climb_success_pct','climb_failure_pct','total_cargo_avg',
                           'auto_cargo_avg','teleop_cargo_avg','climb_points_avg','highest_endgame_position','oprs','pre_oprs', 'pre_climb_points', 'pre_district_rank', 'pre_district_points' ]]
team_summary.to_csv("./data/team_summary.csv")


