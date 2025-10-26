# wled-director
Simple light show coordinator written in python using yaml config files.  WLED instances are defined in the hosts.yaml file.  The main config file is _config.yaml, all others are included from there.  Presets are basically WLED segment data, used as a building block for shows ( you can reuse most of the settings and override other settings in the show entry to add variation. )  Shows are defined in config/shows/*.yaml - most of my work is in christmas.yaml.  Give everything a look and ask questions if needed.  

This is a personal project for me to learn and have fun - the code is a beautiful mess, there are most likely 100 better ways to do this, and there are better solutions out there (xlights).  I have exploited yaml tags to add some procedural configuration options, which was fun to figure out and parse.

I have added code to handle RGB MQTT lights served via ESPHOME ( I picked up some Melpo BLE lights from Amazon and was able to find a ESPHOME project that bridges these to HA and MQTT ).  You could probably expose other rgb lights in Home Assistant via MQTT in a similar way ( I may try one of my RGB Hue bulbs ).

The configuration logic is quite wild, the entire project could use a rewrite.  I would like to nail down a more flexible configuration to cut down on redundancy - not needing multiple 'shows' just to change simple details ( do I want the floods to match the other lights, or be a complimentary hue, or be a separate color, etc. )  Would be nice to reference key colors or build lists of named colors and keyed colors on the fly in configuration.  It's tough because it becomes messy quick, or the config gets super long when using mapped yaml tag constructors.  Once again, its a learning process.

TODO (Priority - Task):
--------------------------
10 - clean up code, most likely a ground up rewrite once the goal is more clear<br>
10 - finish creating modules to handle common tasks.<br>


