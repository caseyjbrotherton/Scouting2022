"""

# Gather TBA Data

Read an ini file regarding authorization, match and last update time.

Contact TBA and download information regarding match results for all matches, OPR for all teams, and overall insights for the event.
Save all of the information to a CSV for scouting.

"""

import configparser
import glob
import logging

import numpy as np
import pandas as pd

import re
import sys
import time
import tbaapiv3client
from tbaapiv3client.rest import ApiException

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
logger = logging.getLogger('Gather TBA')

# Setup TBA connection
# make call to TBA for data
config = configparser.ConfigParser()
config.read(r'tba.ini')
event_key = config['TBA']['event_key']
configuration = tbaapiv3client.Configuration(
    host = config['TBA']['tbahost'] ,
    api_key = { 'X-TBA-Auth-Key': config['TBA']['auth_key'] }
)

# OPR -> Offensive Power Rating
# DPR -> Defensive Power Rating
# CCWM -> “calculated contribution to win margin”
df = pd.DataFrame( columns = ["team","ccwms","dprs","oprs"])

with tbaapiv3client.ApiClient(configuration) as api_client:
    api_instance = tbaapiv3client.EventApi(api_client)    
    try:
        api_response = api_instance.get_event_op_rs(event_key ) # TODO: if modified since
    except ApiException as e:
        log.error("Calling EventApi->get_event_op_rs: %s" % e)
        
result_data = api_response.to_dict()
ccwms = result_data['ccwms']
oprs = result_data['oprs']
dprs = result_data['dprs']

for key in oprs.keys() :
    team = re.sub('frc','', key )
    if ( re.match('^[0-9]+$',team) is None ):
        logger.error ( key + " does not match pattern expected of frc[0-9]* ")
        raise SystemExit("Need to stop")
    df.loc[len(df)] = {'team': team, 'ccwms': ccwms[key], 'oprs': oprs[key], 'dprs': dprs[key]}
df.to_csv('./data/tba_oprs.csv')

# get_event_matches will get those who are finished, as well as matches that are just scheduled.
# post_result_time will be "None" for matches that have not been played, yet.

with tbaapiv3client.ApiClient(configuration) as api_client:
    api_instance = tbaapiv3client.EventApi(api_client)    
    try:
        api_response = api_instance.get_event_matches(event_key ) # TODO: if modified since
    except ApiException as e:
        log.error("Calling EventApi->get_event_matches: %s" % e )
        
# Need to fully define frame to be able to create it one row at a time.
        
tba_matches = pd.DataFrame(columns=["match_number", "post_result_time","predicted_time",
                           "red1","red2","red3","red1_taxi","red2_taxi","red3_taxi",
                           "red1_climb","red2_climb","red3_climb","red_points",
                           "red_fouls","red_techfouls","red_teleop_cargo","red_auto_cargo",
                           "red_teleop_low","red_teleop_high",
                           "blue1","blue2","blue3","blue1_taxi","blue2_taxi","blue3_taxi",
                           "blue1_climb","blue2_climb","blue3_climb","blue_points",
                           "blue_fouls","blue_techfouls","blue_teleop_cargo","blue_auto_cargo",
                           "blue_teleop_low","blue_teleop_high",
                          ])
