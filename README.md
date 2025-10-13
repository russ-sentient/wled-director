# wled-director
Simple light show coordinator written in python using yaml config files.  WLED instances are defined in the hosts.yaml file.  The main config file is _config.yaml, all others are included from there.  Presets are basically WLED segment data, used as a building block for shows ( you can reuse most of the settings and override other settings in the show entry to add variation. )  Shows are defined in config/shows/*.yaml - most of my work is in christmas.yaml.  Give everything a look and ask questions if needed.  

This is a personal project for me to learn and have fun - the code is a beautiful mess, there are most likely 100 better ways to do this, and there are better solutions out there.  I have exploited yaml tags to add some procedural configuration options, which was fun to figure out and parse.


TODO:

Priority - Task
--------------------------
10 - clean up code.
10 - finish creating modules to handle common tasks.
8 - figure out if we want to use a modified version of python-wled or continue pushing to JSON api directly.
    Pros to python-wled:
        - async.
        - handles everything.
    Cons:
        - named variables are lengthy rendering the need for conversion from yaml ( exists in from_dict? ).

