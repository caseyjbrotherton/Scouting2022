"""

# Gather TBA Data

Read an ini file regarding authorization, match and last update time.

Contact TBA and download information regarding match results for all matches, OPR for all teams, and overall insights for the event.
Save all of the information to a CSV for scouting.

TODO: understand last modified and format.
TODO: consider having a client that watches for changes and updates on demand.
"""

import configparser
import glob
import logging

import numpy as np
import pandas as pd

import re
import sys
import time
from datetime import date
import tbaapiv3client
from tbaapiv3client.rest import ApiException

def create_matches_df( event, api_response ):
   df = pd.DataFrame(columns=["event","match_number", "post_result_time",'tvalid',"predicted_time",
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
      if (  x.comp_level == "qm" ):
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
          red1 = int(re.sub('frc','',ra['team_keys'][0]))
          red2 = int(re.sub('frc','',ra['team_keys'][1]))
          red3 = int(re.sub('frc','',ra['team_keys'][2]))
          blue1 = int(re.sub('frc','',ba['team_keys'][0]))
          blue2 = int(re.sub('frc','',ba['team_keys'][1]))
          blue3 = int(re.sub('frc','',ba['team_keys'][2]))
   
        if ( ra['dq_team_keys'] or ba['dq_team_keys'] ):
          logger.warning('A match had dq teams.  Not sure what to do with this.  Match: %d' % x.match_number)
          logger.debug(ra)
          logger.debug(ba)

        # Match has been played because we have a score breakdown
        played = red is not None and blue is not None 
        df.loc[len(df)] = {'match_number' : x.match_number, 
           'post_result_time': time.strftime('%Y-%m-%d %H:%M', time.localtime(x.post_result_time)) if played else "", 
           'tvalid': "T" if played else "F",
           'predicted_time': time.strftime('%Y-%m-%d %H:%M', time.localtime(x.predicted_time)),
           'red1': red1, 'red2': red2, 'red3': red3,
           'red1_taxi': red['taxiRobot1'] if played else "", 
           'red2_taxi': red['taxiRobot2'] if played else "", 
           'red3_taxi': red['taxiRobot3'] if played else "", 
           'red1_climb': red['endgameRobot1'] if played else "", 
           'red2_climb': red['endgameRobot2'] if played else "", 
           'red3_climb': red['endgameRobot3'] if played else "",
           'red_points': red['totalPoints'] if played else 0,
           'red_fouls' : red['foulCount'] if played else 0,
           'red_techfouls' : red['techFoulCount'] if played else 0,
           'red_teleop_cargo' : red['teleopCargoTotal'] if played else 0,
           'red_auto_cargo' : red['autoCargoTotal'] if played else 0,
           'red_teleop_low' : red['teleopCargoLowerBlue'] + red['teleopCargoLowerFar'] + red['teleopCargoLowerNear'] + red['teleopCargoLowerRed'] 
                              if played else 0,
            'red_teleop_high' : red['teleopCargoUpperBlue'] + red['teleopCargoUpperFar'] + red['teleopCargoUpperNear'] + red['teleopCargoUpperRed'] 
                                if played else 0,
            'blue1': blue1, 'blue2': blue2, 'blue3': blue3,
            'blue1_taxi': blue['taxiRobot1'] if played else "", 
            'blue2_taxi': blue['taxiRobot2'] if played else "", 
            'blue3_taxi': blue['taxiRobot3'] if played else "", 
            'blue1_climb': blue['endgameRobot1'] if played else "", 
            'blue2_climb': blue['endgameRobot2'] if played else "", 
            'blue3_climb': blue['endgameRobot3'] if played else "",
            'blue_points': blue['totalPoints'] if played else 0,
            'blue_fouls' : blue['foulCount'] if played else 0,
            'blue_techfouls' : blue['techFoulCount'] if played else 0,
            'blue_teleop_cargo' : blue['teleopCargoTotal'] if played else 0,
            'blue_auto_cargo' : blue['autoCargoTotal'] if played else 0,
            'blue_teleop_low' : blue['teleopCargoLowerBlue'] + blue['teleopCargoLowerFar'] + blue['teleopCargoLowerNear'] + blue['teleopCargoLowerRed'] 
                                if played else 0,
            'blue_teleop_high' : blue['teleopCargoUpperBlue'] + blue['teleopCargoUpperFar'] + blue['teleopCargoUpperNear'] + blue['teleopCargoUpperRed']
                                 if played else 0
            }
        

   df = df.sort_values( by = ['match_number'] )
   df = df.fillna(0)
   return( df )

def create_teams_df( event, api_response ):
   df = pd.DataFrame(columns=["event","team","nickname"])
   for record in api_response:
     team = record.to_dict()
     df.loc[len(df)] = {'event': event, 'team': team['team_number'], 'nickname' : team['nickname'] }
   return( df )

def create_rank_df( event, api_response ):
   df = pd.DataFrame(columns=["event","team","rank","wins","losses","ties","dq"])
   for x in api_response.rankings:
     rank = x.to_dict() 
     team = re.sub('frc','',rank['team_key'])
     if ( re.match('^[0-9]+$',team) is None ):
         logger.error ( key + " does not match pattern expected of frc[0-9]* ")
         raise SystemExit("Need to stop")
     wlt = rank['record']
     df.loc[len(df)] = {'event': event, 'team': int(team), 'rank': rank['rank'], 
                        'wins': wlt['wins'], 'losses': wlt['losses'],
                        'ties': wlt['ties'], 'dq': rank['dq'] }
   return(df)

def create_oprs_df( event, api_response ):
   # OPR -> Offensive Power Rating
   # DPR -> Defensive Power Rating
   # CCWM -> “calculated contribution to win margin”
   df = pd.DataFrame( columns = ["event","team","ccwms","dprs","oprs"])

   result_data = api_response.to_dict()
   ccwms = result_data['ccwms']
   oprs = result_data['oprs']
   dprs = result_data['dprs']

   for key in oprs.keys() :
      team = re.sub('frc','', key )
      if ( re.match('^[0-9]+$',team) is None ):
         logger.error ( key + " does not match pattern expected of frc[0-9]* ")
         raise SystemExit("Need to stop")
      df.loc[len(df)] = {'event': event,'team': int(team), 'ccwms': ccwms[key], 'oprs': oprs[key], 'dprs': dprs[key]}
   return( df )

def process_matches( df ):
   # Breakdown tba information for each match per team.
   # Duplicate technical fouls, fouls, 
   # TODO: This feels clunky. Might be a more elegant way to do this.
   # extract all six climb placements and save them without the alliance name
   red=pd.DataFrame()
   red = df_matches[['match_number','post_result_time','tvalid','predicted_time','red1','red1_climb','red_fouls','red_techfouls']].rename(columns={'match_number':'match','red1':'team','red1_climb':'climb','red_fouls':'fouls','red_techfouls':'techfouls'})
   red=pd.concat([red,df[['match_number','post_result_time','tvalid','predicted_time','red2','red2_climb','red_fouls','red_techfouls']].rename(columns={'match_number':'match','red2':'team','red2_climb':'climb','red_fouls':'fouls','red_techfouls':'techfouls'})])
   red=pd.concat([red,df[['match_number','post_result_time','tvalid','predicted_time','red3','red3_climb','red_fouls','red_techfouls']].rename(columns={'match_number':'match','red3':'team','red3_climb':'climb','red_fouls':'fouls','red_techfouls':'techfouls'})])

   blue=pd.DataFrame()
   blue = df[['match_number','post_result_time','tvalid','predicted_time','blue1','blue1_climb','blue_fouls','blue_techfouls']].rename(columns={'match_number':'match','blue1':'team','blue1_climb':'climb','blue_fouls':'fouls','blue_techfouls':'techfouls'})
   blue=pd.concat([blue,df[['match_number','tvalid','post_result_time','predicted_time','blue2','blue2_climb','blue_fouls','blue_techfouls']].rename(columns={'match_number':'match','blue2':'team','blue2_climb':'climb','blue_fouls':'fouls','blue_techfouls':'techfouls'})])
   blue=pd.concat([blue,df[['match_number','tvalid','post_result_time','predicted_time','blue3','blue3_climb','blue_fouls','blue_techfouls']].rename(columns={'match_number':'match','blue3':'team','blue3_climb':'climb','blue_fouls':'fouls','blue_techfouls':'techfouls'})])

   red['alliance']='red'
   blue['alliance']='blue'
   cl=pd.DataFrame()
   cl=pd.concat([red,blue])
   cl.sort_values(['match','alliance'],inplace=True)
   return(cl)

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

# Gather the teams for the event
# TODO: modified since
with tbaapiv3client.ApiClient(configuration) as api_client:
    api_instance = tbaapiv3client.EventApi(api_client)
    try:
        get_event_teams_response = api_instance.get_event_teams(event_key)
        get_event_rankings_response = api_instance.get_event_rankings(event_key)
        get_event_oprs_response = api_instance.get_event_op_rs(event_key ) 
        get_event_matches_response = api_instance.get_event_matches(event_key ) 
    except ApiException as e:
        log.error("Calling EventApi for current event: %s" % e )
        raise SystemExit("Need to stop")

df_teams = create_teams_df(event_key,get_event_teams_response)
df_teams.to_csv('./data/tba_teams.csv', index=False)

df_rank = create_rank_df(event_key,get_event_rankings_response)
df_rank.to_csv('./data/tba_rank.csv', index=False)

df_oprs = create_oprs_df(event_key,get_event_oprs_response)
df_oprs.to_csv('./data/tba_oprs.csv', index=False)

df_matches = create_matches_df(event_key,get_event_matches_response)
df_matches.to_csv('./data/tba_matches.csv',  index=False)

df_matches_by_team = process_matches(df_matches)
df_matches_by_team.to_csv('./data/tba_matches_by_team.csv',  index=False)

# Gather previous events for all of the teams
prior_events = {}
today = date.today()
for team in df_teams.team:
   team_key = "frc" + str(team)
   with tbaapiv3client.ApiClient(configuration) as api_client:
      api_instance = tbaapiv3client.EventApi(api_client)
      try:
          api_response = api_instance.get_team_events_by_year(team_key, "2022" ) 
      except ApiException as e:
          #log.error("Calling EventApi for team list: %s" % e )
          raise SystemExit("Need to stop")

   for event in api_response:
      if ( event.end_date < today ):
         prior_events[event.key]=event.start_date

df_prior_matches_by_team = pd.DataFrame()
df_prior_oprs = pd.DataFrame()

for prior_event in prior_events.keys():
   with tbaapiv3client.ApiClient(configuration) as api_client:
      api_instance = tbaapiv3client.EventApi(api_client)
      try:
         get_prior_event_oprs_response = api_instance.get_event_op_rs( prior_event ) 
         get_prior_event_matches_response = api_instance.get_event_matches( prior_event ) 
      except ApiException as e:
          log.error("Calling EventApi for prior events: %s" % e )
          raise SystemExit("Need to stop")

   temp_oprs = create_oprs_df(prior_event,get_prior_event_oprs_response)
   temp_matches = create_matches_df(prior_event,get_prior_event_matches_response)
   temp_matches_by_team = process_matches(temp_matches)
   df_prior_oprs=pd.concat([temp_oprs[temp_oprs.team.isin(df_teams.team)],df_prior_oprs])
   df_prior_matches_by_team=pd.concat([temp_matches_by_team[temp_matches_by_team.team.isin(df_teams.team)],df_prior_matches_by_team])

df_prior_oprs.to_csv('./data/tba_prior_oprs.csv', index=False)
df_prior_matches_by_team.to_csv('./data/tba_prior_matches_by_team.csv', index=False)

