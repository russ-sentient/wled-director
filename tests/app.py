import asyncio
import colorsys
import random
import yaml
import json, httpx
from datetime import datetime, time, date, timedelta

my_host = "http://4.3.2.1"

def send( data:dict ):
    url = f"{my_host}/json/state"

    r = httpx.post( url=url, json=data )
    # debug( r )
    # if r.status_code == 200:
    #     debug( r.json() )

json_strip = ['udpn', 'ps', 'pl', 'nl', 'on', 'bri', 'transition', 'lor', 'mainseg' ]

palettes = ['Default', '* Random Cycle', '* Color 1', '* Colors 1&2', '* Color Gradient', '* Colors Only', 'Party', 'Cloud', 
            'Lava', 'Ocean', 'Forest', 'Rainbow', 'Rainbow Bands', 'Sunset', 'Rivendell', 'Breeze', 'Red & Blue', 'Yellowout', 
            'Analogous', 'Splash', 'Pastel', 'Sunset 2', 'Beech', 'Vintage', 'Departure', 'Landscape', 'Beach', 'Sherbet', 'Hult', 
            'Hult 64', 'Drywet', 'Jul', 'Grintage', 'Rewhi', 'Tertiary', 'Fire', 'Icefire', 'Cyane', 'Light Pink', 'Autumn', 
            'Magenta', 'Magred', 'Yelmag', 'Yelblu', 'Orange & Teal', 'Tiamat', 'April Night', 'Orangery', 'C9', 'Sakura', 'Aurora', 
            'Atlantica', 'C9 2', 'C9 New', 'Temperature', 'Aurora 2', 'Retro Clown', 'Candy', 'Toxy Reaf', 'Fairy Reaf', 'Semi Blue', 
            'Pink Candy', 'Red Reaf', 'Aqua Flash', 'Yelblu Hot', 'Lite Light', 'Red Flash', 'Blink Red', 'Red Shift', 'Red Tide', 'Candy2'
]

effects = ['Solid', 'Blink', 'Breathe', 'Wipe', 'Wipe Random', 'Random Colors', 'Sweep', 'Dynamic', 'Colorloop', 'Rainbow', 'Scan', 
          'Scan Dual', 'Fade', 'Theater', 'Theater Rainbow', 'Running', 'Saw', 'Twinkle', 'Dissolve', 'Dissolve Rnd', 'Sparkle', 
          'Sparkle Dark', 'Sparkle+', 'Strobe', 'Strobe Rainbow', 'Strobe Mega', 'Blink Rainbow', 'Android', 'Chase', 'Chase Random', 
          'Chase Rainbow', 'Chase Flash', 'Chase Flash Rnd', 'Rainbow Runner', 'Colorful', 'Traffic Light', 'Sweep Random', 'Chase 2', 
          'Aurora', 'Stream', 'Scanner', 'Lighthouse', 'Fireworks', 'Rain', 'Tetrix', 'Fire Flicker', 'Gradient', 'Loading', 'Police', 
          'Fairy', 'Two Dots', 'Fairytwinkle', 'Running Dual', 'Halloween', 'Chase 3', 'Tri Wipe', 'Tri Fade', 'Lightning', 'ICU', 
          'Multi Comet', 'Scanner Dual', 'Stream 2', 'Oscillate', 'Pride 2015', 'Juggle', 'Palette', 'Fire 2012', 'Colorwaves', 'Bpm', 
          'Fill Noise', 'Noise 1', 'Noise 2', 'Noise 3', 'Noise 4', 'Colortwinkles', 'Lake', 'Meteor', 'Meteor Smooth', 'Railway', 
          'Ripple', 'Twinklefox', 'Twinklecat', 'Halloween Eyes', 'Solid Pattern', 'Solid Pattern Tri', 'Spots', 'Spots Fade', 'Glitter', 
          'Candle', 'Fireworks Starburst', 'Fireworks 1D', 'Bouncing Balls', 'Sinelon', 'Sinelon Dual', 'Sinelon Rainbow', 'Popcorn', 'Drip', 
          'Plasma', 'Percent', 'Ripple Rainbow', 'Heartbeat', 'Pacifica', 'Candle Multi', 'Solid Glitter', 'Sunrise', 'Phased', 'Twinkleup', 
          'Noise Pal', 'Sine', 'Phased Noise', 'Flow', 'Chunchun', 'Dancing Shadows', 'Washing Machine', 'Candy Cane', 'Blends', 'TV Simulator', 
          'Dynamic Smooth'
]

def dump():
    url = f"{my_host}/json"

    r = httpx.get( url=url )

    debug( r.status_code )
    if r.status_code == 200:
        debug( r.json() )

        palettes = r.json()['palettes']
        effects = r.json()['effects']

        debug( f"{palettes=}\n\n{effects=}\n")


def recv():
    url = f"{my_host}/json/state"

    r = httpx.get( url=url )

    debug( r )
    if r.status_code == 200:
        debug( r.json() )

        data = r.json()

        for s in json_strip:
            if s in data:
                del data[s]
            else:
                debug( f"KeyError - {s}" )

        with open( "dump.json", "w" ) as file:
            json.dump( data, file, indent=3 )

        return data
    
    return None


#dump()
def wled_test1():
    d = recv()

    data = {
        'seg': [{
            'spc': 0,
            'grp': 1,
            'col': [
                [255, 0, 0],
                [0,0,255],
                [0,0,0]
            ],
            'pal': 3,
            'fx': 21
        },
        {
            'spc': 1,
            'grp': 1
        }]
    }

    if d:
        d.update( data )
        send( d )


def yaml_load():
    with open( 'wled.yaml', 'r' ) as file:
        config = yaml.load( file, yaml.Loader )
        debug( config )
        return config
    

def wheel( hue:int ) -> list:
    hue = 255 - hue
    if hue < 85:
        return [ 255 - hue * 3, 0, hue * 3 ]
    if hue < 170:
        hue -= 85
        return [ 0, hue * 3, 255 - hue * 3 ]
    hue -= 170
    return [ hue * 3, 255 - hue * 3, 0 ]

def random_hue() -> list:
    return wheel( random.randint(0, 255) )


def parse_scheme( scheme ):
    debug( f"parse_scheme( {scheme} )")

    for i_seg in range(len(scheme['seg'])):
        for i_col in range(len(scheme['seg'][i_seg]['col'])):
            # handle string values ( pull from libraries/handle active controls )
            col = scheme['seg'][i_seg]['col'][i_col]
            if isinstance( col, str ):
                if col[0] == '$':
                    if col[1:] == "random_hue":
                        scheme['seg'][i_seg]['col'][i_col] = random_hue()
                elif col in config['colors']:
                    scheme['seg'][i_seg]['col'][i_col] = config['colors'][col]
                else:
                    scheme['seg'][i_seg]['col'][i_col] = [0,0,0]
                    
    return scheme



config = yaml_load()

for s in config['schemes']:
    parse_scheme( config['schemes'][s] )


#wled_test1()