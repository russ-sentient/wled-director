import yaml, httpx, random, copy, colorsys, re, json
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor

from libs.utils import scaleByte

import yaml_include

yaml.add_constructor("!include", yaml_include.Constructor(base_dir='./config'))

import atexit

# def timedelta_constructor( loader:yaml.FullLoader, node:yaml.MappingNode ) -> timedelta:
#     return timedelta( **loader.construct_mapping( node ) )

# def get_loader() -> yaml.FullLoader:
#     loader = yaml.FullLoader
#     loader.add_constructor( "!timedelta", timedelta_constructor )
#     return loader

class WDirector( ):

    ## Keys to strip out of a wled JSON pull before displaying it to the user.
    _json_strip = ['udpn', 'ps', 'pl', 'nl', 'on', 'bri', 'transition', 'lor', 'mainseg' ]


    _palettes = [   "Default","* Random Cycle","* Color 1","* Colors 1&2","* Color Gradient","* Colors Only","Party","Cloud","Lava","Ocean",
                    "Forest","Rainbow","Rainbow Bands","Sunset","Rivendell","Breeze","Red & Blue","Yellowout","Analogous","Splash",
                    "Pastel","Sunset 2","Beach","Vintage","Departure","Landscape","Beech","Sherbet","Hult","Hult 64",
                    "Drywet","Jul","Grintage","Rewhi","Tertiary","Fire","Icefire","Cyane","Light Pink","Autumn",
                    "Magenta","Magred","Yelmag","Yelblu","Orange & Teal","Tiamat","April Night","Orangery","C9","Sakura",
                    "Aurora","Atlantica","C9 2","C9 New","Temperature","Aurora 2","Retro Clown","Candy","Toxy Reaf","Fairy Reaf",
                    "Semi Blue","Pink Candy","Red Reaf","Aqua Flash","Yelblu Hot","Lite Light","Red Flash","Blink Red","Red Shift","Red Tide",
                    "Candy2"
            ]

    _effects = [    "Solid","Blink","Breathe","Wipe","Wipe Random","Random Colors","Sweep","Dynamic","Colorloop","Rainbow","Scan","Scan Dual","Fade","Theater",
                    "Theater Rainbow","Running","Saw","Twinkle","Dissolve","Dissolve Rnd","Sparkle","Sparkle Dark","Sparkle+","Strobe","Strobe Rainbow","Strobe Mega",
                    "Blink Rainbow","Android","Chase","Chase Random","Chase Rainbow","Chase Flash","Chase Flash Rnd","Rainbow Runner","Colorful","Traffic Light",
                    "Sweep Random","Chase 2","Aurora","Stream","Scanner","Lighthouse","Fireworks","Rain","Tetrix","Fire Flicker","Gradient","Loading","Rolling Balls",
                    "Fairy","Two Dots","Fairytwinkle","Running Dual","RSVD","Chase 3","Tri Wipe","Tri Fade","Lightning","ICU","Multi Comet","Scanner Dual","Stream 2",
                    "Oscillate","Pride 2015","Juggle","Palette","Fire 2012","Colorwaves","Bpm","Fill Noise","Noise 1","Noise 2","Noise 3","Noise 4","Colortwinkles",
                    "Lake","Meteor","Meteor Smooth","Railway","Ripple","Twinklefox","Twinklecat","Halloween Eyes","Solid Pattern","Solid Pattern Tri","Spots",
                    "Spots Fade","Glitter","Candle","Fireworks Starburst","Fireworks 1D","Bouncing Balls","Sinelon","Sinelon Dual","Sinelon Rainbow","Popcorn","Drip",
                    "Plasma","Percent","Ripple Rainbow","Heartbeat","Pacifica","Candle Multi","Solid Glitter","Sunrise","Phased","Twinkleup","Noise Pal","Sine",
                    "Phased Noise","Flow","Chunchun","Dancing Shadows","Washing Machine","RSVD","Blends","TV Simulator","Dynamic Smooth","Spaceships","Crazy Bees",
                    "Ghost Rider","Blobs","Scrolling Text","Drift Rose","Distortion Waves","Soap","Octopus","Waving Cell","Pixels","Pixelwave","Juggles","Matripix",
                    "Gravimeter","Plasmoid","Puddles","Midnoise","Noisemeter","Freqwave","Freqmatrix","GEQ","Waterfall","Freqpixels","RSVD","Noisefire","Puddlepeak",
                    "Noisemove","Noise2D","Perlin Move","Ripple Peak","Firenoise","Squared Swirl","RSVD","DNA","Matrix","Metaballs","Freqmap","Gravcenter","Gravcentric",
                    "Gravfreq","DJ Light","Funky Plank","RSVD","Pulser","Blurz","Drift","Waverly","Sun Radiation","Colored Bursts","Julia","RSVD","RSVD","RSVD","Game Of Life",
                    "Tartan","Polar Lights","Swirl","Lissajous","Frizzles","Plasma Ball","Flow Stripe","Hiphotic","Sindots","DNA Spiral","Black Hole","Wavesins","Rocktaves",
                    "Akemi"
            ]


    # @pyscript_compile
    def pullConfig( self ):
        try:
            with open( self.config_file, 'r' ) as file:
                self.config = yaml.load( file, yaml.FullLoader )
                #self.log.debug( f"{self.config_file} = {self.config}")
                new_show_types = list( dict(self.config['shows']).keys() ) + ['disabled']

                # Check if this is updated and publish list, also do initial pull here
                if not hasattr( self, 'list_show_types' ) or self.list_show_types != new_show_types:
                    self.list_show_types = new_show_types
                    self.log.debug( f"show_types updated: {self.list_show_types=}")
                    self.mqtt.Publish( "status/show_types", self.list_show_types )

        except BaseException as e:
            self.log.error( e )
            return False
        
        return True


    # @pyscript_compile
    def wled_post( self, host, data ):
        try:
            r = httpx.post( url=f"{host}/json/state", json=data )

            if r.status_code == 200:
                if self.config['debug']['wled_post']:
                    self.log.debug( f"{host} - {r.text}" )

                ## WARNINIG - not sure how threading effects this!!
                if host in self.wled_errors:
                    del self.wled_errors[host]

                return
        except BaseException as e:
            self.log.error( f"( {host} ) -> {e}")

            ## not sure how this handles threading!!
            if host not in self.wled_errors:
                self.wled_errors[host] = data
            else:
                self.mergeWLEDData( data, self.wled_errors[host] )


    # @pyscript_compile
    def wled_get( self, host, path="/json/state" ):
        r = httpx.get( url=f"{host}{path}" )

        if r.status_code == 200:
            return r.json()

        return None
    

    def getDefaultSegmentCount( self, host:str ):
        if host in self.config['hosts'] and 'default' in self.config['hosts'][host] and 'seg' in self.config['hosts'][host]['default']:
            return len(self.config['hosts'][host]['default']['seg'])
        else:
            self.log.warning( f"{host} not in self.config['hosts'] or contains no default segments, returning 1 segment - check config!" )
            return 1


    ## trim/duplicate segment data based on segment count in host definition.

    def fix_segments( self, data:dict, host:str ):
        # adjust segments to light ( trim/duplicate )
        if isinstance( data['seg'], dict ): return

        wled_segs = self.getDefaultSegmentCount( host )

        self.log.debug( f"{host}: {data}")

        custom_segs = 0
        for i, segment in enumerate(data['seg']):
            self.log.debug( f"{host}({i}): {segment}")
            if i < wled_segs: continue
            if "start" in segment and "stop" in segment:
                custom_segs += 1

        data_segs = len( data['seg'] )
        self.log.debug( f"{host}: {data_segs=}, {wled_segs=}, {custom_segs=}" )
        wled_segs += custom_segs

        if wled_segs > data_segs:
            for i in range( data_segs, wled_segs ):
                data['seg'].append( data['seg'][i%data_segs])
        elif wled_segs < data_segs:
            for i in range( wled_segs, data_segs ):
                data['seg'].pop(wled_segs)

        ## auto populate opposite spc and grp # WIP
        ## HACK: just do porch and garage for now
        if host in ['porch','garage']:
            blank_segs = []

            for seg in data['seg']:
                if "spc" in seg:
                    spc = seg['spc']

                    if spc > 0:
                        blank_segs.append( { "start":0, "stop":self.config['hosts'][host]['default']['seg'][0]['stop'], "fx":0, "pal":0, "col":["000000","000000","000000"], "spc": 1, "of": 1, "grp": spc } )
        
            if len( blank_segs ):
                data['seg'].extend( blank_segs )
                self.log.debug( f"{host} - {blank_segs}" )


    ## send data to all of the wled instances
    # @pyscript_compile
    def updateWLED( self, wled_data=None, simple:bool = False ):
        if wled_data == None:
            wled_data = self.wled_data

        req_hosts = []
        req_data = []

        debug_me = self.config['debug']['update_lights']

        for host, data in wled_data.items():
            if host not in self.config['hosts']:
                self.log.error( f"{host} not in config.hosts" )
                continue

            if debug_me: 
                self.log.debug( f"wled_data[{host}] (pre bri)= {data}")

            host_config = dict( self.config['hosts'][host] )

            if 'disabled' in host_config and host_config['disabled']:
                continue

            if not simple:
                if 'strip' in data:
                    if 'type' in host_config and host_config['type'] == 'strip':
                        self.parseData( data['strip'], "ul_strips" )
                        self.mergeWLEDData( data['strip'], data )
                    del data['strip']

                if 'bri' in host_config and 'bri' not in data:
                    data['bri'] = host_config['bri']

                self.fix_segments( data, host )

            if debug_me: 
                self.log.debug( f"wled_data[{host}](post bri)= {data}")

            req_hosts.append( host_config['hostname'] )
            req_data.append( data )

        with ThreadPoolExecutor(max_workers=7) as pool:
            pool.map(self.wled_post, req_hosts, req_data)

    def color_rgb_to_hsv( self, r:int, g:int, b:int ) -> list:
        rf = r/255
        gf = g/255
        bf = b/255

        ( hf, sf, vf ) = colorsys.rgb_to_hsv( rf, gf, bf )

        return [ int(hf*255), int(sf*255), int(vf*255) ]


    def color_hsv_to_rgb( self, h:int, s:int, v:int ) -> list:
        hf = h/255
        sf = s/255
        vf = v/255

        ( rf, gf, bf ) = colorsys.hsv_to_rgb( hf, sf, vf )

        return [ int(rf*255), int(gf*255), int(bf*255) ]

    def color_hue_shift( self, r:int, g:int, b:int, deg:int ) -> list:
        rf = r/255
        gf = g/255
        bf = b/255
        df = deg/360

        ( hf, sf, vf ) = colorsys.rgb_to_hsv( rf, gf, bf )
        hf = (hf + df) % 1.0
        ( rf, gf, bf ) = colorsys.hsv_to_rgb( hf, sf, vf )

        return [ int(rf*255), int(gf*255), int(bf*255) ]

    def random_hue( self, key:str, val:int = 255 ) -> list:
        return self.color_hsv_to_rgb( self.random_int( f"{key}%HUE", 256 ), 255, val )


    def random_list( self, key:str, lst:list, no_repeat:str = "" ) -> list:
        l_key = f"{key}%LIST"

        ## see if we have a key:
        if l_key in self.keyed_randoms:
            ## make sure this item is in the supplied list:
            if self.keyed_randoms[l_key] in lst:
                return self.keyed_randoms[l_key]

        choice = random.choice( lst )

        if no_repeat:
            nr_key = f"{no_repeat}%NORP"

            if nr_key in self.keyed_randoms:
                rem_lst = [ i for i in lst if i not in self.keyed_randoms[nr_key]]
                self.log.debug( f"{rem_lst=}" )

                if len(rem_lst) > 0:
                    choice = random.choice( rem_lst )
                    self.keyed_randoms[nr_key].append( choice )
                else:
                    self.log.warning( f"list ran out of choices: {lst=}, {self.keyed_randoms[nr_key]=}")
            else:
                self.keyed_randoms[nr_key] = [choice]

        self.keyed_randoms[l_key] = choice
        return choice


    def random_int( self, key:str, start:int = 0, end:int = 0 ) -> int:
        if "%" in key:
            int_key = key
        else:
            int_key = f"{key}%INT"

        if int_key in self.keyed_randoms:
            return self.keyed_randoms[int_key]

        if end:
            idx = random.randint( start, end )
        elif start:
            idx = random.randint( 0, start )
        else:
            self.log.error( "no start or end value, no existing key - returning zero.")
            idx = 0

        self.keyed_randoms[int_key] = idx
        return idx
    
    def random_bool( self, key:str, true:int = 50, false:int = 50 ):
        if "%" in key:
            b_key = key
        else:
            b_key = f"{key}%INT"

        if b_key in self.keyed_randoms:
            return self.keyed_randoms[b_key]
        else:
            res = random.randrange(0, true+false) < false
            self.keyed_randoms[b_key] = res
            return res

    ## scan final preset data structure and replace special tags / proper names with raw data so we can send it to WLED
    def parseData( self, data:dict, group:str ):
        if 'seg' not in data or isinstance( data['seg'], dict ):
            return
        
        segs = data['seg']

        for i_seg in range(len(data['seg'])):

            seg = segs[i_seg]

            if 'copy' in seg:
                ## try to copy info from another segment and merge it.
                copy_host = str(seg['copy'])

                if copy_host in self.wled_data:
                    data['seg'][i_seg].update(self.pullSyncData( self.wled_data[copy_host]['seg'][0] ))
                    self.linked_copies[group] = copy_host
                    continue

            ## look for named effects and replace with index

            if 'fx' in seg:
                fx = seg['fx']

                if isinstance( fx, str ):
                    if fx in self._effects:
                        data['seg'][i_seg]['fx'] = self._effects.index( fx )
                    else:
                        self.log.error( f"fx: {fx} not in self._effects!" )
                        data['seg'][i_seg]['fx'] = 0

            ## look for named palettes and replace with index
            if 'pal' in seg:
                pal = seg['pal']

                if isinstance( pal, str ):
                    if pal.startswith( "$list" ):
                        rb = re.findall( '[(](.*?)[)]', pal )
                        rx = re.findall( '<(.*?)>', pal )

                        if len( rx ):
                            rx = f"PAL%{rx[0]}"
                            self.log.debug( f"pal: key={rx}")
                        else:
                            rx = f"PAL%{group}"
                            self.log.debug( f"pal: group.key={rx}")

                        if not len(rb):
                            if rx in self.keyed_randoms:
                                pal = self.keyed_randoms[rx]
                            else:
                                self.log.error( f"pal: $list - must be in format $list('name') and/or <'key'>" )
                        else:
                            if rb[0] not in self.config['lists']['palettes']:
                                self.log.error( f"pal: $list('{rb[0]}') not in config.lists.palettes!" )
                            else:
                                pal = self.weightedPick( self.config['lists']['palettes'][rb[0]] )
                                self.keyed_randoms[rx] = pal

                    if pal in self._palettes:
                        data['seg'][i_seg]['pal'] = self._palettes.index( pal )
                    else:
                        self.log.error( f"pal: {pal} not in self._palettes!" )
                        data['seg'][i_seg]['pal'] = 0

            for int_tag in [ "sx", "ix", "c1", "c2", "c3", "spc", "grp" ]:
                if int_tag in seg:
                    val = seg[int_tag]

                    if isinstance( val, str ):
                        if val.startswith( "$rand" ):
                            rb = re.findall( '[(](.*?)[)]', val )
                            rx = re.findall( '<(.*?)>', val )
                            rand = 0

                            if not len( rx ):
                                rx = [ group, ]

                            if len(rb):
                                args = str( rb[0] ).split( "," )
                                if len(args) > 1:
                                    rand = self.random_int( rx[0], int( args[0] ), int( args[1] ) )
                                else:
                                    rand = self.random_int( rx[0], int( rb[0] ) )
                            else:
                                rand = self.random_int( rx[0], 0, 255 )  

                            self.log.info( f"{int_tag}: {val} = {rand}")
                            data['seg'][i_seg][int_tag] = rand

            for bool_tag in [ 'rev', 'mi' ]:
                if bool_tag in seg:
                    val = seg[bool_tag]

                    if isinstance( val, str ):
                        if val.startswith( "$rand" ):
                            rb = re.findall( '[(](.*?)[)]', val )
                            rx = re.findall( '<(.*?)>', val )
                            rand = False

                            if not len( rx ):
                                rx = [ group, ]

                            if len(rb):
                                args = str( rb[0] ).split( "," )
                                if len(args) > 1:
                                    rand = self.random_bool( rx[0], int( args[0] ), int( args[1] ) )
                                else:
                                    rand = self.random_bool( rx[0] )
                            else: 
                                rand = self.random_bool( rx[0] )  

                            self.log.info( f"{bool_tag}: {val} = {rand}")
                            data['seg'][i_seg][bool_tag] = rand



            ## look for color specific $tags / color names...
            if 'col' in seg:
                self.log.info( f"col: {seg['col']}" )

                if isinstance( seg['col'], str ):

                    if seg['col'].startswith( "$list" ):
                        rb = re.findall( '[(](.*?)[)]', seg['col'] )

                        if len(rb):
                            if rb[0] in self.config['lists']['colors']:
                                col_lst = self.config['lists']['colors'][rb[0]]

                                seg['col'] = col_lst[:min(3,len(col_lst))]

                                if len(col_lst) < 3:
                                    for i in range( 3-len(col_lst) ):
                                        seg['col'].append('black')
                            else:
                                self.log.error( f"col: $list({rb[0]}) not in config.lists.colors!" )

                        else:
                            self.log.error( f"col: $list - must be in format $list('name')" )

                for i_col in range(len(seg['col'])):
                    # handle string values ( pull from libraries/handle active controls )

                    col = seg['col'][i_col]

                    ## allow priority tag
                    if isinstance( col, str ) and col[0] == '^':
                        col = col[1:]

                        if self.curr_group_data and 'animate' in self.curr_group_data:
                            ani = self.curr_group_data['animate']

                            try:
                                ani['seg'][i_seg]['col'][i_col] = col
                                self.log.debug( f"forced animate seg[{i_seg}].col[{i_col}] to {col}")
                            except:
                                self.log.warning( f"failed to force animate color to {col}")

                    self.log.debug( f"col[{i_col}]={col}")

                    if isinstance( col, str ):
                        ## handle $ tags first, then fall through to name indexing
                        if col[0] == '$':
                            if col.startswith( "$rand_hue"):
                                rb = re.findall( '[(](.*?)[)]', col )
                                rx = re.findall( '<(.*?)>', col )

                                if len(rx):
                                    key = rx[0]
                                else:
                                    key = group

                                if len(rb):
                                    val = int( rb[0] )
                                else:
                                    val = 255

                                color = self.random_hue( key, val )
                                self.log.info( f"col[{i_col}]: rand_hue<{key}> = {color}")
                                data['seg'][i_seg]['col'][i_col] = color
                                continue

                            elif col.startswith( "$rand_list" ):
                                rb = re.findall( '[(](.*?)[)]', col )
                                rx = re.findall( '<(.*?)>', col )
                                no_rep = ""

                                if not len(rb):
                                    self.log.error( f"col: $rand_list must have '(list_name)', using black" )
                                    data['seg'][i_seg]['col'][i_col] = 'black'
                                    continue

                                if rb[0][0] == '!':
                                    rb[0] = rb[0][1:]
                                    no_rep = rb[0]

                                if rb[0] in self.config['lists']['colors']:
                                    n_col = self.random_list( rx[0] if len(rx) else group, self.config['lists']['colors'][rb[0]], no_rep )

                                    self.log.info( f"col[{i_col}]: $rand_list({rb[0]}) = {n_col=}")

                                    if isinstance( n_col, list ):
                                        data['seg'][i_seg]['col'][i_col] = n_col
                                        continue

                                    col = n_col
                                else:
                                    self.log.warning( f"$rand_list: {rb[0]} not in lists.colors!")

                        if col in self.config['colors']:
                            data['seg'][i_seg]['col'][i_col] = self.config['colors'][col]
                        else:
                            data['seg'][i_seg]['col'][i_col] = [0,0,0]
                            self.log.error( f"col: {col} not in config.colors!" )

    def turnOff( self ):
        data_blank = copy.deepcopy( self.config['defaults']['preset'] )
        self.parseData( data_blank, "all" )

        for host in self.wled_data:
            self.wled_data[host] = data_blank

        self.updateWLED()
        self.initWLEDData()
        self.wled_data.clear()

        self.initFloods()
        self.updateFloods()


    ## called every tick, handle any operation logic here ( handle timeout retries, pick new shows, handle animating shows )
    def Update( self ):
        now = datetime.now()

        if self.mqtt.wd_pull_config:
            self.pullConfig()
            self.mqtt.wd_pull_config = False

        if self.mqtt.wd_pick_show:
            self.time_pick_show = datetime.now()
            self.mqtt.wd_pick_show = False

        elif self.mqtt.wd_animate:
            if self.animate_duration < timedelta( minutes=20 ):
                self.time_animate = datetime.now()
            self.mqtt.wd_animate = False

        if now.second % 5 == 0:
            self.log.debug( f"Next show: {round((self.time_pick_show-now).total_seconds(),1)}s" )
            if self.time_animate:
                self.log.debug( f"Animate: {round((self.time_animate-now).total_seconds(),1)}s" )

        if self.time_pick_show <= now:
            if self.show_type == "disabled":
                self.turnOff() ## calls initWLEDData()

                self.time_pick_show = now + timedelta( seconds=30.0 )
                self.mqtt.sendTimes( {'pick_show': 30.0 } )

                self.mqtt.Publish( 'status/show_type', self.show_type )
                self.mqtt.Publish( 'status/show_name', "OFF" )

                return
            
            if self.pullConfig() and self.pickShow():
                show_duration = self.show_duration * self.mqtt.wd_show_duration
                self.time_pick_show = now + show_duration

                if self.animate_duration < self.show_duration:
                    animate_duration = self.animate_duration * self.mqtt.wd_show_duration
                    self.time_animate = now + animate_duration
                    self.mqtt.sendTimes( times={ "pick_show": show_duration.total_seconds(), 'animate':animate_duration.total_seconds() } )
                else: 
                    self.time_animate = now + self.animate_duration
                    self.mqtt.sendTimes( times={ "pick_show": show_duration.total_seconds(), 'animate':0.0 } )

                self.time_retry = timedelta( seconds=self.config['settings']['wled_retry']['seconds'] ) + now
                self.updateWLED()

                self.updateFloods()
                self.flood_rep_time = timedelta( seconds=self.config['settings']['flood_retry']['seconds'] ) + now
                self.flood_rep_cnt = self.config['settings']['flood_retry']['count']

                ##
            else:
                self.log.warning( "pickShow() or pullConfig() failed, retry in 10s" )
                self.time_pick_show = now + timedelta( seconds = 10 )
                self.time_retry = None

        elif self.time_animate and self.time_animate <= now:
            self.Animate()
            self.updateWLED()

            if self.animate_duration < self.show_duration:
                animate_duration = self.animate_duration * self.mqtt.wd_show_duration
                self.time_animate = now + animate_duration
                self.mqtt.sendTimes( times={'animate':animate_duration.total_seconds()} )
            else: 
                self.time_animate = now + self.animate_duration
                self.mqtt.sendTimes( times={'animate':0.0} )

            if ( self.time_pick_show - self.time_animate ) < self.animate_duration:
                self.time_animate = None


        elif self.time_retry and self.time_retry <= now:
            if len(self.wled_errors) and self.wled_retry_count:
                req_hosts = list( self.wled_errors.keys() )
                req_data = list( self.wled_errors.values() )

                with ThreadPoolExecutor(max_workers=7) as pool:
                    pool.map(self.wled_post,req_hosts, req_data)

                self.wled_retry_count -= 1
                self.time_retry = timedelta( seconds=self.config['settings']['wled_retry']['seconds'] ) + now
            else:
                self.wled_retry_count = 0
                self.time_retry = None


        if self.flood_rep_time and self.flood_rep_time <= now:
            if self.flood_rep_cnt:
                self.updateFloods()
                self.flood_rep_time = timedelta( seconds=self.config['settings']['flood_retry']['seconds'] ) + now
                self.flood_rep_cnt -= 1
            else:
                self.flood_rep_time = None


    ## search data for weights, either as value or as weight key of sub data use them to randomly pick a result from the available ones
    def weightedPick( self, data:dict ) -> str:
        if data:

            if len( data ) == 1:
                return next(iter(data))

            sum_wt = 0
            accum = 0

            for k, v in data.items():

                ## skip defaults special key
                if k == "defaults":
                    continue

                if isinstance( v, str ) and v.startswith( "test" ):
                    self.log.warning( f"test enabled for: {k}")
                    return k
                if isinstance( v, dict ):
                    if 'weight' in v:
                        ## if any element is labelled test we pick this one, if more than one will pick first
                        if isinstance( v['weight'], str ) and v['weight'].startswith( "test" ):
                            self.log.warning( f"test enabled for: {k}")
                            return k
                        elif isinstance( v['weight'], int ):
                            sum_wt += v['weight']
                    else:
                        v['weight'] = 50
                        sum_wt += 50

                elif isinstance( v, int ):
                    sum_wt += v
                ## if any element is labelled test we pick this one, if more than one will pick first
                elif isinstance( v, str ) and v == "test":
                    return k
                elif not v:
                    sum_wt += 50
                    data[k] = 50

            choice = random.randrange(0, sum_wt)
            self.log.debug( f"{choice=}")

            for k, v in data.items():
                if k == "defaults":
                    continue

                if isinstance( v, dict ):
                    accum += v['weight']
                elif isinstance( v, int ):
                    accum += v

                if choice <= accum:
                    self.log.debug( f"returning: {k}")
                    return k
        else:
            self.log.error( f"({data}) - no data passed!" )

        self.log.error( "not returning data!")
        return ""


    def mergeWLEDData( self, src, dest ):
        for k,v in src.items():
            if k == 'seg':
                continue
            dest[k] = v

        if 'seg' in src and 'seg' in dest:
            if isinstance( src['seg'], dict ) and 'i' in src['seg']:
                dest['seg'] = src['seg']
                dest = copy.deepcopy( dest )
                return
            
            src_segs = len( src['seg'] )
            dest_segs = len( dest['seg'] )

            if src_segs > dest_segs:
                ## HACK: fix custom segments temporarily
                custom_cnt = 0
                for seg in src['seg']:
                    if 'start' in seg and 'stop' in seg:
                        custom_cnt += 1

                if custom_cnt:
                    self.log.debug( f"custom segments detected, adding to destination" )
                    for i in range(dest_segs,src_segs):
                        dest['seg'].append( copy.deepcopy( src['seg'][i] ) )

            dest_segs = len( dest['seg'] )

            ## loop through destination.  If we have more destination segments, duplicate source, if less truncate:
            for i in range(dest_segs):
                for key in src['seg'][i%src_segs]:
                    if key == "col":
                        if isinstance( src['seg'][i%src_segs]['col'], str ):
                            dest['seg'][i]['col'] = src['seg'][i%src_segs]['col']
                            continue

                        for i_c in range(len(src['seg'][i%src_segs]['col'])):
                            d_col = dest['seg'][i]['col'][i_c]
                            s_col = src['seg'][i%src_segs]['col'][i_c]

                            ## the entire reason for all of this mess... if the destination color has the ^, dont fucking replace it
                            if isinstance( d_col, str ) and d_col[0] == "^":
                                if not (isinstance( s_col, str ) and s_col[0] == "^"):
                                    continue
                            
                            dest['seg'][i]['col'][i_c] = src['seg'][i%src_segs]['col'][i_c]
                    else:       
                        dest['seg'][i][key] = src['seg'][i%src_segs][key]

                #dest['seg'][i].update( src['seg'][i%src_segs] )            
        
        dest = copy.deepcopy( dest )

    def Animate( self ):
        if not self.show or not self.show_type:
            return
        
        self.keyed_randoms.clear()
        self.wled_errors.clear()
        old_wled_data = copy.deepcopy( self.wled_data )
        self.wled_data.clear()

        self.wled_retry_count = self.config['settings']['wled_retry']['count']
        self.time_retry = None

        debug_me = self.config['debug']['animate']
        show_data = self.config['shows'][self.show_type][self.show]

        if 'groups' not in show_data:
            return
        
        self.log.info( "ANIMATE ================================")
        
        for g_name, g_data in show_data['groups'].items():
            if 'animate' not in g_data:
                if 'data' in g_data:
                    g_data['animate'] = g_data['data']
                else:
                    continue

            self.log.info( f"GROUP: {g_name}")

            animate_data = copy.deepcopy( g_data['animate'] )
            if debug_me:
                self.log.debug( f"DATA Pre Parse: {animate_data}")
            self.parseData( animate_data, g_name )
            if debug_me:
                self.log.debug( f"DATA Pre Parse: {animate_data}")

            hosts = []

            if 'hosts' not in g_data:
                if g_name in self.config['hosts']:
                    hosts.append( g_name )
                    self.log.warning( f"self.config.shows.{self.show_type}.{self.show}.{g_name} has no hosts, using group name {g_name}" ) 
                elif g_name in self.config['lists']['hosts']:
                    hosts += self.config['lists']['hosts'][g_name]
                    self.log.warning( f"self.config.shows.{self.show_type}.{self.show}.{g_name} has no hosts, using group name {g_name} as host list" ) 
                else:
                    self.log.error( f"self.config.shows.{self.show_type}.{self.show}.{g_name} has no hosts and group name isn't in config.hosts!")
                    continue

            ## if we have a hosts 
            if 'hosts' in g_data:
                if isinstance( g_data['hosts'], str ):
                    g_data['hosts'] = [g_data['hosts'],]

                for host in g_data['hosts']:
                    if host.startswith( "$list" ):
                        rb = re.findall( "[(](.*?)[)]", host )
                        if len(rb):
                            if rb[0] not in self.config['lists']['hosts']:
                                self.log.error( f"{rb[0]} not in config.lists.hosts" )
                                continue

                            hosts += self.config['lists']['hosts'][rb[0]]
                        else:
                            self.log.error( f"{host} must be in format '$list(list_name)'" )
                            continue
                    else:
                        hosts.append( host )

            for host in hosts:
                self.wled_data[host] = copy.deepcopy(animate_data)

        for c_group, c_host in self.linked_copies.items():
            if c_group == 'angel':
                segs = old_wled_data[c_group]['seg']

                for i,seg in enumerate(segs):
                    if 'copy' in seg:
                        print( 'angel copy seg found' )
                        self.wled_data[c_group] = old_wled_data[c_group]
                        copy_host = seg['copy']
                        if copy_host in self.wled_data:
                            self.wled_data[c_group]['seg'][i].update( self.pullSyncData( self.wled_data[copy_host]['seg'][0] ) )
                        else:
                            self.log.error( f"Error with copy function: \n{self.show_type=}\n{self.linked_copies=}\n{seg=}")

    def pullSyncData( self, seg_data:dict ) -> dict:
        ret_data = dict()
        copy_fields = [ 'col', 'fx', 'pal', 'ix', 'sx', 'rev', 'mi' ]
        for field in copy_fields:
            if field in seg_data:
                ret_data[field] = seg_data[field]

        return copy.deepcopy( ret_data )

    def pickShow( self ) -> bool:
        self.log.info( "NEW SHOW ================================")

        ## clear data out...
        self.initWLEDData()

        show_type = self.show_type ## copy incase this changes during cycle

        debug_me = self.config['debug']['show_data']

        self.log.info( f"SHOW TYPE: {show_type}" )
        self.mqtt.Publish( 'status/show_type', show_type )

        if show_type in self.config['shows']:
            shows = self.config['shows'][show_type]

            # weighted pick for preset
            self.show = self.weightedPick( shows )

            self.log.info( f'SHOW: {self.show}')

            if not self.show:
                self.log.error( f"weighed_pick({shows}) returned None" )
                return False
            
            self.mqtt.Publish( 'status/show_name', self.show )

            show_data = shows[self.show]

            if debug_me:
                self.log.debug( f'\t{show_data=}')

            if 'groups' not in show_data or len( show_data['groups'] ) == 0:
                self.log.error( f"self.config.shows.{show_type}.{self.show} has no groups!")
                return False

            if 'duration' in show_data:
                self.show_duration = timedelta( seconds=show_data['duration'] )
            else:
                self.show_duration = timedelta( seconds=self.config['defaults']['duration'] )

            if 'animate' in show_data:
                if isinstance( show_data['animate'], str ) and show_data['animate'].startswith( "$rand" ):
                    val = show_data['animate']
                    key = "ANIMATE"
                    rb = re.findall( '[(](.*?)[)]', val )
                    rand = 0

                    if len(rb):
                        args = str( rb[0] ).split( "," )
                        if len(args) > 1:
                            rand = self.random_int( key, int( args[0] ), int( args[1] ) )
                        else:
                            rand = self.random_int( key, int( rb[0] ) )
                    else:
                        rand = self.random_int( key, 0, 255 )  

                    self.animate_duration = timedelta( seconds=rand )
                else:
                    self.animate_duration = timedelta( seconds=show_data['animate'] )


            ## TODO: fix this, we need to search down into the groups and figure out if angel is included in hosts.
            if not self.config['hosts']['angel']['disabled'] and 'angel' not in show_data['groups']:
                show_data['groups']['angel'] = self.config['defaults']['angel']

            ## loop through groups:
            for g_name, g_data in show_data['groups'].items():
                
                self.log.info( f'GROUP: {g_name}')
                self.curr_group_data = g_data
                self.curr_group_name = g_name

                if debug_me:
                    self.log.debug( f"\t{g_data=}")

                # if isinstance( g_data, str ):
                #     if g_data not in self.config['presets']:
                #         log.error( f"group data is string but {g_data} is not in config.presets" )
                #         continue
            

                hosts = []

                if 'hosts' not in g_data:
                    if g_name in self.config['hosts']:
                        hosts.append( g_name )
                        self.log.info( f"self.config.shows.{show_type}.{self.show}.{g_name} has no hosts, using group name {g_name}" ) 
                    elif g_name in self.config['lists']['hosts']:
                        hosts += self.config['lists']['hosts'][g_name]
                        self.log.info( f"self.config.shows.{show_type}.{self.show}.{g_name} has no hosts, using group name {g_name} as host list" ) 
                    else:
                        self.log.error( f"self.config.shows.{show_type}.{self.show}.{g_name} has no hosts and group name isn't in config.hosts!")
                        continue

                my_data = copy.deepcopy( self.config['defaults']['preset'] )

                if debug_me:
                    self.log.debug( f"\tmy_data: {my_data}")


                ## if a preset is defined parse it to my_data:
                if "preset" in g_data:
                    preset = ""

                    if g_data['preset'].startswith( "$list" ):
                        l_name = g_data['preset']

                        rb = re.findall( "[(](.*?)[)]", g_data['preset'] )
                        rx = re.findall( "<(.*?)>", g_data['preset'] )

                        ## FIXME: could cause undesired effects if we want to re-roll this during this show.
                        ## see if we have a random key, if not use the group name
                        if not len( rx ):
                            rx = [ g_name ]

                        p_key = f"{rx[0]}%PRESET"

                        if p_key in self.keyed_randoms:
                            preset = self.keyed_randoms[p_key]

                        elif len( rb ) > 0:
                            self.log.debug( f"rb: {rb}")
                            pick_list = {}

                            for item in rb:
                                # add single preset to base list with probability ex: (random_rgb%50)
                                if item.find("%") >= 0:
                                    spl = item.split("%", maxsplit=1)
                                    if spl[0] not in self.config['presets']:
                                        self.log.error( f"({item}) - '{spl[0]}' is not a valid preset")
                                        continue
                                    
                                    if spl[1].find( "test" ) >= 0:
                                        prob = "test"
                                    else:
                                        try:
                                            prob = int( spl[1] )
                                        except:
                                            self.log.error( f"({item}) - '{spl[1]}' value after % must be integer" )
                                            continue

                                    pick_list[spl[0]] = prob
                                elif item in self.config['lists']['presets']:
                                    pick_list.update( self.config['lists']['presets'][item] )
                                else:
                                    self.log.error( f"({item}) - not valid, check config" )
                            
                            preset = self.weightedPick( pick_list )
                            self.keyed_randoms[p_key] = preset

                        else:
                            self.log.error( f"{l_name} must be in format '$list<key>(list_name)(preset%percentage)'" )
                            return False

                    else:
                        preset = g_data['preset']

                    self.log.info( f"PRESET: {preset}")

                    if preset not in self.config['presets']:
                        self.log.error( f"self.config.shows.{show_type}.{self.show}.{g_name}.{preset} not in config.presets!")
                    else:
                        ## FIXME: this kills custom segments!
                        self.mergeWLEDData( copy.deepcopy( self.config['presets'][preset] ), my_data )

                        if debug_me:
                            self.log.debug( f"\tmy_data: {my_data}")

                if 'global' in show_data:
                    self.mergeWLEDData( show_data['global'], my_data )

                data = None

                if 'data' in g_data:
                    self.log.debug( "DATA:" )

                    if debug_me:
                        self.log.debug( f"\tdata: {g_data['data']}" )

                    self.mergeWLEDData( g_data['data'], my_data )

                    if debug_me:
                        self.log.debug( f"\tmy_data: {my_data}")

                    ## for fallthrough updates:
                    data = copy.deepcopy( g_data['data'] )
                    self.parseData( data, g_name )
                    

                self.log.info( "PARSE:" )
                self.parseData( my_data, g_name )

                if debug_me:
                    self.log.debug( f'\tmy_data: {my_data}')

                ## if we have a hosts 
                if 'hosts' in g_data:
                    if isinstance( g_data['hosts'], str ):
                        g_data['hosts'] = [g_data['hosts'],]

                    for host in g_data['hosts']:
                        if host.startswith( "$list" ):
                            rb = re.findall( "[(](.*?)[)]", host )
                            if len(rb):
                                if rb[0] not in self.config['lists']['hosts']:
                                    self.log.error( f"{rb[0]} not in config.lists.hosts" )
                                    continue

                                hosts += self.config['lists']['hosts'][rb[0]]
                            else:
                                self.log.error( f"{host} must be in format '$list(list_name)'" )
                                continue
                        else:
                            hosts.append( host )

                for host in hosts:
                    if data and host in self.wled_data:
                        print( "ANNDDD CRASH!" )
                        self.mergeWLEDData( data, self.wled_data[host] )
                    else:
                        self.wled_data[host] = copy.deepcopy(my_data)
                
                self.last_data[g_name] = copy.deepcopy(my_data)

            fl_hosts_used = list()
            
            ## check for mqtt floods
            if 'floods' in show_data and 'floods' in self.config:
                for f_name, f_data in show_data['floods'].items():

                    if 'chance' in f_data and f_data['chance'] <= random.randrange(0,100):
                        self.log.info( f"Floods <{f_name}>: Chance of {f_data['chance']} did not pass, continuing..." )
                        continue

                    f_data = f_data['data']
                    parsed_fdata = self.parseFloodData( f_name, f_data )

                    if f_name in self.config['floods']:
                        fl_hosts_used.append(f_name)
                        self.flood_data[f_name] = copy.deepcopy(parsed_fdata)
                    elif 'floods' in self.config['lists'] and f_name in self.config['lists']['floods']:
                        for fl_name in self.config['lists']['floods'][f_name]:
                            fl_hosts_used.append(fl_name)
                            self.flood_data[fl_name] = copy.deepcopy(parsed_fdata)

            ## show specific defaults, check against data, if data keys missing
            if 'defaults' in self.config['shows'][show_type]:
                show_defaults = self.config['shows'][show_type]['defaults']

                if 'floods' in show_defaults and len(fl_hosts_used) < len(self.config['floods']):
                    for df_name, df_data in show_defaults['floods'].items():

                        ## TODO: add ability to use lists here?
                        if df_name not in fl_hosts_used and (df_name in self.config['floods']):

                            if 'chance' in df_data and df_data['chance'] <= random.randrange(0,100):
                                self.log.info( f"Defaults -> Floods <{df_name}>: Chance of {df_data['chance']} did not pass, continuing..." )
                                continue

                            df_data = df_data['data']
                            parsed_fdata = self.parseFloodData( df_name, df_data )

                            if df_name in self.config['floods']:
                                self.flood_data[df_name] = copy.deepcopy(parsed_fdata)

                if 'wled' in show_defaults:
                    for df_name, df_data in show_defaults['wled'].items():
                        if 'data' in df_data and df_name in self.config['hosts']:
                            d_my_data = df_data['data']
                            self.parseData( d_my_data, f"DEFAULT%{df_name}" )
                            self.wled_data[df_name] = copy.deepcopy( d_my_data )

        else:
            self.log.error( f"{show_type} not in config.shows!" )
            return False

        return True
    
    # push default flood data to flood data dict
    def initFloods( self ):
        self.flood_rep_time = None
        self.flood_rep_cnt = 0

        for f_name in self.config['floods']:
            self.flood_data[f_name] = { 'brightness': 0 }

    def updateFloods( self ):
        for fh_name, fh_data in self.config['floods'].items():
            if 'disabled' in fh_data and not fh_data['disabled']:
                f_data = self.flood_data[fh_name]

                ## add ability to scale brightness and rgb per light.  crude attempt at gamma balancing lights to other lights.
                if 'scalars' in fh_data:
                    scalars = fh_data['scalars']
                    if 'brightness' in scalars and 'brightness' in f_data:
                        f_data['brightness'] = scaleByte( f_data['brightness'], scalars['brightness'] )

                    if 'color' in f_data:
                        if 'r' in scalars and 'r' in f_data['color']:
                            f_data['color']['r'] = scaleByte( f_data['color']['r'], scalars['r'] )
                        if 'g' in scalars and 'g' in f_data['color']:
                            f_data['color']['g'] = scaleByte( f_data['color']['g'], scalars['g'] )
                        if 'b' in scalars and 'b' in f_data['color']:
                            f_data['color']['b'] = scaleByte( f_data['color']['b'], scalars['b'] )

                    if 'hue' in scalars and  'color' in f_data and {'r', 'g', 'b'}.issubset(f_data['color'].keys()):
                        ( f_data['color']['r'], f_data['color']['g'], f_data['color']['b'] ) = \
                            self.color_hue_shift( f_data['color']['r'], f_data['color']['g'], f_data['color']['b'], scalars['hue'])

                self.log.info( f"{fh_name=} {self.flood_data[fh_name]=}")
                self.mqtt.Publish( fh_data['topic'], self.flood_data[fh_name] )

    def parseFloodData( self, f_name, f_data ) -> dict:
        col_titles = ['r','g','b']
        pf_data = dict()

        ## HACK: turn on floods
        pf_data['state'] = 'ON'
 
        if 'bri' in f_data:
            pf_data['brightness'] = f_data['bri']

        if 'col' in f_data:
            pf_data['color'] = dict()

            col = f_data['col']

            if isinstance( col, str ):
                ## handle $ tags first, then fall through to name indexing
                if col[0] == '$':
                    if col.startswith( "$rand_hue"):
                        rb = re.findall( '[(](.*?)[)]', col )
                        rx = re.findall( '<(.*?)>', col )

                        if len(rx):
                            key = rx[0]
                        else:
                            key = f_name

                        if len(rb):
                            val = int( rb[0] )
                        else:
                            val = 255

                        color = self.random_hue( key, val )
                        self.log.info( f"col: rand_hue<{key}> = {color}")
                        col = color

                    elif col.startswith( "$rand_list" ):
                        rb = re.findall( '[(](.*?)[)]', col )
                        rx = re.findall( '<(.*?)>', col )
                        no_rep = ""

                        if not len(rb):
                            self.log.error( f"col: $rand_list must have '(list_name)', using black" )
                            col = 'black'

                        if rb[0][0] == '!':
                            rb[0] = rb[0][1:]
                            no_rep = rb[0]

                        if rb[0] in self.config['lists']['colors']:
                            n_col = self.random_list( rx[0] if len(rx) else f_name, self.config['lists']['colors'][rb[0]], no_rep )

                            self.log.info( f"col: $rand_list({rb[0]}) = {n_col=}")

                            col = n_col
                        else:
                            self.log.warning( f"$rand_list: {rb[0]} not in lists.colors!")

                if isinstance( col, str ):
                    if col in self.config['colors']:
                        col = self.config['colors'][col]
                    else:
                        col = [0,0,0]
                        self.log.error( f"col: {col} not in config.colors!" )

            if isinstance( col, list ):
                for i, val in enumerate(col):
                    pf_data['color'][col_titles[i]] = val

            if sum(col) == 0:
                pf_data['brightness'] = 0

        return pf_data


    # def ha_pull_config_now( self ):
    #     self.ha_pull_config = True

    def initWLEDSegments( self ):
        ## maybe we just push default segment information to all wled nodes...
        
        my_wledData = {}

        for k in self.config['hosts']:
            # self.log.debug( f"{k}")

            if 'disabled' in self.config['hosts'][k] and self.config['hosts'][k]['disabled']:
                continue

            host_config = self.config['hosts'][k]

            if 'default' in host_config: ## here we go - new segment setup
                my_wledData[k] = {}

                for tag in host_config['default']:
                    if tag in ['seg', 'bri']: continue
                    my_wledData[k][tag] = host_config['default'][tag]

                segments = list( host_config['default']['seg'] )

                ## black out default segments
                if self.config['settings']['blank_all_hosts'] or self.show_type == "disabled":
                    for seg in segments:
                        seg.update({ "pal": 0, "col": [[0,0,0],[0,0,0],[0,0,0]], "grp": 1, "spc": 0 })

                ## delete any additional segments
                for i in range(len(segments),10):
                    segments.append( {'stop':0} )

                my_wledData[k]['seg'] = list(segments)

                # self.log.debug( f"{k} - {my_wledData[k]}")
            else:
                self.log.error( f"host '{k}' - does not contain default parameter!" )

        self.updateWLED( my_wledData, simple=True )

    def initWLEDData( self ):
        ## default segment data:
        self.initWLEDSegments()

        # clear retained data from last show
        self.wled_errors.clear()
        self.keyed_randoms.clear()
        self.wled_retry_count = self.config['settings']['wled_retry']['count']
        self.time_retry = None
        self.time_animate = None

        self.animate_duration = timedelta( days=14 )

        self.wled_data.clear()
        self.flood_data.clear()
        self.last_data.clear()

        self.linked_copies.clear()

        ## hack for over-riding forced animation colors
        self.curr_group_data = None
        self.curr_group_name = ''

        if self.config['settings']['blank_all_hosts'] or self.show_type == "disabled":
            for k in self.config['hosts']:
                self.wled_data[k] = { 'seg': [] }

                for i in range( self.getDefaultSegmentCount(k) ):
                    self.wled_data[k]['seg'].append( { "pal": 0, "col": [[0,0,0],[0,0,0],[0,0,0]], "grp": 1, "spc": 0 } )

        self.initFloods()

    def __del__( self ):
        self.log.info( "exiting..." )
        del self.mqtt

    
    def __init__( self ):
        self.log = WLDLogger.get( self.__class__.__name__ )

        self.log.debug( "Starting MQTT Connection..." )
        
        atexit.register(self.__del__)

        self.mqtt = WDMqtt( self, "wled_director" )

        self.log.debug( "Pulling initial configuration data..." )

        self.config_file = "./config/_config.yaml"
        self.pullConfig( )

        self.log.debug( "Initializing class data..." )
        
        random.seed( datetime.now().microsecond )

        ## setup the data registers
        self.flood_data = dict()

        self.wled_data = dict()
        self.last_data = dict()
        self.wled_errors = dict()
        self.linked_copies = dict()
        self.keyed_randoms = dict()

        self.curr_group_data = dict()
        self.curr_group_name = ""

        self.time_pick_show     = datetime.now()
        self.time_retry         = None
        self.time_animate       = None

        self.flood_rep_time     = None
        self.flood_rep_cnt      = 0

        self.show_duration      = timedelta( seconds= 5 )
        self.animate_duration   = timedelta( days= 14 )
        self.show               = ""
        self.show_type          = 'disabled'

        self.mqtt.startLoop()
        
        if 'show_type' in self.config['defaults']:
            self.show_type      = self.config['defaults']['show_type']

        self.initWLEDData()

        self.log.debug( "Initialization complete!" )


from libs.mqtt import WDMqtt
from libs.logger import WLDLogger

