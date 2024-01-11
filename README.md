# wled-director
Simple light show coordinator written in python using yaml config files.

I have tried to lay out the config files in as much of an intuitive way as possible and commented where possible.  This is a learning project for me so I am sure there are much better ways to write/organize the code.

TODO:

10 - clean up code
10 - finish creating modules to handle common tasks
8 - figure out if we want to use a modified version of python-wled or continue pushing to JSON api directly.
    Pros to python-wled:
        - async
        - handles everything
    Cons:
        - named variables are lengthy rendering the need for conversion from yaml ( exists in from_dict? )

