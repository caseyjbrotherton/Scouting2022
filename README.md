# Scouting2022

This notebook will read data collected from [2729 Storm Robotics' Scouting Radar](https://github.com/2729StormRobotics/ScoutingRadar2022 )
as well as information from [The Blue Alliance](https://www.thebluealliance.com/apidocs/v3) in order to present information similar
to [Spamalytics 2022]( http://bit.ly/SPAMalytics2022 ) point rankings as well as additional information.

## Usage instructions:
- Copy tba.ini.sample to tba.ini
- replace the authorization key with your own authorization key
- Use the included scoutingConfig.ini for scouting, or change the python scripts to match your needs.
- Copy the exported objective_data.csv file from Scouting Radar into the directory with all of the notebooks.
- Python must be installed.
- Install [jupyter-lab](https://jupyter.org/install)
- Install [pandas](https://pandas.pydata.org/pandas-docs/stable/getting_started/install.html) *Which should install numpy as well*
- Install [bokeh extension for jupyter](https://github.com/bokeh/jupyter_bokeh)
- Install [The Blue Alliance Python API](https://github.com/TBA-API/tba-api-client-python)
- Start with **jupyter-lab**
- Run all "*Data" notebooks before running *Analysis notebooks.


## Todo
This is a work in progress, putting a github repository up with a minimum viable set of tables to work on improving and working with the 2158 to improve the output.

- Handle bad data gracefully.
- Check scouting data against match lineup
- More graphs with bokeh.  Right now there are only tables.
- Make the notebooks configurable for future years

