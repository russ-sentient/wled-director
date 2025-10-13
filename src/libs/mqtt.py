from paho.mqtt import client as mqtt_client
from director import WDirector
from .logger import WLDLogger
from typing import Callable
from datetime import timedelta
from math import floor
import json

class WDMqtt:
    ## Callbacks:
    def _wd_pick_show_now( self, client, userdata, message ):
         self.log.info( "mqtt: pick show now" )
         self.wd_pick_show = True

    def _wd_animate_now( self, client, userdata, message ):
         self.log.info( "mqtt: animate now" )
         self.wd_animate = True

    def _wd_pull_config_now( self, client, userdata, message ):
         self.log.info( "mqtt: pull_config now" )
         self.wd_pull_config = True

    def _wd_set_show_duration( self, client, userdata, message ):
        self.log.info( "mqtt: set show duration" )
        self.wd_show_duration = float( message.payload.decode() ) / 100
        self.log.info( f"show duration: {self.wd_show_duration}")

    def _wd_show_type( self, client, userdata, message ):
        payload = message.payload.decode()
        self.log.info( f"mqtt: {payload=}" )

        if len(payload) == 0:
            self.log.error( "received empty payload, returning..." )
            return

        # we are messing with parent class data here, be mindful of what we do.
        show_types = self.wd.list_show_types
        curr_show = self.wd.show_type

        if payload != curr_show:
            if payload in show_types:
                self.wd.show_type = payload
                self.wd_pick_show = True
            else:
                self.log.error( "show_type not in wd.config.shows!" )
        else:
            self.log.warning( "payload == current show, returning..." )


    ## Class methods:
    def Connect(self):
        def on_connect(client, userdata, flags, rc):
            if rc == 0:
                self.log.info("Connected to MQTT Broker!")
            else:
                self.log.error("Failed to connect, return code %d\n", rc)

        def on_disconnect( client, userdata, flags, rc):
            self.log.error( "MQTT Disconnected, attempting to reconnect..." )
            self.Connect()

        client = mqtt_client.Client( mqtt_client.CallbackAPIVersion.VERSION1, "wled_director" )
        client.username_pw_set('wled', 'horse-whale-23' )
        client.on_connect = on_connect
        client.on_disconnect = on_disconnect
        client.connect('10.0.50.41', 1883)

        self.client = client

    def formatTime( self, seconds:float ) -> str:
        ## format from seconds float into HA compatible timer string.
        ## 'HH:MM:SS.F'

        h = 0
        m = 0
        s = 0.0

        if seconds >= (60*60):
            h = floor( seconds / (60*60) )
            seconds -= h * 60 * 60
        
        if seconds >= 60:
            m = floor( seconds / 60 )
            seconds -= m * 60

        s = round( seconds, 1 )

        return f"{h:02}:{m:02}:{s:04.1f}"

    def sendTimes( self, times:dict ) -> None:
        if 'animate' in times:
            self.Publish( topic="status/animate_timer", data=self.formatTime( times['animate'] ) )
        if 'pick_show' in times:
            self.Publish( topic="status/pick_show_timer", data=self.formatTime( times['pick_show'] ) )

    def Publish( self, topic:str, data ) -> None:
        str_data = ""
        if isinstance( data, (str|int|float) ):
            str_data = data
        else:
            str_data = json.dumps( data )

        self.client.publish( f"{self.base_topic}/{topic}", str_data, retain=True )

    def Subscribe( self, topics:list ) -> None:
        sub_list = list()

        for topic in topics:
            sub_list.append( (f"{self.base_topic}/{topic}",1) )

        self.client.subscribe( sub_list )

    def addCallback( self, topic:str, callback:Callable ):
        self.client.message_callback_add( f"{self.base_topic}/{topic}", callback )

    def startLoop(self):
        self.log.debug( "Starting MQTT event loop..." )
        self.Subscribe( ['pick_show', 'animate', 'show_type', 'show_duration', 'pull_config' ] )
        self.addCallback( 'pick_show', self._wd_pick_show_now )
        self.addCallback( 'animate', self._wd_animate_now )
        self.addCallback( 'show_type', self._wd_show_type )
        self.addCallback( 'show_duration', self._wd_set_show_duration )
        self.addCallback( 'pull_config', self._wd_pull_config_now )
        self.client.loop_start()

    def __init__( self, WD_inst:WDirector, base_topic:str  ):
        self.wd = WD_inst
        self.log = WLDLogger.get( self.__class__.__name__ )
        self.base_topic = base_topic

        self.log.debug( "" )

        self.wd_animate = False
        self.wd_pick_show = False
        self.wd_pull_config = False
        self.wd_show_duration = 1.0

        self.Connect()

    def __del__( self ):
        self.client.loop_stop()