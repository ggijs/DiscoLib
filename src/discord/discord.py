import json
import select
import threading
import time
import websocket

import discord.utility as utility
import discord.data.guild as guild
import discord.msg_builder as msg_builder

class Discord:

    def __init__(self, token):
        self.guilds = {}
        self.heartbeat_interval = None
        self.heartbeat_response = False
        self.socket_lock = threading.Lock()
        self.modules = []
        self.sequence = None
        self.socket = None
        self.token = token
        self.ticks_since_hb = 0
        self.tickspeed = 0.1 # every 100ms

    def connect(self):
        url = utility.get_connection_url(self.token)["url"]
        self.socket = websocket.WebSocket()
        self.socket.connect('{}/?v=6&encoding=json'.format(url))
        
        # consume hello message
        hello = json.loads(self.socket.recv())
        self.heartbeat_interval = hello["d"]["heartbeat_interval"]
        print('Heartbeat interval: {}ms'.format(self.heartbeat_interval))
        
        self.send(msg_builder.identify(self.token))
        self.event_loop()

    def heartbeat(self):
        self.ticks_since_hb += 1
        if self.ticks_since_hb * 100 >= self.heartbeat_interval:
            # TODO: no heart_Ack -> connection error.
            msg = {
            'op': 1,
            'd':self.sequence
            }
            self.send(json.dumps(msg))
            self.ticks_since_hb = 0
            self.heartbeat_response = False


    def send(self, message):
        with self.socket_lock:
            self.socket.send(message)

    def dispatch(self, message):
        data = json.loads(message)
        if data["op"] == 0:
            if data["t"] == 'GUILD_CREATE':
                print('GUILD CREATE JWZ!!!')
                gld = guild.Guild(data["d"])
                print(gld.to_string(1))
                return
        print('\n', message)

    def event_loop(self):
        start = time.time()

        while True:
            self.heartbeat()

            while self.pending_data():
                self.dispatch(self.socket.recv())

            for m in self.modules:
                m.update()

            worktime = time.time() - start
            start += self.tickspeed
            if(worktime > self.tickspeed):
                print('Warning! event loop is not keeping up, last update took {}S.'.format(worktime))
                continue
            time.sleep(self.tickspeed - worktime)

    def peel(self, message):
        self.sequence = message["s"]
        return message["d"]

    def pending_data(self):
        return select.select([self.socket], [], [], 0)[0]

    # Subject to change
    def register_module(self, module):
        pass
