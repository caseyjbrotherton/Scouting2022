
# Climb point lookup
CLIMB_POINTS = dict([
    ('Traversal',15), # TBA terminology
    ('Traverse',15), # initial app config
    ('High',10),
    ('Mid',6),
    ('Low',4),
    ('None',0)])

CLIMB_NAMES = dict([
    (15,'Traversal'),
    (10,'High'),
    (6,'Mid'),
    (4,'Low'),
    (0,'None')])

# these are columns for the app data
# These columns will determine an id of a set of measurements.
ID_COLUMNS = ["team", "match"]
# These columns all contain time that an event occured
VALUE_COLUMNS = ["Taxi", "No_Move", "Upper_Hub", "Lower_Hub", "Miss", "Start_Climb"]
# These columns all contain a string that is not a time.
DESC_COLUMNS = ["is_red", "Notes"]


FIRST_AVG = 3
LAST_AVG = 3
TOTAL_AVG = FIRST_AVG + LAST_AVG