for x in api_response:
   if ( x.comp_level == "qm" ):
      #only gathering scouting information for the qualifying matches.
      if ( x.set_number != 1 ):
        logger.warning("Set Number non zero, not sure what to do with this.  Match: %d" % x.match_number)
        logger.debug(x)
      ra=x.alliances.to_dict()['red']
      ba=x.alliances.to_dict()['blue']
      if ( x.score_breakdown is None ):
        red = None
        blue = None
      else:  
        red=x.score_breakdown['red']
        blue=x.score_breakdown['blue']
      
      red1 = re.sub('frc','',ra['team_keys'][0])
      red2 = re.sub('frc','',ra['team_keys'][1])
      red3 = re.sub('frc','',ra['team_keys'][2])
      blue1 = re.sub('frc','',ba['team_keys'][0])
      blue2 = re.sub('frc','',ba['team_keys'][1])
      blue3 = re.sub('frc','',ba['team_keys'][2])
   
      if ( ra['dq_team_keys'] or ba['dq_team_keys'] ):
         logger.warning('A match had dq teams.  Not sure what to do with this.  Match: %d' % x.match_number)
         logger.debug(ra)
         logger.debug(ba)
        
      if ( red is None or blue is None ):
          # Match hasn't been played yet?
          #logger.debug(x)
          # TODO: more elegant way of doing this.  Maybe a list context?
          tba_matches.loc[len(tba_matches)] = {'match_number' : x.match_number, 
                         'post_result_time': "", 
                         'predicted_time': time.strftime('%Y-%m-%d %H:%M', time.localtime(x.predicted_time)),
                         'red1': red1, 'red2': red2, 'red3': red3,
                         'red1_taxi': "", 'red2_taxi': "", 'red3_taxi': "", 
                         'red1_climb': "None", 'red2_climb': "None" , 'red3_climb': "None",
                         'red_points': 0,
                         'red_fouls' : 0,
                         'red_techfouls' : 0,
                         'red_teleop_cargo' : 0,
                         'red_auto_cargo' : 0,
                         'red_teleop_low' : 0 ,
                         'red_teleop_high' : 0 ,
                         'blue1': blue1, 'blue2': blue2, 'blue3': blue3,
                         'blue1_taxi': "", 'blue2_taxi': "", 'blue3_taxi': "", 
                         'blue1_climb': "None", 'blue2_climb': "None", 'blue3_climb': "None",
                         'blue_points': 0,
                         'blue_fouls' : 0,
                         'blue_techfouls' : 0,
                         'blue_teleop_cargo' : 0,
                         'blue_auto_cargo' : 0,
                         'blue_teleop_low' : 0 ,
                         'blue_teleop_high' : 0 }            
      else:  
          tba_matches.loc[len(tba_matches)] = {'match_number' : x.match_number, 
                         'post_result_time': time.strftime('%Y-%m-%d %H:%M', time.localtime(x.post_result_time)), 
                         'predicted_time': time.strftime('%Y-%m-%d %H:%M', time.localtime(x.predicted_time)),
                         'red1': red1, 'red2': red2, 'red3': red3,
                         'red1_taxi': red['taxiRobot1'], 'red2_taxi': red['taxiRobot2'], 'red3_taxi': red['taxiRobot3'], 
                         'red1_climb': red['endgameRobot1'], 'red2_climb': red['endgameRobot2'], 'red3_climb': red['endgameRobot3'],
                         'red_points': red['totalPoints'],
                         'red_fouls' : red['foulCount'],
                         'red_techfouls' : red['techFoulCount'],
                         'red_teleop_cargo' : red['teleopCargoTotal'],
                         'red_auto_cargo' : red['autoCargoTotal'],
                         'red_teleop_low' : red['teleopCargoLowerBlue'] + red['teleopCargoLowerFar'] + red['teleopCargoLowerNear'] + red['teleopCargoLowerRed'] ,
                         'red_teleop_high' : red['teleopCargoUpperBlue'] + red['teleopCargoUpperFar'] + red['teleopCargoUpperNear'] + red['teleopCargoUpperRed'] ,
                         'blue1': blue1, 'blue2': blue2, 'blue3': blue3,
                         'blue1_taxi': blue['taxiRobot1'], 'blue2_taxi': blue['taxiRobot2'], 'blue3_taxi': blue['taxiRobot3'], 
                         'blue1_climb': blue['endgameRobot1'], 'blue2_climb': blue['endgameRobot2'], 'blue3_climb': blue['endgameRobot3'],
                         'blue_points': blue['totalPoints'],
                         'blue_fouls' : blue['foulCount'],
                         'blue_techfouls' : blue['techFoulCount'],
                         'blue_teleop_cargo' : blue['teleopCargoTotal'],
                         'blue_auto_cargo' : blue['autoCargoTotal'],
                         'blue_teleop_low' : blue['teleopCargoLowerBlue'] + blue['teleopCargoLowerFar'] + blue['teleopCargoLowerNear'] + blue['teleopCargoLowerRed'] ,
                         'blue_teleop_high' : blue['teleopCargoUpperBlue'] + blue['teleopCargoUpperFar'] + blue['teleopCargoUpperNear'] + blue['teleopCargoUpperRed'] }

      tba_matches = tba_matches.sort_values( by = ['match_number'] )
tba_matches = tba_matches.fillna(0)
tba_matches.to_csv('./data/tba_matches.csv')

# Breakdown tba information for each match per team.
# Duplicate technical fouls, fouls, 
# TODO: This feels clunky. Might be a more elegant way to do this.
# extract all six climb placements and save them without the alliance name
red=pd.DataFrame()
red = tba_matches[['match_number','post_result_time','predicted_time','red1','red1_climb','red_fouls','red_techfouls']].rename(columns={'match_number':'match','red1':'team','red1_climb':'climb','red_fouls':'fouls','red_techfouls':'techfouls'})
red=pd.concat([red,tba_matches[['match_number','post_result_time','predicted_time','red2','red2_climb','red_fouls','red_techfouls']].rename(columns={'match_number':'match','red2':'team','red2_climb':'climb','red_fouls':'fouls','red_techfouls':'techfouls'})])
red=pd.concat([red,tba_matches[['match_number','post_result_time','predicted_time','red3','red3_climb','red_fouls','red_techfouls']].rename(columns={'match_number':'match','red3':'team','red3_climb':'climb','red_fouls':'fouls','red_techfouls':'techfouls'})])

blue=pd.DataFrame()
blue = tba_matches[['match_number','post_result_time','predicted_time','blue1','blue1_climb','blue_fouls','blue_techfouls']].rename(columns={'match_number':'match','blue1':'team','blue1_climb':'climb','blue_fouls':'fouls','blue_techfouls':'techfouls'})
blue=pd.concat([blue,tba_matches[['match_number','post_result_time','predicted_time','blue2','blue2_climb','blue_fouls','blue_techfouls']].rename(columns={'match_number':'match','blue2':'team','blue2_climb':'climb','blue_fouls':'fouls','blue_techfouls':'techfouls'})])
blue=pd.concat([blue,tba_matches[['match_number','post_result_time','predicted_time','blue3','blue3_climb','blue_fouls','blue_techfouls']].rename(columns={'match_number':'match','blue3':'team','blue3_climb':'climb','blue_fouls':'fouls','blue_techfouls':'techfouls'})])

red['alliance']='red'
blue['alliance']='blue'
cl=pd.DataFrame()
cl=pd.concat([red,blue])
cl.sort_values(['match','alliance'],inplace=True)
cl.to_csv('./data/tba_matches_by_team.csv')
